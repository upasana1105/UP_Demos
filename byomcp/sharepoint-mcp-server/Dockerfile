# Build stage
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Production stage
FROM node:20-slim

WORKDIR /app

# Copy from builder
COPY --from=builder /app ./

# Set environment to production
ENV NODE_ENV=production

# Expose the port (Cloud Run uses PORT env var)
EXPOSE 3000

# Start the server
CMD ["node", "index.js"]
