#!/bin/sh
# No downloads, no cloud fallback, no global service installation.
set -eu
if command -v ollama >/dev/null 2>&1; then
    runtime=$(command -v ollama)
elif [ -x "$HOME/Applications/Ollama.app/Contents/Resources/ollama" ]; then
    runtime="$HOME/Applications/Ollama.app/Contents/Resources/ollama"
else
    echo 'Install the official Ollama runtime after reviewing its disk requirements.' >&2
    exit 1
fi
export OLLAMA_NO_CLOUD=1
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
exec "$runtime" serve
