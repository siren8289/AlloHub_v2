package com.allohub.allocation;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;

/**
 * 출자 비율대로 원 단위 금액을 나눈다.
 *
 * 소수점 때문에 합이 투자금과 어긋나지 않게,
 * 마지막 출자자가 남은 원을 모두 가져간다.
 * 그래서 배분액 합계는 항상 투자금과 같다.
 */
public final class AllocationCalculator {

    private AllocationCalculator() {
    }

    public static List<Long> split(long totalAmount, List<Double> ratios) {
        List<Long> amounts = new ArrayList<>();
        long used = 0;

        for (int i = 0; i < ratios.size(); i++) {
            boolean last = i == ratios.size() - 1;
            if (last) {
                amounts.add(totalAmount - used);
                continue;
            }
            // 예) 100원 × 33.33% = 33.33원 → 소수점은 버리고 33원
            long part = BigDecimal.valueOf(totalAmount)
                    .multiply(BigDecimal.valueOf(ratios.get(i)))
                    .divide(BigDecimal.valueOf(100), 0, RoundingMode.DOWN)
                    .longValue();
            amounts.add(part);
            used += part;
        }
        return amounts;
    }
}
