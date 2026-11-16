[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

Based on Benjamin Renard's [MIT-licensed hass-ftp](https://github.com/brenard/hass-ftp). This version adds FTPS, active/passive transfers, charset and TLS choices, and backup upload progress.

## Installation

For Home Assistant 2026.11 or later, add `https://github.com/HackANurse/haos-ftp`
through _Settings_ → _Marketplace_ → _Add from link_ (type _Integration_) and install it.
For earlier versions, add the same URL as a custom _Integration_ repository in HACS
and download it there. Restart Home Assistant if prompted, then go to
_Settings_ → _Devices & services_ → _Add integration_ and search for _FTP_.

## Configuration is done in the UI

When adding the integration, you will have to provide :

- The IP address (or the hostname) and port of the FTP server
- The username and password to login
- The path of the remote directory where to store your backups
- The FTP/FTPS protocol, transfer mode, charset, compatibility mode, and TLS minimum version
- Optional custom CA certificate, client certificate, private key, and key password (absolute paths under `/config/ssl/`)

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/HackANurse/haos-ftp.svg?style=for-the-badge
[commits]: https://github.com/HackANurse/haos-ftp/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/HackANurse/haos-ftp/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/HackANurse/haos-ftp.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40HackANurse-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/HackANurse/haos-ftp.svg?style=for-the-badge
[releases]: https://github.com/HackANurse/haos-ftp/releases
[user_profile]: https://github.com/HackANurse

