# Local backups

This directory is for **operator-local** database dumps, config snapshots, and restore notes.

## Security rules

- **Never commit** `.env`, API keys, HMAC secrets, or database passwords into this folder.
- Files here are gitignored except this README.
- Prefer encrypted storage and `chmod 600` on sensitive archives.
- Rotate credentials after any backup that captured live secrets.

For deployment restore procedures, keep private runbooks outside the repository (see `.gitignore`).
