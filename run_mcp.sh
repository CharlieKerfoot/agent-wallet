#!/bin/zsh
source ~/.zshrc
exec uv run --directory /Users/charliekerfoot/Dev/random_projects/agent-wallet python mcp_server.py
