#!/usr/bin/env bash
# Requires SSH key authentication and a verified host key.
set -euo pipefail
cd "$(dirname "$0")/.."
bash deploy/upload.sh
ssh -t -o BatchMode=yes -o StrictHostKeyChecking=yes \
    "${DEPLOY_USER}@${DEPLOY_HOST}" 'cd /opt/msi-hbp && sudo bash deploy/deploy.sh'
