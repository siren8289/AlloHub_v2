package com.allohub.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.allohub.global.exception.ApiException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

/**
 * FastAPI(AI 서버) 호출.
 *   POST /api/v1/screen  상장기업 위험 진단 (ML + DL + LLM)
 */
@Component
public class AiClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String baseUrl;

    public AiClient(RestTemplate restTemplate, ObjectMapper objectMapper, @Value("${app.ai.base-url}") String baseUrl) {
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
        this.baseUrl = baseUrl;
    }

    public JsonNode screen(Map<String, Object> request) {
        try {
            JsonNode response = restTemplate.postForObject(baseUrl + "/api/v1/screen", request, JsonNode.class);
            if (response == null) {
                throw ApiException.aiError("AI 서버 응답이 비어 있습니다.", null);
            }
            return response;
        } catch (HttpStatusCodeException e) {
            // 404는 "그 종목이 없다"는 뜻이므로, 서버 장애와 구분해서 돌려준다.
            if (e.getStatusCode().value() == 404) {
                throw ApiException.notFound(readDetail(e));
            }
            throw ApiException.aiError("AI 서버 호출에 실패했습니다.", e);
        } catch (RestClientException e) {
            throw ApiException.aiError("AI 서버 호출에 실패했습니다.", e);
        }
    }

    /** FastAPI 오류 본문의 detail 문장을 꺼낸다. 없으면 기본 문장. */
    private String readDetail(HttpStatusCodeException e) {
        try {
            JsonNode body = objectMapper.readTree(e.getResponseBodyAsString());
            if (body.hasNonNull("detail")) {
                return body.get("detail").asText();
            }
        } catch (Exception ignored) {
            // 본문이 JSON이 아니면 아래 기본 문장을 쓴다.
        }
        return "상장 종목에서 회사를 찾지 못했습니다.";
    }
}
