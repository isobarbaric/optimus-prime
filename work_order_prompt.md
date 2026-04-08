# Work Order #1: a

## Description

b

## Linked Blueprints

The following blueprint documents describe the components you need to implement. These are the authoritative specification — implement exactly what they describe.

## Blueprint: Backend

```component
name: AuthenticationService
container: API Server
responsibilities:
  - Handle JWT validation via AWS Cognito
  - Manage JWT token lifecycle
```

```component
name: DatabaseSession
container: API Server
responsibilities:
  - Manage SQLModel ORM sessions
  - Apply Alembic migrations
```

---

## Instructions

Implement this work order in full. Read the blueprint specifications carefully and implement each component described. Use the existing codebase as context for patterns, naming conventions, and module placement.

When you are done making all changes, stop. Do not add extra files, tests, or documentation beyond what the work order and blueprints specify.
