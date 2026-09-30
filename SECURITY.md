# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Data & Credentials Protection Guidelines

`AutoPost` interacts with external APIs (Google Gemini, YouTube Data API v3, Reddit API, Cloudflare R2).
To protect your privacy and credentials:

1. **Never Commit Your `.env` File**:
   - The `.env` file contains your sensitive API keys and OAuth refresh tokens.
   - It is listed in `.gitignore` by default. Always verify with `git status` that `.env` is never staged.
2. **YouTube OAuth Scopes**:
   - The pipeline requests `https://www.googleapis.com/auth/youtube.upload` and `https://www.googleapis.com/auth/youtube` to schedule and upload videos to your channel.
   - Guard your client secrets and refresh tokens as you would passwords.
3. **GitHub Actions Secrets**:
   - When deploying with GitHub Actions, store all credentials as encrypted **Repository Secrets** (`Settings` -> `Secrets and variables` -> `Actions`).
   - Never print or echo secrets in workflow steps.
4. **Token Revocation**:
   - If you ever suspect a credential or refresh token was compromised, revoke it immediately via your [Google Account Permissions](https://myaccount.google.com/permissions) or the [Google Cloud Console](https://console.cloud.google.com/).

---

## Reporting a Vulnerability

If you discover a security vulnerability within this project:

1. **Do not create a public GitHub issue.**
2. Send a confidential report to the project maintainer via GitHub Security Advisory or direct message.
3. Include details of the vulnerability, reproduction steps, and potential impact.

We will review the issue promptly and publish a fix.
