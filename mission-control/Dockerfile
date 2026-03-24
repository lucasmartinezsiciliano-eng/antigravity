FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY public ./public
COPY server.js .
RUN mkdir -p /app/data
ENV CRM_DATA_DIR=/app/data
EXPOSE 3333
CMD ["node", "server.js"]
