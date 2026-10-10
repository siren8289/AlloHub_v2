package com.allohub.allocation.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.List;

/** 출자금 배분 요청. totalAmount는 원 단위 정수다. */
public class AllocationRequest {

    @NotBlank(message = "회사 이름을 입력하세요.")
    private String companyName;

    @NotNull(message = "투자 금액을 입력하세요.")
    @Min(value = 1, message = "투자 금액은 1원 이상이어야 합니다.")
    private Long totalAmount;

    @NotEmpty(message = "출자자를 한 명 이상 입력하세요.")
    @Size(max = 20, message = "출자자는 20명까지 입력할 수 있습니다.")
    @Valid
    private List<InvestorRequest> investors;

    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }

    public Long getTotalAmount() { return totalAmount; }
    public void setTotalAmount(Long totalAmount) { this.totalAmount = totalAmount; }

    public List<InvestorRequest> getInvestors() { return investors; }
    public void setInvestors(List<InvestorRequest> investors) { this.investors = investors; }
}
