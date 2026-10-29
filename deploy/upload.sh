#!/usr/bin/env bash
# Upload tracked files only. Set the target in the local environment.
set -euo pipefail
: "${DEPLOY_HOST:?Set DEPLOY_HOST to your server hostname}"
: "${DEPLOY_USER:?Set DEPLOY_USER to your SSH account}"
[[ "$DEPLOY_HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]] || exit 2
[[ "$DEPLOY_USER" =~ ^[A-Za-z_][A-Za-z0-9_-]*$ ]] || exit 2
cd "$(dirname "$0")/.."
target="${DEPLOY_USER}@${DEPLOY_HOST}"
ssh_opts=(-o BatchMode=yes -o StrictHostKeyChecking=yes)
ssh "${ssh_opts[@]}" "$target" 'mkdir -p /opt/msi-hbp'
# .env, private keys, local data and untracked files are not included.
git archive --format=tar HEAD | ssh "${ssh_opts[@]}" "$target" 'tar -xf - -C /opt/msi-hbp'
printf '%s\n' 'Tracked files uploaded. Configure the server-local .env before deployment.'
