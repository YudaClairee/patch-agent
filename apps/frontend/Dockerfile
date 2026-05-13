FROM node:20.17-alpine AS builder

WORKDIR /app
RUN npm install -g pnpm@10.33.3
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build

FROM node:20.17-alpine
WORKDIR /app
COPY --from=builder /app/.output ./.output
EXPOSE 3000
ENV PORT=3000
CMD ["node", ".output/server/index.mjs"]
