FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy rest of files and build package to `dist`
COPY . .

ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL $VITE_BACKEND_URL

RUN npm run build

# Multi-stage build
FROM nginxinc/nginx-unprivileged:alpine

# Remove default config, and use ours
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/

# Copy HTML files from `build` image
COPY --from=build /app/dist /usr/share/nginx/html