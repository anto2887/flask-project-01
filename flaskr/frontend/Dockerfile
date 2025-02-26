# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Install AWS CLI
RUN apk add --no-cache python3 py3-pip curl unzip && \
    pip3 install --upgrade pip && \
    pip3 install awscli && \
    rm -rf /var/cache/apk/*

# Copy build files from previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy certificate fetching script
COPY fetch-cert.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/fetch-cert.sh

# Expose ports
EXPOSE 80 443

# Start nginx with certificate fetching
CMD ["/bin/sh", "-c", "/usr/local/bin/fetch-cert.sh && nginx -g 'daemon off;'"]