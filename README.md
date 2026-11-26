<img src="assets/haos-ftp-icon.svg" alt="Icona haos-ftp / haos-ftp icon" width="96" align="right">

# haos-ftp — backup FTP/FTPS per Home Assistant

[Italiano](#italiano) · [English](#english)

## Italiano

**haos-ftp** è una versione aggiornata di [hass-ftp di Benjamin Renard](https://github.com/brenard/hass-ftp). L'autore originale è Benjamin Renard (@brenard); la sua nota di copyright MIT è conservata nel file [LICENSE](LICENSE). Questa è un'integrazione personalizzata per Home Assistant, mantenuta indipendentemente dall'autore originale.

### Differenze rispetto all'originale

L'integrazione originale permette già di caricare, elencare, scaricare ed eliminare i backup via FTP. Questa versione mantiene tali funzioni e aggiunge:

| Ambito | Originale | Questa versione |
| --- | --- | --- |
| Sicurezza della connessione | FTP in chiaro | FTP in chiaro, FTPS esplicito facoltativo o obbligatorio, FTPS implicito |
| Trasferimento dati | Modalità passiva con `aioftp` | Modalità passiva o attiva con `ftplib` di Python |
| Certificati TLS | Nessuna impostazione | Verifica con CA di sistema, nome del server nel certificato configurabile, CA personalizzata facoltativa, certificato client, chiave privata e password per la chiave cifrata |
| Compatibilità del server | UTF-8 ed elenchi tramite `aioftp` | Codifica UTF-8, Latin-1 o Windows-1252; modalità NLST facoltativa |
| Caricamento dei backup | Presente | Trasferimento in streaming, avanzamento tramite l'interfaccia attuale degli agenti di backup di Home Assistant e pulizia dopo un errore |
| Scaricamento dei backup | Presente | Usa lo stesso nome `.tar` generato per il caricamento |

Il caricamento invia i blocchi al server mentre Home Assistant produce il backup, evitando di tenere inattiva la connessione durante la copia in un file temporaneo. Lo scaricamento usa ancora un file temporaneo e richiede spazio libero almeno pari alla dimensione del backup. Questa versione aggiunge anche test automatici per il trasporto ed etichette di configurazione in italiano.

### Opzioni di connessione e certificati

- Protocollo: FTP in chiaro, FTPS esplicito se disponibile, FTPS esplicito obbligatorio o FTPS implicito obbligatorio.
- Modalità di trasferimento dati passiva o attiva.
- Codifica del server: UTF-8, Latin-1 o Windows-1252.
- Modalità compatibilità: usa NLST al posto di MLSD per elencare i file.
- Versione minima TLS 1.2 o 1.3. I certificati del server vengono verificati tramite le CA di sistema.
- Nome server nel certificato TLS facoltativo: permette di verificare il certificato con il nome del nodo FTP quando è diverso dall'indirizzo usato per collegarsi. La verifica TLS resta attiva.
- File PEM facoltativi: CA personalizzata per verificare il server, certificato client e chiave privata per TLS reciproco, con eventuale password della chiave.
- Nome della connessione, host/IP, porta e cartella dei backup configurabili. I server FTPS impliciti usano normalmente la porta 990.

Salva i file PEM in una posizione leggibile da Home Assistant, per esempio `/config/ssl/`, e inserisci nelle impostazioni i loro **percorsi assoluti**. Certificato client e chiave privata vanno forniti insieme. Certificati e chiavi non sono memorizzati in questo repository; i file vengono riletti a ogni nuova connessione, quindi una sostituzione ha effetto dall'operazione successiva.

La modalità «FTPS esplicito se disponibile» torna a FTP in chiaro solo se il server segnala che `AUTH TLS` non è supportato. Se imposti certificati personalizzati, il ripiego su FTP in chiaro è disabilitato. Per vietare sempre connessioni non cifrate, scegli una modalità TLS obbligatoria.

### Server FTP Aruba

Per un hosting Aruba, inserisci in **Indirizzo/IP** l'indirizzo FTP del dominio indicato nel pannello Aruba (per esempio `ftp.example.com`) e le credenziali dell'account Aruba nel formato `123456@aruba.it`. La [guida ufficiale Aruba](https://guide.aruba.it/hosting-e-domini/hosting/gestione-strumenti-hosting/pubblicazione-gestione-sito/configurazione-client-ftp-pubblicazione-ftp-ftps) indica **FTPS implicito sulla porta 990**; per FTP con TLS esplicito se disponibile indica la porta 21. Alcuni nodi Aruba presentano un certificato intestato al nome del nodo, diverso dall'indirizzo FTP del dominio: in **Nome server nel certificato TLS** indica il nome DNS presente nel certificato, per esempio `ftplnx02.aruba.it` *solo se è quello effettivamente presentato dal tuo server*. Il certificato continua a essere verificato; non è necessario disabilitare la verifica TLS.

Per conoscere il nome del certificato, usa un client FTP che mostri i dettagli TLS oppure, da terminale, `openssl s_client -connect ftp.example.com:990 -servername ftp.example.com` per FTPS implicito (usa `-starttls ftp -connect ftp.example.com:21` per TLS esplicito). Controlla il campo `subjectAltName` del certificato e verifica che il nome corrisponda al nodo Aruba a cui ti stai collegando. Per **Percorso dei backup**, inizia con una cartella relativa alla directory dell'account, per esempio `backup_ha`, senza `/` iniziale. Se la cartella non esiste, l'integrazione prova a crearla; l'account FTP deve avere permesso di scrittura. Il percorso `/` usa la cartella principale dell'account. Se una voce già in errore resta rossa dopo aver salvato le opzioni, usa il menu della voce → **Ricarica**.

L'integrazione carica, elenca, scarica ed elimina i backup di Home Assistant e mostra l'avanzamento del caricamento. Il caricamento usa una coda limitata di blocchi, senza duplicare l'intero backup nella memoria o in un file temporaneo. Per lo scaricamento serve spazio temporaneo libero almeno pari al backup da ripristinare.

### Installazione

Le versioni seguono il formato `aaaa.mm.nn`: anno, mese e progressivo a due cifre che riparte da `01` ogni mese. Per esempio, `2026.11.06` è il sesto rilascio di novembre 2026. Il numero della versione nel `manifest.json` coincide con il tag del rilascio GitHub.

#### Home Assistant 2026.11 o successivo: Marketplace

Apri _Impostazioni_ → _Marketplace_ → _Aggiungi da link_. Inserisci `https://github.com/HackANurse/haos-ftp`, collega GitHub se richiesto e aggiungi il repository come _Integrazione_. Apri la sua scheda nel Marketplace e installalo. Riavvia Home Assistant se richiesto; poi vai in _Impostazioni_ → _Dispositivi e servizi_ → _Aggiungi integrazione_ e cerca _FTP_.

#### Home Assistant precedente a 2026.11: HACS

In HACS apri _Repository personalizzati_, inserisci `https://github.com/HackANurse/haos-ftp` e seleziona la categoria _Integrazione_. Scarica _FTP Backup agent_, riavvia Home Assistant e cerca _FTP_ in _Impostazioni_ → _Dispositivi e servizi_ → _Aggiungi integrazione_.

#### Installazione manuale

Copia `custom_components/ftp` nella cartella `custom_components` di Home Assistant e riavvia. La cartella `custom_components` si trova accanto a `configuration.yaml`; creala se non esiste. Aggiungi poi l'integrazione _FTP_ dall'interfaccia.

### Ambiente di sviluppo

Lo script `manage` nella radice del repository prepara un ambiente Docker con l'integrazione collegata ai sorgenti. Esegui `./manage create` e poi `./manage start`; Home Assistant sarà disponibile su [http://localhost:8123](http://localhost:8123). Usa `./manage logs` per leggere i log del container.

### Debug

Per attivare i log di debug dell'integrazione, aggiungi questo blocco a `configuration.yaml` (o integra il blocco `logger` esistente) e riavvia Home Assistant:

```yaml
logger:
  default: warn
  logs:
    custom_components.ftp: debug
```

### Attribuzione, IA e sostegno

Le modifiche di questa versione sono state realizzate con l'ausilio dell'intelligenza artificiale (OpenAI Codex) e verificate con test automatici. Il codice originale e la paternità di Benjamin Renard restano riconosciuti nella cronologia del repository e nella [licenza MIT](LICENSE). Questa versione non è approvata o sponsorizzata dall'autore originale.

Se vuoi sostenere la manutenzione di **questa versione**, puoi [offrire un caffè al suo manutentore](https://buymeacoffee.com/andybegh). Il link appartiene al manutentore di questa versione, non a Benjamin Renard.

## English


This is an updated version of [Benjamin Renard's hass-ftp](https://github.com/brenard/hass-ftp). The original author is Benjamin Renard (@brenard); his MIT copyright notice remains in [LICENSE](LICENSE).

### Differences from the original

The original integration already provides a Home Assistant backup agent with FTP upload, listing, download, and deletion. This fork retains those features and adds:

| Area | Original | This fork |
| --- | --- | --- |
| Connection security | Plain FTP | Plain FTP, optional or required explicit FTPS, and implicit FTPS |
| Data transfer | Passive mode through `aioftp` | Passive or active mode through Python's `ftplib` |
| TLS certificates | No certificate settings | System CA verification, configurable certificate server name, optional custom CA, client certificate, private key, and encrypted-key password |
| Server compatibility | UTF-8 and `aioftp` listing behavior | Configurable UTF-8, Latin-1, or Windows-1252; optional NLST listing mode |
| Backup upload | Supported | Streaming transfer, progress reporting for the current Home Assistant backup-agent interface, and cleanup after a failed upload |
| Backup download | Supported | Uses the same generated `.tar` filename as upload |

Uploads send blocks to the server as Home Assistant produces them, avoiding an idle connection while a full backup is staged. Downloads still use a temporary file and need free temporary space at least as large as the backup. The fork also adds automated transport tests and Italian configuration labels.

### Connection options

- Protocol: plain FTP, explicit TLS when available, required explicit TLS, or required implicit TLS.
- Passive or active FTP data connections.
- Server charset: UTF-8, Latin-1, or Windows-1252.
- Compatibility mode uses NLST rather than MLSD for directory listings.
- TLS minimum version 1.2 or 1.3. Certificates are verified against the system CA store. The optional explicit TLS mode falls back to plain FTP only when the server rejects AUTH TLS as unsupported; choose required TLS to prohibit plaintext.
- Optional TLS certificate server name: verify the certificate against the FTP node's hostname when it differs from the address used to connect. Certificate validation remains enabled.
- Optional PEM certificate files: a custom CA for server verification, plus a client certificate and private key for servers that require mutual TLS. An encrypted client key can have a password.
- Custom connection name, host/IP, port, and backup directory. Implicit FTPS servers normally use port 990.

Place PEM files in a path readable by Home Assistant, such as `/config/ssl/`, then enter their **absolute paths** in the integration's connection settings. Certificate contents and private keys are never stored in this repository. Client certificate and key paths must be provided together. A custom certificate configuration will never fall back to plain FTP, even when “explicit TLS if available” is selected. Certificate files are loaded at each new connection, so replacing them takes effect on the next backup operation.

### Aruba FTP servers

For Aruba hosting, enter the domain FTP address shown in your Aruba control panel (for example `ftp.example.com`) in **Host**, and your Aruba account credentials in the form `123456@aruba.it`. The [official Aruba guide](https://guide.aruba.it/hosting-e-domini/hosting/gestione-strumenti-hosting/pubblicazione-gestione-sito/configurazione-client-ftp-pubblicazione-ftp-ftps) specifies **implicit FTPS on port 990**; it lists port 21 for FTP with explicit TLS if available. Some Aruba nodes present a certificate for the node hostname rather than the domain FTP address. Enter the DNS name shown in that certificate under **TLS certificate server name**; `ftplnx02.aruba.it` is only an example and must match the certificate your server actually presents. This setting keeps TLS certificate validation enabled.

You can inspect the certificate with an FTP client that shows TLS details or run `openssl s_client -connect ftp.example.com:990 -servername ftp.example.com` for implicit FTPS (use `-starttls ftp -connect ftp.example.com:21` for explicit TLS) and check `subjectAltName`. Start with a backup path relative to the FTP account directory, such as `backup_ha`, without a leading `/`. The integration attempts to create a missing directory, so the account needs write permission. Use `/` to store backups in the account's top-level directory. If an entry in an error state stays red after saving options, use the entry menu → **Reload**.

The integration uploads, lists, downloads, and deletes Home Assistant backups. It reports upload progress while transferring to the FTP server. Uploads use a bounded queue rather than staging the entire backup in a temporary file or memory. Downloads still require temporary space at least as large as the backup.

This is a _custom component_ for [Home Assistant](https://www.home-assistant.io/).
The original integration was initially based on Home Assistant's
[webdav](https://www.home-assistant.io/integrations/webdav/) integration.

### Installation

Versions use the `yyyy.mm.nn` format: year, month, and a two-digit sequence that starts again at `01` each month. For example, `2026.11.06` is the sixth release of November 2026. The version in `manifest.json` matches the GitHub release tag.

#### Home Assistant 2026.11 and later: Marketplace

Open _Settings_ → _Marketplace_ → _Add from link_. Enter
`https://github.com/HackANurse/haos-ftp`, connect GitHub if prompted, and add it as an
_Integration_. Open the repository in Marketplace and install it. Restart Home Assistant
if prompted. Then go to _Settings_ → _Devices & services_ → _Add integration_ and search
for _FTP_.

#### Home Assistant before 2026.11: HACS

In HACS, open _Custom repositories_, enter
`https://github.com/HackANurse/haos-ftp`, and select _Integration_ as the category.
Download _FTP Backup agent_ from HACS, restart Home Assistant, then go to
_Settings_ → _Devices & services_ → _Add integration_ and search for _FTP_.

#### Manually

Put the `custom_components/ftp` directory in your Home Assistant `custom_components` directory
and restart Home Assistant. You can now add this integration (look for _"FTP"_) and provide the
required connection information to your FTP server.

**Note:** The `custom_components` directory is located in the same directory of the
`configuration.yaml`. If it doesn't exists, create it.

### Run development environment

A development environment is provided with this integration if you want to contribute. The `manage`
script at the root of the repository permit to create and start a Home Assistant docker container
with a pre-installation of this integration (linked to sources).

Start by create the container by running the command `./manage create` and start it by running
`./manage start` command. You can now access to Home Assistant web interface on
[http://localhost:8123](http://localhost:8123) and follow the initialization process of the Home
Assistant instance.

### Debugging

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

### AI assistance and attribution

The changes in this fork were created with the assistance of artificial intelligence (OpenAI Codex) and checked with automated tests. The original code and authorship remain credited to Benjamin Renard in the repository history and MIT [license](LICENSE). This fork is maintained independently and is not endorsed by the original author.

If you would like to support maintenance of **this fork**, you can [buy me a coffee](https://buymeacoffee.com/andybegh). This link belongs to the fork maintainer, not to Benjamin Renard.
