# Security policy

## Reporting a vulnerability

Please do not publish exploit details or credentials in a public issue. Use GitHub's private vulnerability reporting feature if enabled, or contact the repository maintainer privately through GitHub.

## Secret handling

- Never commit `.env` files or real credentials.
- Store provider keys, database URLs, API tokens, webhook secrets, and deployment credentials in a dedicated secret manager or protected deployment environment variables.
- Rotate any credential that has been committed or exposed. Removing it from the latest file does not remove it from Git history or copies already cloned.
- Use unique, strong database passwords and restrict database/network access.
- Do not upload private customer documents or personal data to test environments.

## Deployment note

The project is a starter implementation, not a security certification. Before production use, perform dependency, application, infrastructure, tenancy/isolation, authentication, authorization, rate-limit, backup/restore, and privacy reviews.
