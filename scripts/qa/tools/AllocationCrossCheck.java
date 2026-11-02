import com.allohub.allocation.AllocationCalculator;

import java.util.List;

/** 도구 B. JUnit 없이 배분 계산을 다시 확인한다. */
public class AllocationCrossCheck {

    public static void main(String[] args) {
        check("TC-UNIT-J-001",
                AllocationCalculator.split(100L, List.of(33.33, 33.33, 33.34)),
                List.of(33L, 33L, 34L));
        check("TC-UNIT-J-002",
                AllocationCalculator.split(100000L, List.of(60.0, 40.0)),
                List.of(60000L, 40000L));
    }

    private static void check(String id, List<Long> actual, List<Long> expected) {
        String status = actual.equals(expected) ? "PASS" : "FAIL";
        System.out.println(id + " " + status + " actual=" + actual + " expected=" + expected);
    }
}
