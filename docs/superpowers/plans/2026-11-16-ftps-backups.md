# FTP/FTPS Backup Integration Plan

**Goal:** Update brenard/hass-ftp for Home Assistant backup upload and the connection choices shown in the screenshots.

**Architecture:** Keep the existing Home Assistant backup agent and replace its FTP transport with a stdlib `ftplib` adapter supporting active/passive data connections, explicit/implicit FTPS, TLS version, charset, and a compatibility listing mode. Stream large backup files through bounded temporary files so no entire backup is held in memory. Preserve backup metadata sidecars and the original MIT notice.

**Tech stack:** Python 3.13, Home Assistant backup platform, `ftplib`, `pytest`.

## Tasks

1. Add transport tests for protocol selection, TLS policy, passive/active, encoding, and compatibility mode. Verify failure before implementation.
2. Implement transport adapter; run focused tests.
3. Extend setup and configuration flow; add schema and error tests.
4. Update backup upload progress and cleanup; add tests for failed transfers.
5. Update documentation and translations; run full tests, lint, syntax checks, then publish with attribution if GitHub access permits.

## Review focus

- Optional TLS falls back only when AUTH TLS is unsupported, never on certificate errors.
- No filename or metadata corruption with non-ASCII paths.
- Partial uploads are removed after transfer failures.
- Active transfer works over FTPS, including encrypted data channel.
- Upload progress reports bytes to Home Assistant.
