# ginraidee-linebot

A planned open-source LINE group bot for choosing where to eat lunch.
Members manage their group's restaurants with `@ginrai-manage` and start
selection with `@ginrai`. Voting closes at 12:00 noon, Thailand time.

Planned stack: Python, FastAPI, SQLite, and Docker with persistent database
and image storage. Local and server deployments will use
`docker-compose.yml` and `docker-compose-prod.yml` respectively.

## Project status

Requirements and the development planning bundle are written. P0 is in review;
application code, Compose files, agent execution, and testing have not started.

## Planning documents

- [Confirmed requirements and decision history](docs/discovery.md)
- [Implementation plan, development phases, and todo list](docs/implementation-plan.md)
- [Kanban board and task-card index](docs/kanban.md)
- [Individual task cards](.scratch/ginraidee/issues/)
- [Roles, review workflow, and three-round defect limit](docs/development-workflow.md)
- [Manual acceptance checklist](docs/uat.md)

Start with the implementation plan and board. Proposed defaults and unresolved
choices are marked for review rather than silently added to the requirements.
