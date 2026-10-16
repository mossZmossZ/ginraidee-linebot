from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import asyncio
import ipaddress
import socket
from typing import Awaitable, Callable
from urllib.parse import urlsplit
import warnings

import httpx
from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_DECODED_PIXELS = 20_000_000
MAX_REDIRECTS = 3


class ImageValidationError(ValueError):
    """An image URL or its response is unsafe or unsupported."""


@dataclass(frozen=True)
class DownloadedImage:
    source_url: str
    content: bytes


class ImageFetcher:
    def __init__(
        self,
        client_factory: Callable[..., httpx.AsyncClient] = httpx.AsyncClient,
        resolve_host: Callable[
            [str], Awaitable[list[ipaddress.IPv4Address | ipaddress.IPv6Address]]
        ]
        | None = None,
    ) -> None:
        self.client_factory = client_factory
        self.resolve_host = resolve_host or _resolve_host

    async def fetch(self, url: str) -> DownloadedImage:
        current_url = validate_image_url(url)
        try:
            async with self.client_factory(timeout=10.0, follow_redirects=False) as client:
                for redirect_count in range(MAX_REDIRECTS + 1):
                    await _ensure_public_destination(current_url, self.resolve_host)
                    async with client.stream("GET", current_url) as response:
                        if response.status_code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location or redirect_count == MAX_REDIRECTS:
                                raise ImageValidationError("Too many or invalid redirects")
                            current_url = validate_image_url(str(response.url.join(location)))
                            continue
                        response.raise_for_status()
                        declared_size = response.headers.get("content-length")
                        if declared_size and (
                            not declared_size.isdigit() or int(declared_size) > MAX_IMAGE_BYTES
                        ):
                            raise ImageValidationError("Image is larger than 5 MB")
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > MAX_IMAGE_BYTES:
                                raise ImageValidationError("Image is larger than 5 MB")
                        return DownloadedImage(source_url=current_url, content=bytes(content))
        except httpx.HTTPError as error:
            raise ImageValidationError("Image download failed") from error
        raise ImageValidationError("Image download failed")


def validate_image_url(url: str) -> str:
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
    ):
        raise ImageValidationError("A public HTTPS image URL is required")
    return url


async def _ensure_public_destination(
    url: str,
    resolve_host: Callable[[str], Awaitable[list[ipaddress.IPv4Address | ipaddress.IPv6Address]]],
) -> None:
    host = urlsplit(url).hostname
    if host is None:
        raise ImageValidationError("A public HTTPS image URL is required")
    try:
        addresses = await resolve_host(host)
    except socket.gaierror as error:
        raise ImageValidationError("Image host could not be resolved") from error
    if not addresses or any(not address.is_global for address in addresses):
        raise ImageValidationError("Private or local image hosts are not allowed")


async def _resolve_host(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    records = await asyncio.to_thread(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM)
    return list({ipaddress.ip_address(record[4][0]) for record in records})


def normalize_image(content: bytes) -> bytes:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as opened:
                if opened.format not in {"JPEG", "PNG"}:
                    raise ImageValidationError("Only JPEG and PNG images are supported")
                if opened.width * opened.height > MAX_DECODED_PIXELS:
                    raise ImageValidationError("Image dimensions are too large")
                opened.load()
                image = opened.convert("RGBA" if "A" in opened.getbands() else "RGB")
    except (Image.DecompressionBombError, Image.DecompressionBombWarning, UnidentifiedImageError, OSError) as error:
        raise ImageValidationError("The response is not a valid JPEG or PNG image") from error
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def save_normalized_image(image_directory: Path, content: bytes) -> str:
    image_directory.mkdir(parents=True, exist_ok=True)
    image_id = uuid4().hex
    target = image_directory / f"{image_id}.png"
    temporary = image_directory / f".{image_id}.tmp"
    temporary.write_bytes(normalize_image(content))
    temporary.replace(target)
    return image_id


def image_path(image_directory: Path, image_id: str) -> Path | None:
    if len(image_id) != 32 or any(character not in "0123456789abcdef" for character in image_id):
        return None
    target = image_directory / f"{image_id}.png"
    return target if target.is_file() else None


def delete_image(image_directory: Path, image_id: str) -> None:
    target = image_path(image_directory, image_id)
    if target is not None:
        target.unlink()


def recover_unreferenced_images(image_directory: Path, referenced_image_ids: set[str]) -> None:
    if not image_directory.is_dir():
        return
    recovery_directory = image_directory / "orphaned"
    for candidate in image_directory.glob("*.png"):
        if candidate.stem not in referenced_image_ids:
            recovery_directory.mkdir(exist_ok=True)
            candidate.replace(recovery_directory / candidate.name)
