package com.allohub.allocation;

import com.allohub.ai.AiClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** 배분 합계와 비율 검증. AI 서버는 가짜로 바꾼다. */
@SpringBootTest
@AutoConfigureMockMvc
class AllocationControllerTest {

    @Autowired
    MockMvc mockMvc;

    @Autowired
    ObjectMapper objectMapper;

    @MockBean
    AiClient aiClient;

    private static final String AI = """
            {"company_name":"삼성전자","corp_name":"삼성전자(주)","stock_code":"A005930","market":"KOSPI",
             "ml_score":12.0,"dl_score":14.0,"score":13.0,"grade":"stable",
             "explanation":"안정 단계입니다.","explanation_source":"basic"}
            """;

    @Test
    void splitsAmountAndMarksBalanced() throws Exception {
        given(aiClient.screen(any())).willReturn(objectMapper.readTree(AI));

        String body = """
                {"companyName":"삼성전자","totalAmount":100000,
                 "investors":[{"name":"김출자","ratio":60},{"name":"이출자","ratio":40}]}
                """;
        mockMvc.perform(post("/api/allocations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.balanced").value(true))
                .andExpect(jsonPath("$.lines[0].amount").value(60000))
                .andExpect(jsonPath("$.lines[1].amount").value(40000))
                .andExpect(jsonPath("$.grade").value("stable"));
    }

    @Test
    void ratioMustSumTo100() throws Exception {
        String body = """
                {"companyName":"삼성전자","totalAmount":100000,
                 "investors":[{"name":"김출자","ratio":60},{"name":"이출자","ratio":30}]}
                """;
        mockMvc.perform(post("/api/allocations").contentType(MediaType.APPLICATION_JSON).content(body))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errorCode").value("BAD_REQUEST"));
    }
}
