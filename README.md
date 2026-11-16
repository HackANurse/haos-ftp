# FTP/FTPS Backup agent for Home Assistant

This is an updated version of [Benjamin Renard's hass-ftp](https://github.com/brenard/hass-ftp). The original author is Benjamin Renard (@brenard); his MIT copyright notice remains in [LICENSE](LICENSE).

## Differences from the original

The original integration already provides a Home Assistant backup agent with FTP upload, listing, download, and deletion. This fork retains those features and adds:

| Area | Original | This fork |
| --- | --- | --- |
| Connection security | Plain FTP | Plain FTP, optional or required explicit FTPS, and implicit FTPS |
| Data transfer | Passive mode through `aioftp` | Passive or active mode through Python's `ftplib` |
| TLS certificates | No certificate settings | System CA verification, optional custom CA, client certificate, private key, and encrypted-key password |
| Server compatibility | UTF-8 and `aioftp` listing behavior | Configurable UTF-8, Latin-1, or Windows-1252; optional NLST listing mode |
| Backup upload | Supported | Progress reporting for the current Home Assistant backup-agent interface, plus cleanup after a failed upload |
| Backup download | Supported | Uses the same generated `.tar` filename as upload |

The transport now stages each transfer in a temporary file. It needs free temporary disk space at least as large as the backup. The fork also adds automated transport tests and Italian configuration labels.

## AI assistance and attribution

The changes in this fork were created with the assistance of artificial intelligence (OpenAI Codex) and checked with automated tests. The original code and authorship remain credited to Benjamin Renard in the repository history and MIT [license](LICENSE). This fork is maintained independently and is not endorsed by the original author.

If you would like to support maintenance of **this fork**, you can [buy me a coffee](https://buymeacoffee.com/andybegh). This link belongs to the fork maintainer, not to Benjamin Renard.

## Connection options

- Protocol: plain FTP, explicit TLS when available, required explicit TLS, or required implicit TLS.
- Passive or active FTP data connections.
- Server charset: UTF-8, Latin-1, or Windows-1252.
- Compatibility mode uses NLST rather than MLSD for directory listings.
- TLS minimum version 1.2 or 1.3. Certificates are verified against the system CA store. The optional explicit TLS mode falls back to plain FTP only when the server rejects AUTH TLS as unsupported; choose required TLS to prohibit plaintext.
- Optional PEM certificate files: a custom CA for server verification, plus a client certificate and private key for servers that require mutual TLS. An encrypted client key can have a password.
- Custom connection name, host/IP, port, and backup directory. Implicit FTPS servers normally use port 990.

Place PEM files in a path readable by Home Assistant, such as `/config/ssl/`, then enter their **absolute paths** in the integration's connection settings. Certificate contents and private keys are never stored in this repository. Client certificate and key paths must be provided together. A custom certificate configuration will never fall back to plain FTP, even when “explicit TLS if available” is selected. Certificate files are loaded at each new connection, so replacing them takes effect on the next backup operation.

The integration uploads, lists, downloads, and deletes Home Assistant backups. It reports upload progress while transferring to the FTP server. The current transport stages each transfer in a temporary file on the HAOS filesystem; make sure free temporary space is at least the size of the largest backup. Backups are not loaded into memory as one blob.

This is a _custom component_ for [Home Assistant](https://www.home-assistant.io/).
The original integration was initially based on Home Assistant's
[webdav](https://www.home-assistant.io/integrations/webdav/) integration.

## Installation

### Using HACS

Firstly, you have to add the following custom repository :

- Repository : `https://github.com/HackANurse/haos-ftp`
- Category : _Integration_

After, click on _Explore & download repositories_, search and install _FTP_
integration. Finally, go to _Settings_, _Devices & services_, click on _+ Add integration_ button
and search for _FTP_.

### Manually

Put the `custom_components/ftp` directory in your Home Assistant `custom_components` directory
and restart Home Assistant. You can now add this integration (look for _"FTP"_) and provide the
required connection information to your FTP server.

**Note:** The `custom_components` directory is located in the same directory of the
`configuration.yaml`. If it doesn't exists, create it.

## Run development environment

A development environment is provided with this integration if you want to contribute. The `manage`
script at the root of the repository permit to create and start a Home Assistant docker container
with a pre-installation of this integration (linked to sources).

Start by create the container by running the command `./manage create` and start it by running
`./manage start` command. You can now access to Home Assistant web interface on
[http://localhost:8123](http://localhost:8123) and follow the initialization process of the Home
Assistant instance.

## Debugging

To enable debug log, edit the `configuration.yaml` file and locate the `logger` block. If it does not
exists, add it with the following content :

```yaml
logger:
  default: warn
  logs:
    custom_components.ftp: debug
```

Don't forget to restart Home Assistant after.

**Note:** In development environment and you will be able to follow docker container logs by running
the `./manage logs` command.

