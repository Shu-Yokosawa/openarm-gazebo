#!/bin/bash
# ホスト側で Docker からの X11 アクセスを許可する

set -e

echo "X11 転送のセットアップを開始..."

xhost +local:docker

XAUTH_FILE=/tmp/.docker.xauth
[ -f "${XAUTH_FILE}" ] && rm "${XAUTH_FILE}"
touch "${XAUTH_FILE}"
chmod 666 "${XAUTH_FILE}"

xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "${XAUTH_FILE}" nmerge -

echo "完了: X11 転送の準備ができました"
echo "  DISPLAY=${DISPLAY}"
echo "  XAUTH_FILE=${XAUTH_FILE}"
