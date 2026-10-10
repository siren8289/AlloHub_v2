// Spring 서버와 통신하는 함수를 한 곳에 모았다.

// 서버 주소. .env 의 VITE_API_URL 이 없으면 로컬 주소를 쓴다.
const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

// ---------- 타입(데이터 모양) ----------

export type ScreenResult = {
  id: number;
  companyName: string;
  corpName: string;
  stockCode: string;
  market: string;
  grade: string;              // stable / warning / danger
  mlScore: number;
  dlScore: number;
  score: number;
  dividendRate: number;
  netProfit: number;
  defaultCount: number;
  suspendCount: number;
  rehabCount: number;
  reductionCount: number;
  explanation: string;
  explanationSource: string;  // gemini / basic
};

export type InvestorInput = {
  name: string;
  ratio: number;
};

export type AllocationLine = {
  investorName: string;
  ratio: number;
  amount: number;
};

export type AllocationResult = {
  id: number;
  companyName: string;
  stockCode: string;
  market: string;
  grade: string;
  score: number;
  totalAmount: number;
  balanced: boolean;
  explanation: string;
  lines: AllocationLine[];
};

// ---------- 공통 요청 함수 ----------

// 서버에 요청을 보내고 JSON 결과를 돌려준다. 실패하면 오류 메시지를 던진다.
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(API_URL + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    // Spring 오류는 { errorCode, message } 모양이다.
    let message = "요청에 실패했습니다.";
    try {
      const body = await response.json();
      message = body.message ?? message;
    } catch {
      // JSON이 아니면 기본 문장을 쓴다.
    }
    throw new Error(message);
  }
  return response.json();
}

// ---------- 서버 호출 ----------

export function createScreen(companyName: string) {
  return request<ScreenResult>("/api/screens", {
    method: "POST",
    body: JSON.stringify({ companyName }),
  });
}

export function getScreen(id: string) {
  return request<ScreenResult>(`/api/screens/${id}`);
}

export function createAllocation(companyName: string, totalAmount: number, investors: InvestorInput[]) {
  return request<AllocationResult>("/api/allocations", {
    method: "POST",
    body: JSON.stringify({ companyName, totalAmount, investors }),
  });
}

// 단계 코드를 화면에 보일 한글 이름으로 바꾼다.
export function gradeLabel(grade: string) {
  if (grade === "stable") return "안정";
  if (grade === "warning") return "주의";
  if (grade === "danger") return "위험";
  return grade;
}

// 원 단위 숫자에 쉼표를 붙인다. 예) 1000000 → 1,000,000원
export function won(amount: number) {
  return `${amount.toLocaleString("ko-KR")}원`;
}
