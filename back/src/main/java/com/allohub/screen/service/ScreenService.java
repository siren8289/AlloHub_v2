package com.allohub.screen.service;

import com.allohub.screen.dto.ScreenRequest;
import com.allohub.screen.entity.CompanyScreen;
import com.allohub.screen.repository.CompanyScreenRepository;
import com.allohub.ai.AiClient;
import com.allohub.global.exception.ApiException;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

/**
 * 메인 기능 1: 상장기업 위험 진단
 *   1. 회사 이름을 AI 서버에 보낸다
 *   2. ML/DL 점수와 LLM 설명을 DB에 저장한다
 *   3. 저장된 결과를 돌려준다
 */
@Service
public class ScreenService {

    private final AiClient aiClient;
    private final CompanyScreenRepository screenRepository;

    public ScreenService(AiClient aiClient, CompanyScreenRepository screenRepository) {
        this.aiClient = aiClient;
        this.screenRepository = screenRepository;
    }

    public CompanyScreen screen(ScreenRequest request) {
        // Python은 snake_case(company_name)를 쓴다.
        JsonNode ai = aiClient.screen(Map.of("company_name", request.getCompanyName().trim()));

        CompanyScreen screen = new CompanyScreen();
        screen.setCompanyName(ai.path("company_name").asText());
        screen.setCorpName(ai.path("corp_name").asText());
        screen.setStockCode(ai.path("stock_code").asText());
        screen.setMarket(ai.path("market").asText());
        screen.setGrade(ai.path("grade").asText());
        screen.setMlScore(ai.path("ml_score").asDouble());
        screen.setDlScore(ai.path("dl_score").asDouble());
        screen.setScore(ai.path("score").asDouble());
        screen.setDividendRate(ai.path("dividend_rate").asDouble());
        screen.setNetProfit(ai.path("net_profit").asDouble());
        screen.setDefaultCount(ai.path("default_count").asInt());
        screen.setSuspendCount(ai.path("suspend_count").asInt());
        screen.setRehabCount(ai.path("rehab_count").asInt());
        screen.setReductionCount(ai.path("reduction_count").asInt());
        screen.setExplanation(cut(ai.path("explanation").asText()));
        screen.setExplanationSource(ai.path("explanation_source").asText());
        return screenRepository.save(screen);
    }

    public CompanyScreen get(Long id) {
        CompanyScreen screen = screenRepository.findById(id).orElse(null);
        if (screen == null) {
            throw ApiException.notFound("진단 기록이 없습니다. id=" + id);
        }
        return screen;
    }

    public List<CompanyScreen> recent() {
        return screenRepository.findTop10ByOrderByIdDesc();
    }

    /** 설명 문장이 DB 칸(2000자)보다 길면 잘라 저장한다. */
    private String cut(String text) {
        if (text == null) {
            return "";
        }
        return text.length() <= 2000 ? text : text.substring(0, 2000);
    }
}
