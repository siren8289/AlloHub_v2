package com.allohub.screen.dto;

import jakarta.validation.constraints.NotBlank;

/** 기업 진단 요청. 종목명 또는 법인명을 넣는다. */
public class ScreenRequest {

    @NotBlank(message = "회사 이름을 입력하세요.")
    private String companyName;

    public String getCompanyName() {
        return companyName;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }
}
