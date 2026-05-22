# Development Workflow

EchoFinder workflow:

1. Create feature branch from `test-main`.
2. Open PR into `test-main`.
3. Validate and merge to `test-main`.
4. Mark work as **Pending Release**.
5. Release via PR from `test-main` to `main`.
6. Merge to `main` only when release criteria are met.

Definitions:

- Merged to `test-main`: implemented and pending release.
- Merged to `main`: released.
