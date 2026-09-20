#!/usr/bin/env bash

release="${1:-main}"
localectl set-keymap br-abnt2
archinstall \
    --plugin-url https://gitlab.com/gabriel.chamon/archie/-/raw/$release/archinstall/plugin.py \
    --config /tmp/user_configuration.json \
    --creds /tmp/user_credentials.json
