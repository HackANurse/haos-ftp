[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

Based on Benjamin Renard's [MIT-licensed hass-ftp](https://github.com/brenard/hass-ftp). This version adds FTPS, active/passive transfers, charset and TLS choices, and backup upload progress.

## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "FTP".

## Configuration is done in the UI

When adding the integration, you will have to provide :

- The IP address (or the hostname) and port of the FTP server
- The username and password to login
- The path of the remote directory where to store your backups
- The FTP/FTPS protocol, transfer mode, charset, compatibility mode, and TLS minimum version

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/HackANurse/hass-ftp.svg?style=for-the-badge
[commits]: https://github.com/HackANurse/hass-ftp/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license]: https://github.com/HackANurse/hass-ftp/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/HackANurse/hass-ftp.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40HackANurse-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/HackANurse/hass-ftp.svg?style=for-the-badge
[releases]: https://github.com/HackANurse/hass-ftp/releases
[user_profile]: https://github.com/HackANurse

