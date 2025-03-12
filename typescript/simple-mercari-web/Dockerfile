FROM node:20-alpine
WORKDIR /app
RUN addgroup -S mercari && adduser -S trainee -G mercari

COPY . .
RUN npm ci

RUN chown -R trainee:mercari /app
USER trainee

CMD ["npm", "start", "--", "--host", "0.0.0.0"]

