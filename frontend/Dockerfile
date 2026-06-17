# Stage 1: build React app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
# npm ci requires package-lock.json; use npm install until lock file is committed.
RUN npm install

COPY . .
RUN npm run build

# Stage 2: nginx
FROM nginx:1.25-alpine

# Remove default nginx site
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx site config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React app
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
