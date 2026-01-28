#!/usr/bin/env bash
set -euo pipefail

# Helper script to build and run the NotesVault Docker image and perform quick checks.
# Usage:
#   ./scripts/run_container.sh build        # build the image
#   ./scripts/run_container.sh test-nginx   # run a quick nginx presence/test inside a temporary container
#   ./scripts/run_container.sh run          # run container in foreground mapping ports (default)
#   ./scripts/run_container.sh run-detach   # run container in background and tail logs
#   ./scripts/run_container.sh shell        # open an interactive shell inside a throwaway container
#
# Environment overrides:
#   IMAGE_NAME (default: notesvault:local)
#   HOST_PORT  (default: 8080)  -> maps to container port 80 (nginx)
#   DB_URL     (default: sqlite:///./notes_app.db)
#   SECRET_KEY (default: dev-secret)

IMAGE_NAME=${IMAGE_NAME:-notesvault:local}
HOST_PORT=${HOST_PORT:-8080}
DB_URL=${DB_URL:-sqlite:///./notes_app.db}
SECRET_KEY=${SECRET_KEY:-dev-secret}

function usage() {
  echo "Usage: $0 {build|test-nginx|run|run-detach|shell|nginx-t}"
  exit 1
}

function build() {
  echo "Building Docker image $IMAGE_NAME..."
  docker build -t "$IMAGE_NAME" .
  echo "Build complete."
}

function test_nginx_in_image() {
  echo "Testing whether nginx is available inside image $IMAGE_NAME..."
  docker run --rm "$IMAGE_NAME" sh -c 'if command -v nginx >/dev/null 2>&1; then echo "NGINX_FOUND=$(command -v nginx)"; nginx -v || true; else echo "NGINX_NOT_FOUND"; fi'
}

function run_foreground() {
  echo "Running $IMAGE_NAME in foreground (host:$HOST_PORT -> container:80)."
  echo "DB_URL=$DB_URL SECRET_KEY=(hidden)"
  docker run --rm -p "${HOST_PORT}":80 -p 8000:8000 \
    -e DATABASE_URL="$DB_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    --name notesvault_run \
    "$IMAGE_NAME"
}

function run_detached() {
  echo "Running $IMAGE_NAME detached (host:$HOST_PORT -> container:80)."
  docker run -d -p "${HOST_PORT}":80 -p 8000:8000 \
    -e DATABASE_URL="$DB_URL" \
    -e SECRET_KEY="$SECRET_KEY" \
    --name notesvault_run \
    "$IMAGE_NAME"
  echo "Container started. Showing last 200 lines of logs (follow with docker logs -f notesvault_run):"
  docker logs --tail 200 notesvault_run || true
}

function shell_into_image() {
  echo "Starting interactive shell in $IMAGE_NAME (will exit when you type 'exit')."
  docker run --rm -it --entrypoint sh "$IMAGE_NAME"
}

function nginx_test_cmd() {
  # run nginx -t if present, otherwise report
  docker run --rm "$IMAGE_NAME" sh -c 'if command -v nginx >/dev/null 2>&1; then echo "-> nginx exists at $(command -v nginx)"; nginx -t || true; else echo "-> nginx not found inside image."; fi'
}

COMMAND=${1:-run}
case "$COMMAND" in
  build) build ;;
  test-nginx|nginx-t) test_nginx_in_image ;;
  run) run_foreground ;;
  run-detach) run_detached ;;
  shell) shell_into_image ;;
  *) usage ;;
esac

