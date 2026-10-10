package com.allohub.global.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

/** 모든 오류를 { errorCode, message } 형태의 JSON으로 돌려준다. */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<Map<String, String>> handleApiException(ApiException e) {
        if (e.getStatus().is5xxServerError()) {
            log.error("API error: {}", e.getMessage(), e);
        }
        return error(e.getStatus(), e.getErrorCode(), e.getMessage());
    }

    /** @Valid 검사에 걸린 경우. 예) "companyName: 회사 이름을 입력하세요" */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidation(MethodArgumentNotValidException e) {
        StringBuilder message = new StringBuilder();
        e.getBindingResult().getFieldErrors().forEach(fieldError ->
                message.append(fieldError.getField()).append(": ").append(fieldError.getDefaultMessage()).append(" "));
        return error(HttpStatus.BAD_REQUEST, "VALIDATION_ERROR", message.toString().trim());
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<Map<String, String>> handleInvalidJson(HttpMessageNotReadableException e) {
        return error(HttpStatus.BAD_REQUEST, "INVALID_JSON", "요청 JSON 형식이 올바르지 않습니다.");
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleUnexpected(Exception e) {
        log.error("Unhandled exception", e);
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "INTERNAL_ERROR", "서버 오류가 발생했습니다.");
    }

    private ResponseEntity<Map<String, String>> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status).body(Map.of("errorCode", code, "message", message));
    }
}
