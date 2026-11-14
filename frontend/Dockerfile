FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_NEON_AUTH_URL
ARG VITE_SUPPORT_EMAIL
ARG VITE_GOOGLE_SIGN_IN_ENABLED=false
ENV VITE_NEON_AUTH_URL=$VITE_NEON_AUTH_URL VITE_SUPPORT_EMAIL=$VITE_SUPPORT_EMAIL VITE_GOOGLE_SIGN_IN_ENABLED=$VITE_GOOGLE_SIGN_IN_ENABLED
RUN test -n "$VITE_NEON_AUTH_URL" && npm run build

FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/templates/nginx.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV MOMENTUM_API_UPSTREAM=api:8000 \
    NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1 \
    NGINX_ENVSUBST_OUTPUT_DIR=/tmp \
    NGINX_ENVSUBST_FILTER="^(MOMENTUM_API_UPSTREAM|NGINX_LOCAL_RESOLVERS)$"
USER nginx
EXPOSE 8080
CMD ["nginx", "-c", "/tmp/nginx.conf", "-g", "daemon off;"]
