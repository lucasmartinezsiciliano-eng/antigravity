FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY public ./public
COPY server.js .
RUN mkdir -p /data
ENV CRM_DATA_DIR=/data
EXPOSE 9999
CMD ["node", "server.js"]
