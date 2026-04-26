#!/bin/bash

USER_DATA_DIR=/data/${USER_DATA_DIR:-default}

rm -rf /tmp/.X8888-lock
rm -rf ${USER_DATA_DIR}/SingletonLock

xvfb-run \
  -n 8888 \
  --server-args="-screen 0 1920x1080x24 -ac" \
  google-chrome \
  --window-size=1920,1080 \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-port=9222 \
  --user-data-dir=${USER_DATA_DIR} \
  --no-first-run &

MAX_RETRIES=30
RETRY_INTERVAL=1
RETRY_COUNT=0

sleep 2s

x11vnc -ncache 10 -display :8888 -nopw -noshm -geometry 1920x1080 -forever &

websockify --web /usr/share/novnc/ 0.0.0.0:6080 localhost:5900 &

uv run poe start