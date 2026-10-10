package com.allohub.allocation;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

/** 원 단위 배분이 투자금과 같은지 확인한다. AI 서버는 필요 없다. */
class AllocationCalculatorTest {

    @Test
    void lastInvestorTakesRemainder() {
        // 100원 × 33.33% = 33.33 → 33원. 마지막 사람이 남은 34원을 받는다.
        List<Long> amounts = AllocationCalculator.split(100, List.of(33.33, 33.33, 33.34));
        assertEquals(List.of(33L, 33L, 34L), amounts);
        assertEquals(100L, amounts.stream().mapToLong(Long::longValue).sum());
    }

    @Test
    void evenSplit() {
        List<Long> amounts = AllocationCalculator.split(100000, List.of(60.0, 40.0));
        assertEquals(List.of(60000L, 40000L), amounts);
    }
}
