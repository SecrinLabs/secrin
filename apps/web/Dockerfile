# Web Application Docker Container
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy workspace configuration files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy shared packages
COPY packages/ ./packages/

# Copy web application
COPY apps/web/ ./apps/web/

# Install dependencies
RUN pnpm install --no-frozen-lockfile

# Build the web application
RUN cd apps/web && pnpm build

# Expose port
EXPOSE 3000

# Start the application
CMD ["pnpm", "--filter", "web", "start"]
