# Deployment template

Deployment targets and credentials are operator settings. This repository contains no live server address or usable password in its current deployment files. Earlier commits contained credentials; removing them from the current files does not revoke them. The server administrator must rotate the SSH and Neo4j credentials and review authentication logs. Existing Git history has been retained for the published research references.

## Prerequisites

- A server account permitted to write `/opt/msi-hbp`, SSH key authentication, and a verified server host key. Verify the fingerprint through a trusted channel before adding the host to `known_hosts`.
- Python 3.12 or later, Docker, Nginx and systemd on the server. Review package compatibility in the root README.
- A server-local `.env` copied from `.env.example`, with your API configuration and a new, unique Neo4j password. Keep this file out of Git and restrict its permissions to the service administrator.

## Upload from Linux or macOS

```bash
export DEPLOY_HOST=your-server.example.org
export DEPLOY_USER=your_ssh_account
bash deploy/upload.sh
```

The uploader archives tracked files from the current commit. It does not upload `.git`, the untracked `.env`, keys or local data. The remote account must already have permission to create or write the project directory. `auto_deploy.sh` additionally invokes the server-side setup through sudo; it uses the same SSH key and verified-host requirements.

## Upload from Windows

```powershell
./deploy/deploy.ps1 -ServerHost your-server.example.org -SshUser your_ssh_account
```

This uses Git, OpenSSH and a temporary archive. No SSH password is stored, printed or passed on the command line.

## Configure on the server

Create `/opt/msi-hbp/.env` locally and fill in the settings before running:

```bash
cd /opt/msi-hbp
sudo bash deploy/deploy.sh
```

The setup reads the database password from `.env`, installs the Python dependencies, and creates a Neo4j 5 container only if one does not already exist. New containers bind ports 7474 and 7687 to localhost. It does not remove database containers, reset existing passwords, change firewall policy, or configure production service accounts automatically. The administrator must separately review an existing container's port bindings and access rules.

The `NEO4J_AUTH` setting initializes a new database; it does not change the password in an existing database volume. Use the Neo4j administration procedure to rotate existing credentials, then update the application `.env`. See [Neo4j Docker documentation](https://neo4j.com/docs/operations-manual/current/docker/introduction/).

For the Neo4j browser, create an SSH tunnel from your own computer:

```bash
ssh -L 7474:127.0.0.1:7474 -L 7687:127.0.0.1:7687 your_ssh_account@your-server.example.org
```

Open `http://localhost:7474`. Do not expose database administration ports publicly.

## Web service

Replace `example.org` and the certificate paths in `deploy/nginx.conf` with your own settings. Run Streamlit on localhost port 8080 under an appropriate service account, then configure Nginx and TLS. Review the template before applying it; credentials, certificates and live addresses belong in server-local configuration.

These repository changes were checked statically and with local upload mocks. They have not been deployed to the research server and do not certify that server credentials have been rotated.
