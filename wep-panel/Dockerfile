FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev=false
COPY . .
RUN npm run build
EXPOSE 8787
CMD ["node", "server/index.js"]
