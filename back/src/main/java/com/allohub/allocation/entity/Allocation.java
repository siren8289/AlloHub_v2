package com.allohub.allocation.entity;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.Table;

import java.util.ArrayList;
import java.util.List;

/**
 * 출자금 배분 1건.
 * 투자금, 대상 기업의 위험 단계, 출자자별 금액이 한곳에 저장된다.
 */
@Entity
@Table(name = "allocation")
public class Allocation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String companyName;
    private String stockCode;
    private String market;
    private String grade;
    private double score;
    private long totalAmount;
    private boolean balanced;   // 배분액 합계 == 투자금 이면 true

    @Column(length = 2000)
    private String explanation;

    // 결과 화면에서 출자자 목록을 바로 쓰려고, 조회할 때 함께 읽어 온다.
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "allocation_line", joinColumns = @JoinColumn(name = "allocation_id"))
    private List<AllocationLine> lines = new ArrayList<>();

    public Long getId() { return id; }

    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }

    public String getStockCode() { return stockCode; }
    public void setStockCode(String stockCode) { this.stockCode = stockCode; }

    public String getMarket() { return market; }
    public void setMarket(String market) { this.market = market; }

    public String getGrade() { return grade; }
    public void setGrade(String grade) { this.grade = grade; }

    public double getScore() { return score; }
    public void setScore(double score) { this.score = score; }

    public long getTotalAmount() { return totalAmount; }
    public void setTotalAmount(long totalAmount) { this.totalAmount = totalAmount; }

    public boolean isBalanced() { return balanced; }
    public void setBalanced(boolean balanced) { this.balanced = balanced; }

    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }

    public List<AllocationLine> getLines() { return lines; }
    public void setLines(List<AllocationLine> lines) { this.lines = lines; }
}
