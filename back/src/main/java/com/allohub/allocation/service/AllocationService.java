package com.allohub.allocation.service;

import com.allohub.ai.AiClient;
import com.allohub.allocation.AllocationCalculator;
import com.allohub.allocation.dto.AllocationRequest;
import com.allohub.allocation.dto.InvestorRequest;
import com.allohub.allocation.entity.Allocation;
import com.allohub.allocation.entity.AllocationLine;
import com.allohub.allocation.repository.AllocationRepository;
import com.allohub.global.exception.ApiException;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 메인 기능 2: 출자금 배분
 *   1. 비율 합이 100%인지 확인한다
 *   2. 원 단위로 나누고, 마지막 출자자가 나머지 원을 가져간다
 *   3. 대상 기업의 ML/DL/LLM 진단도 함께 붙인다
 */
@Service
public class AllocationService {

    private final AiClient aiClient;
    private final AllocationRepository allocationRepository;

    public AllocationService(AiClient aiClient, AllocationRepository allocationRepository) {
        this.aiClient = aiClient;
        this.allocationRepository = allocationRepository;
    }

    public Allocation allocate(AllocationRequest request) {
        List<InvestorRequest> investors = request.getInvestors();
        double ratioSum = 0;
        List<Double> ratios = new ArrayList<>();
        for (InvestorRequest investor : investors) {
            ratioSum += investor.getRatio();
            ratios.add(investor.getRatio());
        }
        // 33.33 + 33.33 + 33.34 처럼 소수 둘째 자리 반올림 오차는 허용한다.
        if (Math.abs(ratioSum - 100.0) > 0.05) {
            throw ApiException.badRequest("출자 비율의 합은 100%여야 합니다. 현재 합계: " + ratioSum);
        }

        List<Long> amounts = AllocationCalculator.split(request.getTotalAmount(), ratios);
        long amountSum = 0;
        for (Long amount : amounts) {
            amountSum += amount;
        }

        JsonNode ai = aiClient.screen(Map.of("company_name", request.getCompanyName().trim()));

        Allocation allocation = new Allocation();
        allocation.setCompanyName(ai.path("company_name").asText());
        allocation.setStockCode(ai.path("stock_code").asText());
        allocation.setMarket(ai.path("market").asText());
        allocation.setGrade(ai.path("grade").asText());
        allocation.setScore(ai.path("score").asDouble());
        allocation.setTotalAmount(request.getTotalAmount());
        allocation.setBalanced(amountSum == request.getTotalAmount());
        allocation.setExplanation(cut(ai.path("explanation").asText()));

        List<AllocationLine> lines = new ArrayList<>();
        for (int i = 0; i < investors.size(); i++) {
            AllocationLine line = new AllocationLine();
            line.setInvestorName(investors.get(i).getName().trim());
            line.setRatio(investors.get(i).getRatio());
            line.setAmount(amounts.get(i));
            lines.add(line);
        }
        allocation.setLines(lines);
        return allocationRepository.save(allocation);
    }

    public Allocation get(Long id) {
        Allocation allocation = allocationRepository.findById(id).orElse(null);
        if (allocation == null) {
            throw ApiException.notFound("배분 기록이 없습니다. id=" + id);
        }
        return allocation;
    }

    public List<Allocation> recent() {
        return allocationRepository.findTop10ByOrderByIdDesc();
    }

    private String cut(String text) {
        if (text == null) {
            return "";
        }
        return text.length() <= 2000 ? text : text.substring(0, 2000);
    }
}
