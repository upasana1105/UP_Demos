#!/bin/bash

# Configuration
PORT=3000
SERVER_SCRIPT="index.js"

echo "🚀 Starting Jira MCP Persistence Script..."

# Function to kill existing processes on port
cleanup() {
    echo "🧹 Cleaning up port $PORT..."
    lsof -ti :$PORT | xargs kill -9 2>/dev/null || true
}

# Start the MCP Server in the background
start_server() {
    cleanup
    echo "📂 Starting MCP Server..."
    node "$SERVER_SCRIPT" &
    SERVER_PID=$!
    echo "✅ Server started with PID $SERVER_PID"
}

# Loop to keep the tunnel alive
start_tunnel() {
    while true; do
        echo "🌐 Starting tunnel via localhost.run..."
        # This will stay connected until it crashes or is closed
        ssh -o ServerAliveInterval=60 -R 80:localhost:$PORT nokey@localhost.run
        
        echo "⚠️ Tunnel disconnected. Restarting in 5 seconds..."
        sleep 5
    done
}

# Trap exit signals
trap "kill \$SERVER_PID; exit" SIGINT SIGTERM

# Main execution
start_server
sleep 2
start_tunnel
