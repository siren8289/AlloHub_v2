package com.allohub.allocation.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/** 출자자 1명. ratio는 퍼센트(예: 60 이면 60%). */
public class InvestorRequest {

    @NotBlank(message = "출자자 이름을 입력하세요.")
    private String name;

    @NotNull(message = "출자 비율을 입력하세요.")
    @DecimalMin(value = "0.01", message = "출자 비율은 0보다 커야 합니다.")
    @DecimalMax(value = "100", message = "출자 비율은 100 이하여야 합니다.")
    private Double ratio;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public Double getRatio() {
        return ratio;
    }

    public void setRatio(Double ratio) {
        this.ratio = ratio;
    }
}
