import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createAllocation, gradeLabel, won, type AllocationResult, type InvestorInput } from "../api/api";

const INPUT = "mt-1 w-full border border-slate-200 rounded-lg px-3 py-2";

// 기능 2: 출자 비율대로 투자금을 나누고, 그 기업의 진단 결과도 같이 보여 준다.
export default function AllocatePage() {
  const [params] = useSearchParams();
  const [companyName, setCompanyName] = useState(params.get("company") ?? "삼성전자");
  const [totalAmount, setTotalAmount] = useState("100000000");
  const [investors, setInvestors] = useState<InvestorInput[]>([
    { name: "김출자", ratio: 60 },
    { name: "이출자", ratio: 40 },
  ]);
  const [result, setResult] = useState<AllocationResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // 화면에서 바로 비율 합을 보여 준다. 서버도 같은 규칙을 다시 검사한다.
  const ratioSum = useMemo(
    () => investors.reduce((sum, investor) => sum + Number(investor.ratio || 0), 0),
    [investors],
  );

  function updateInvestor(index: number, field: keyof InvestorInput, value: string) {
    setInvestors((prev) => prev.map((investor, i) => {
      if (i !== index) return investor;
      if (field === "ratio") return { ...investor, ratio: Number(value) };
      return { ...investor, name: value };
    }));
  }

  async function handleSubmit() {
    if (Number(totalAmount) <= 0) {
      setError("투자 금액은 1원 이상이어야 합니다.");
      return;
    }
    if (Math.abs(ratioSum - 100) > 0.05) {
      setError("출자 비율의 합은 100%여야 합니다.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const created = await createAllocation(companyName.trim(), Number(totalAmount), investors);
      setResult(created);
    } catch (e) {
      setError(e instanceof Error ? e.message : "배분에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-4">
        <h2 className="text-xl font-bold">출자금 배분</h2>
        <p className="text-sm text-slate-500">
          비율대로 원 단위로 나누고, 마지막 출자자가 남은 원을 받습니다. 합계는 투자금과 같아야 합니다.
        </p>

        <label className="block text-sm">
          투자 대상 종목명
          <input className={INPUT} value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
        </label>

        <label className="block text-sm">
          투자 금액 (원)
          <input className={INPUT} value={totalAmount} onChange={(e) => setTotalAmount(e.target.value)} />
        </label>

        <div className="space-y-2">
          {investors.map((investor, index) => (
            <div key={index} className="grid grid-cols-[1fr_120px_auto] gap-2 items-end">
              <label className="block text-sm">
                출자자
                <input className={INPUT} value={investor.name} onChange={(e) => updateInvestor(index, "name", e.target.value)} />
              </label>
              <label className="block text-sm">
                비율(%)
                <input className={INPUT} value={investor.ratio} onChange={(e) => updateInvestor(index, "ratio", e.target.value)} />
              </label>
              <button
                type="button"
                className="text-sm text-slate-500 pb-2"
                onClick={() => setInvestors((prev) => prev.filter((_, i) => i !== index))}
                disabled={investors.length === 1}
              >
                삭제
              </button>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            className="text-indigo-700"
            onClick={() => setInvestors((prev) => [...prev, { name: "", ratio: 0 }])}
          >
            출자자 추가
          </button>
          <span className={Math.abs(ratioSum - 100) > 0.05 ? "text-red-600" : "text-slate-500"}>
            비율 합계 {ratioSum}%
          </span>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="button"
          onClick={handleSubmit}
          disabled={loading}
          className="bg-indigo-700 text-white rounded-lg px-4 py-2 disabled:opacity-50"
        >
          {loading ? "계산 중..." : "배분하기"}
        </button>
      </div>

      {result && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-3">
          <h3 className="font-bold">{result.companyName} · {gradeLabel(result.grade)} {result.score}점</h3>
          <p className="text-sm">
            배분 합계 {won(result.lines.reduce((sum, line) => sum + line.amount, 0))}
            {" / 투자금 "}{won(result.totalAmount)}
            {" · "}{result.balanced ? "합계가 맞습니다." : "합계가 맞지 않습니다."}
          </p>
          <ul className="text-sm divide-y divide-slate-100">
            {result.lines.map((line) => (
              <li key={line.investorName + line.ratio} className="py-2 flex justify-between">
                <span>{line.investorName} ({line.ratio}%)</span>
                <span>{won(line.amount)}</span>
              </li>
            ))}
          </ul>
          <p className="text-sm leading-6 whitespace-pre-wrap">{result.explanation}</p>
        </div>
      )}
    </div>
  );
}
