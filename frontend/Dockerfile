# Etapa de build
FROM node:20-alpine AS builder
WORKDIR /app

# Instalar dependencias
COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm@8 || true
RUN pnpm install --frozen-lockfile || pnpm install

# Copiar código y construir
COPY . .
RUN pnpm run build

# Etapa de producción
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copiar archivos estáticos y producción desde builder
COPY --from=builder /app/.next .next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Instalar solo dependencias de producción
RUN npm install -g pnpm@8 || true
RUN pnpm install --prod --frozen-lockfile || pnpm install --prod

EXPOSE 3000

CMD ["pnpm", "start"]
