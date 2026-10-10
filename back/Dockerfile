# syntax=docker/dockerfile:1

# 1단계: 빌드
FROM eclipse-temurin:17-jdk-jammy AS build
WORKDIR /workspace

# 빌드 설정만 먼저 복사해서 라이브러리를 받아 둔다. (소스만 바뀌면 이 단계는 캐시 사용)
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew && ./gradlew --no-daemon dependencies > /dev/null

COPY src ./src
RUN ./gradlew --no-daemon bootJar -x test

# 2단계: 실행
FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build /workspace/build/libs/*.jar /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
