#!/usr/bin/env bash
set -euo pipefail
mkdir -p "$HOME/bin"
export PATH="$HOME/bin:$PATH"

if ! command -v kubectl >/dev/null 2>&1; then
  VER=$(curl -fsSL https://dl.k8s.io/release/stable-1.31.txt)
  curl -fsSL -o "$HOME/bin/kubectl" "https://dl.k8s.io/release/${VER}/bin/linux/amd64/kubectl"
  chmod +x "$HOME/bin/kubectl"
  echo "installed kubectl ${VER}"
fi

if ! command -v kind >/dev/null 2>&1; then
  curl -fsSL -o "$HOME/bin/kind" https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
  chmod +x "$HOME/bin/kind"
  echo "installed kind v0.27.0"
fi

kubectl version --client
kind version
