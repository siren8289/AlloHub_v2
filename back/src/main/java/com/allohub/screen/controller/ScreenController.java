package com.allohub.screen.controller;

import com.allohub.screen.dto.ScreenRequest;
import com.allohub.screen.entity.CompanyScreen;
import com.allohub.screen.service.ScreenService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * POST /api/screens        기업 진단 실행 + 저장
 * GET  /api/screens/{id}   진단 결과 다시 보기
 * GET  /api/screens        최근 진단 10건
 */
@RestController
@RequestMapping("/api/screens")
public class ScreenController {

    private final ScreenService screenService;

    public ScreenController(ScreenService screenService) {
        this.screenService = screenService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public CompanyScreen create(@Valid @RequestBody ScreenRequest request) {
        return screenService.screen(request);
    }

    @GetMapping("/{id}")
    public CompanyScreen get(@PathVariable Long id) {
        return screenService.get(id);
    }

    @GetMapping
    public List<CompanyScreen> recent() {
        return screenService.recent();
    }
}
