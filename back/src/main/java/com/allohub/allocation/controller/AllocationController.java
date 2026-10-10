package com.allohub.allocation.controller;

import com.allohub.allocation.dto.AllocationRequest;
import com.allohub.allocation.entity.Allocation;
import com.allohub.allocation.service.AllocationService;
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
 * POST /api/allocations        배분 실행 + 저장
 * GET  /api/allocations/{id}   배분 결과 다시 보기
 * GET  /api/allocations        최근 배분 10건
 */
@RestController
@RequestMapping("/api/allocations")
public class AllocationController {

    private final AllocationService allocationService;

    public AllocationController(AllocationService allocationService) {
        this.allocationService = allocationService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Allocation create(@Valid @RequestBody AllocationRequest request) {
        return allocationService.allocate(request);
    }

    @GetMapping("/{id}")
    public Allocation get(@PathVariable Long id) {
        return allocationService.get(id);
    }

    @GetMapping
    public List<Allocation> recent() {
        return allocationService.recent();
    }
}
