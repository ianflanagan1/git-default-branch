#!/bin/sh
# Links git-default-branch onto your PATH, where git also finds it as `git default-branch`. Run
# with `devbox run setup`, which first runs `uv sync` to build .venv.

set -o errexit -o nounset

here=$(cd "$(dirname "$0")" && pwd -P)

"$here/.venv/bin/python" -m cli_kit.link "$here"
