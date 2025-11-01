++ docs/guides/migration.md
# Migration Guide

## Upgrading to v2.3.0

### Embedding Dimension Validation

- All write and search operations now validate embedding length against the table
  dimension. Existing databases created with `create_table` are supported automatically,
  but manual schemas must follow the `float[dim]` declaration used by `sqlite-vec`.
- Action: ensure any custom tooling or fixtures produce embeddings with the expected
  dimension before calling client methods.

### Import Behaviour

- `import_from_json` and `import_from_csv` honour `skip_duplicates`, skipping records
  whose rowids already exist.
- Importers now require embeddings to be present; CSV sources exported without the
  `embedding` column raise a descriptive error.
- Action: export backups with `include_embeddings=True` if you intend to re-import them.

### Backup & Restore Helpers

- New `backup()` and `restore()` helpers wrap JSONL/CSV workflows and log the format
  being used. Prefer these helpers for consistent backup scripts.

### Continuous Coverage

- The CI pipeline now uploads `coverage.xml` as an artifact. Configure downstream
  tooling (Codecov, Sonar, etc.) to consume the artifact if you need external reporting.

## General Advice

- Always run `pytest --cov=sqlite_vec_client --cov-report=xml` before publishing.
- Keep `requirements-dev.txt` up-to-date locally to build the documentation site with
  `mkdocs serve`.
