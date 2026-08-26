# Security Baseline
- No secrets in Git; use `.env`.
- Keep production `DEBUG=false`, explicit `ALLOWED_HOSTS`, HTTPS/HSTS, secure cookies.
- Validate uploads by content, extension, size, and dimensions; serve user media from an isolated origin where possible.
- Run non-root containers; least-privilege database credentials; regular OS/Python package updates.
