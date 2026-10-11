package com.allohub.screen;

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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/** AI 서버는 가짜(Mock)로 바꾸고, Spring의 저장·조회 흐름만 확인한다. */
@SpringBootTest
@AutoConfigureMockMvc
class ScreenControllerTest {

    @Autowired
    MockMvc mockMvc;

    @Autowired
    ObjectMapper objectMapper;

    @MockBean
    AiClient aiClient;

    @Test
    void createAndGet() throws Exception {
        given(aiClient.screen(any())).willReturn(objectMapper.readTree("""
                {"company_name":"삼성전자","corp_name":"삼성전자(주)","stock_code":"A005930","market":"KOSPI",
                 "ml_score":12.0,"dl_score":14.0,"score":13.0,"grade":"stable",
                 "dividend_rate":2.1,"net_profit":1000,"default_count":0,"suspend_count":0,
                 "rehab_count":0,"reduction_count":0,
                 "explanation":"안정 단계입니다.","explanation_source":"basic"}
                """));

        mockMvc.perform(post("/api/screens")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"companyName\":\"삼성전자\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").exists())
                .andExpect(jsonPath("$.grade").value("stable"))
                .andExpect(jsonPath("$.score").value(13.0));

        mockMvc.perform(get("/api/screens"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].companyName").value("삼성전자"));
    }

    @Test
    void blankNameReturns400() throws Exception {
        mockMvc.perform(post("/api/screens")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"companyName\":\"\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errorCode").value("VALIDATION_ERROR"));
    }
}
