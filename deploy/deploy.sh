#!/usr/bin/env bash
# Server-side setup template; run only after configuring the server-local .env.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
[[ "$EUID" -eq 0 ]] || { echo 'Run this server-side setup with sudo.' >&2; exit 1; }
[[ -f .env ]] || { echo 'Create a server-local .env from .env.example first.' >&2; exit 1; }
for tool in python3 docker nginx systemctl; do
    command -v "$tool" >/dev/null || { echo "Install prerequisite: $tool" >&2; exit 1; }
done
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ is required"'
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
# Read dotenv using the application parser; never echo or pass its password as an argument.
NEO4J_PASSWORD="$(venv/bin/python - <<'PY'
from dotenv import dotenv_values
p = dotenv_values('.env').get('NEO4J_PASSWORD', '')
if len(p) < 16 or p in {'your_password_here', 'your_unique_password_here'} or '\n' in p:
    raise SystemExit('Set a unique Neo4j password of at least 16 characters in .env.')
print(p, end='')
PY
)"
chmod 600 .env
if docker container inspect neo4j-msi-hbp >/dev/null 2>&1; then
    echo 'Existing Neo4j container retained; this script does not rotate existing credentials.'
else
    export NEO4J_AUTH="neo4j/${NEO4J_PASSWORD}"
    docker run -d --name neo4j-msi-hbp --restart unless-stopped \
        -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
        -v "$PROJECT_DIR/neo4j_data:/data" -e NEO4J_AUTH neo4j:5
    unset NEO4J_AUTH
fi
unset NEO4J_PASSWORD
echo 'Neo4j is reachable locally; use an SSH tunnel for its browser.'
echo 'Review deploy/nginx.conf and configure your own domain and TLS certificate.'
echo 'Start the application using venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8080'
echo 'Configure the service account and systemd unit according to your server policy.'
