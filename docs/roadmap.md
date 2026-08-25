# Roadmap

## Phase 2: Content Experience
- Multi-theme selection and per-site theme settings.
- Image watermark pipeline with configurable position, opacity, and text/image marks.
- Email notifications for replies and moderation events.
- Comment tree rendering and reply notification threading.
- Rich Markdown admin editor and batch media insertion.

## Phase 3: Migration
- Emlog database inspection adapter for articles, categories, tags, and comments.
- Preserve parent/child comment relationships during import.
- Legacy URL map and redirects for historical absolute links.
- Generic importer interface for other blog engines.

## Phase 4: Platform
- Plugin discovery, lifecycle hooks, dependency isolation, and admin controls.
- Automated stable-version upgrade workflow with lockfile refresh and compatibility checks.
- CI checks for tests, linting, migrations, Docker build, dependency audit, and image scan.
- Scheduled backups and tested restore procedure.

## Security Baseline
- No secrets in Git; use `.env`.
- Keep production `DEBUG=false`, explicit `ALLOWED_HOSTS`, HTTPS/HSTS, secure cookies.
- Validate uploads by content, extension, size, and dimensions; serve user media from an isolated origin where possible.
- Run non-root containers; least-privilege database credentials; regular OS/Python package updates.
