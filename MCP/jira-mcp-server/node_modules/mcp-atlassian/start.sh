#!/bin/bash

# Debug script for MCP server
echo "Starting MCP Atlassian server..." >&2
echo "Current directory: $(pwd)" >&2
echo "Node version: $(node --version)" >&2
echo "Environment variables:" >&2
echo "  ATLASSIAN_BASE_URL: ${ATLASSIAN_BASE_URL}" >&2
echo "  ATLASSIAN_EMAIL: ${ATLASSIAN_EMAIL}" >&2
echo "  ATLASSIAN_API_TOKEN: ${ATLASSIAN_API_TOKEN:0:10}..." >&2

exec node dist/index.js