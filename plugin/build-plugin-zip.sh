#!/usr/bin/env bash
# Build the plugin as one ZIP for the Claude app (Customize > Plugins > upload), in plugin/dist/.
# The app version leaves out .mcp.json: in the app, BuildersMCP, Gmail and Calendar are already connected
# as account connectors, so the plugin carries only skills, agents, commands, rules and schemas.
set -euo pipefail
cd "$(dirname "$0")"
rm -rf dist/app && mkdir -p dist/app/builders
cp -r .claude-plugin agents commands shared skills dist/app/builders/
(cd dist/app && zip -qr ../builders-plugin-app.zip builders)
rm -rf dist/app
ls -la dist/builders-plugin-app.zip
