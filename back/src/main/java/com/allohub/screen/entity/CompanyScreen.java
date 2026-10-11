package com.allohub.screen.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/**
 * 기업 진단 1건.
 * 사용자가 입력한 이름과 AI 결과(ML/DL 점수, 공시 건수, 설명)를 함께 저장한다.
 * 프론트에는 이 객체를 그대로 JSON으로 보내 준다.
 */
@Entity
@Table(name = "company_screen")
public class CompanyScreen {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String companyName;     // 종목명
    private String corpName;        // 법인명
    private String stockCode;
    private String market;          // KOSPI / KOSDAQ / KONEX
    private String grade;          // stable / warning / danger
    private double mlScore;
    private double dlScore;
    private double score;           // ML과 DL의 평균
    private double dividendRate;
    private double netProfit;
    private int defaultCount;
    private int suspendCount;
    private int rehabCount;
    private int reductionCount;

    @Column(length = 2000)
    private String explanation;
    private String explanationSource;  // gemini / basic

    public Long getId() { return id; }

    public String getCompanyName() { return companyName; }
    public void setCompanyName(String companyName) { this.companyName = companyName; }

    public String getCorpName() { return corpName; }
    public void setCorpName(String corpName) { this.corpName = corpName; }

    public String getStockCode() { return stockCode; }
    public void setStockCode(String stockCode) { this.stockCode = stockCode; }

    public String getMarket() { return market; }
    public void setMarket(String market) { this.market = market; }

    public String getGrade() { return grade; }
    public void setGrade(String grade) { this.grade = grade; }

    public double getMlScore() { return mlScore; }
    public void setMlScore(double mlScore) { this.mlScore = mlScore; }

    public double getDlScore() { return dlScore; }
    public void setDlScore(double dlScore) { this.dlScore = dlScore; }

    public double getScore() { return score; }
    public void setScore(double score) { this.score = score; }

    public double getDividendRate() { return dividendRate; }
    public void setDividendRate(double dividendRate) { this.dividendRate = dividendRate; }

    public double getNetProfit() { return netProfit; }
    public void setNetProfit(double netProfit) { this.netProfit = netProfit; }

    public int getDefaultCount() { return defaultCount; }
    public void setDefaultCount(int defaultCount) { this.defaultCount = defaultCount; }

    public int getSuspendCount() { return suspendCount; }
    public void setSuspendCount(int suspendCount) { this.suspendCount = suspendCount; }

    public int getRehabCount() { return rehabCount; }
    public void setRehabCount(int rehabCount) { this.rehabCount = rehabCount; }

    public int getReductionCount() { return reductionCount; }
    public void setReductionCount(int reductionCount) { this.reductionCount = reductionCount; }

    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }

    public String getExplanationSource() { return explanationSource; }
    public void setExplanationSource(String explanationSource) { this.explanationSource = explanationSource; }
}
