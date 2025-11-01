++ docs/index.md
# sqlite-vec-client Documentation

Welcome to the project documentation. This site complements the information in `README.md`
and focuses on how to operate the client in real-world scenarios.

## Highlights

- Lightweight CRUD and similarity search API powered by `sqlite-vec`
- Typed results for safer integrations
- Bulk operations, metadata filters, and transaction helpers
- New backup/restore helpers to streamline disaster recovery

## Quick Links

- [API Reference](api.md) — method-by-method contract details
- [Migration Guide](guides/migration.md) — upgrade notes for the latest releases
- [Operational Playbook](operations.md) — checklists for testing, backups, and restore

## Building the Docs

```bash
pip install -r requirements-dev.txt
mkdocs serve
```

The site is served at `http://127.0.0.1:8000` by default.
