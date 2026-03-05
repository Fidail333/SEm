#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${IOS_UDID:?IOS_UDID is required}"
: "${IOS_DEVICE_NAME:?IOS_DEVICE_NAME is required}"
: "${IOS_PLATFORM_VERSION:?IOS_PLATFORM_VERSION is required}"

APPIUM_URL="${APPIUM_URL:-http://127.0.0.1:4723}"

pytest -n 1 \
  --targets real_iphone \
  --appium-url "$APPIUM_URL" \
  --alluredir=allure-results
