# syntax=docker/dockerfile:1

# Etapa 1: gera o build de produção, como no deploy
FROM node:24-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .
RUN npm run build

# Etapa 2: só os arquivos estáticos, servidos por um nginx que não roda como root
FROM nginxinc/nginx-unprivileged:1.28-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080
