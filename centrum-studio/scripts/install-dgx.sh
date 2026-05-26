#!/usr/bin/env bash
# install-dgx.sh — one-shot setup for centrum-studio on NVIDIA DGX Spark (Ubuntu 22.04 ARM64).
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/centrum-studio}"
DATA_DIR="${CENTRUM_STUDIO_DATA_DIR:-/srv/centrum-studio}"
REPO_URL="${REPO_URL:-https://github.com/placiano/centrum-studio.git}"

echo "==> centrum-studio install on DGX Spark"
arch=$(uname -m)
if [[ "$arch" != "aarch64" && "$arch" != "arm64" ]]; then
  echo "WARNING: expected ARM64 (aarch64), got $arch — continuing anyway."
fi

echo "==> Creating data directories at ${DATA_DIR}"
sudo mkdir -p "${DATA_DIR}"/{renders,souls,music,luts,cache,workflows}
sudo chown -R "$(id -u)":"$(id -g)" "${DATA_DIR}"
echo "agents" > "${DATA_DIR}/gpu_mode"

echo "==> Installing system packages (ffmpeg, libsndfile, git)"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  ffmpeg libsndfile1 libgl1 libglib2.0-0 git curl ca-certificates python3.12 python3.12-venv

echo "==> Cloning code to ${INSTALL_DIR}"
sudo mkdir -p "${INSTALL_DIR}"
sudo chown -R "$(id -u)":"$(id -g)" "${INSTALL_DIR}"
if [ ! -d "${INSTALL_DIR}/.git" ]; then
  git clone "${REPO_URL}" "${INSTALL_DIR}" || {
    echo "(repo not clonable — assuming code already pushed via scp/rsync)"
  }
fi

echo "==> Creating Python venv"
python3.12 -m venv "${INSTALL_DIR}/.venv"
source "${INSTALL_DIR}/.venv/bin/activate"

echo "==> Installing requirements (this will take a while on first run)"
pip install --upgrade pip
pip install -r "${INSTALL_DIR}/requirements.txt"
pip install -e "${INSTALL_DIR}"

echo "==> Seeding placeholder Soul"
mkdir -p "${DATA_DIR}/souls"
if [ ! -d "${DATA_DIR}/souls/placeholder" ]; then
  cp -r "${INSTALL_DIR}/souls/placeholder" "${DATA_DIR}/souls/placeholder"
  ln -snf v1 "${DATA_DIR}/souls/placeholder/ACTIVE"
fi

if [ -f "${INSTALL_DIR}/luts/centrum_brand.cube" ]; then
  cp -n "${INSTALL_DIR}/luts/centrum_brand.cube" "${DATA_DIR}/luts/" || true
fi

cat <<'EOF'

==> Done.

Next steps:
  1) Ensure ComfyUI is running on http://localhost:8188
  2) Ensure PLUR is running on http://localhost:8420 (optional — falls back to SQLite)
  3) Start MCP server:    /opt/centrum-studio/scripts/start.sh mcp
     Start UI:            /opt/centrum-studio/scripts/start.sh ui
  4) Set GPU mode:        echo saturday_video > /srv/centrum-studio/gpu_mode
EOF
