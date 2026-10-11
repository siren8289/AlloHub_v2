# 1단계: 빌드
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
# 배포에서는 같은 주소의 /api 로 요청하므로 서버 주소를 비운다.
ENV VITE_API_URL=""
RUN npx vite build

# 2단계: nginx로 정적 파일 제공
FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
