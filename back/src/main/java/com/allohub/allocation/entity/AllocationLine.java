package com.allohub.allocation.entity;

import jakarta.persistence.Embeddable;

/** 출자자 1명의 배분 결과. allocation_line 테이블의 한 줄로 저장된다. */
@Embeddable
public class AllocationLine {

    private String investorName;
    private double ratio;   // 퍼센트
    private long amount;    // 원

    public String getInvestorName() { return investorName; }
    public void setInvestorName(String investorName) { this.investorName = investorName; }

    public double getRatio() { return ratio; }
    public void setRatio(double ratio) { this.ratio = ratio; }

    public long getAmount() { return amount; }
    public void setAmount(long amount) { this.amount = amount; }
}
