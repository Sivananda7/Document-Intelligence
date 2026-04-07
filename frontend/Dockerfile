FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

EXPOSE 5173

# Expose host so Vite is accessible from outside the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
