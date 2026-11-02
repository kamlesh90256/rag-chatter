ARG NODE_BASE=node:22.11.0-bookworm-slim
FROM ${NODE_BASE} AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
# Use npm ci for reproducible installs in CI/dev
RUN npm ci --prefer-offline --no-audit --no-fund

FROM ${NODE_BASE} AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE_BASE} AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000
# Use the non-root "node" user for runtime
USER node
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
