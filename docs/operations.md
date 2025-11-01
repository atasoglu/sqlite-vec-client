++ docs/operations.md
# Operational Playbook

## Testing

- Run `pytest --cov=sqlite_vec_client --cov-report=term-missing --cov-report=xml`.
- Upload the generated `coverage.xml` as part of your CI artifacts (handled automatically
  in the GitHub Actions workflow).
- For environments without the native `sqlite-vec` extension, rely on the mocked tests
  planned in the roadmap or disable integration markers temporarily.

## Backups

```python
client.backup("backup.jsonl")
client.backup("backup.csv", format="csv", include_embeddings=True)
```

- JSONL is recommended for long-term storage (embeddings stay in human-readable lists).
- CSV is convenient for spreadsheets but still requires embeddings for restore.

## Restore & Disaster Recovery

```python
client.restore("backup.jsonl")
client.restore("backup.csv", format="csv", skip_duplicates=True)
```

- Use `skip_duplicates=True` when replaying backups into a database that may contain
  partial data (e.g., after a failed migration).

## Observability

- Set `SQLITE_VEC_CLIENT_LOG_LEVEL=DEBUG` in the environment to trace connection
  lifecycle and queries during incident response.
- Logs include connection open/close events and count of rows processed during imports
  and exports.
