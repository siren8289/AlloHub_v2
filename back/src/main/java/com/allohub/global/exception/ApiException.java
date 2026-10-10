package com.allohub.global.exception;

import org.springframework.http.HttpStatus;

/** 서비스에서 던지는 예외. GlobalExceptionHandler가 JSON 응답으로 바꾼다. */
public class ApiException extends RuntimeException {

    private final HttpStatus status;
    private final String errorCode;

    public ApiException(HttpStatus status, String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.status = status;
        this.errorCode = errorCode;
    }

    public HttpStatus getStatus() {
        return status;
    }

    public String getErrorCode() {
        return errorCode;
    }

    public static ApiException badRequest(String message) {
        return new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", message, null);
    }

    public static ApiException notFound(String message) {
        return new ApiException(HttpStatus.NOT_FOUND, "NOT_FOUND", message, null);
    }

    /** AI 서버가 응답하지 않거나 이상한 값을 돌려준 경우 */
    public static ApiException aiError(String message, Throwable cause) {
        return new ApiException(HttpStatus.BAD_GATEWAY, "AI_ERROR", message, cause);
    }
}
