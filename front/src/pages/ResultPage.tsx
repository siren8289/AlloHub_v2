import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getScreen, gradeLabel, type ScreenResult } from "../api/api";

// 단계마다 배경색을 다르게 준다.
function gradeClass(grade: string) {
  if (grade === "danger") return "bg-red-50 text-red-700";
  if (grade === "warning") return "bg-amber-50 text-amber-700";
  return "bg-emerald-50 text-emerald-700";
}

// 기능 1 결과: ML 점수, DL 점수, 공시 건수, 설명
export default function ResultPage() {
  const { id } = useParams();
  const [result, setResult] = useState<ScreenResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    getScreen(id)
      .then(setResult)
      .catch((e) => setError(e instanceof Error ? e.message : "결과를 불러오지 못했습니다."));
  }, [id]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!result) return <p className="text-slate-500">불러오는 중...</p>;

  const filings = [
    ["부도", result.defaultCount],
    ["영업정지", result.suspendCount],
    ["회생", result.rehabCount],
    ["감자", result.reductionCount],
  ] as const;

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-5">
      <div>
        <p className="text-sm text-slate-500">{result.market} · {result.stockCode}</p>
        <h2 className="text-2xl font-bold">{result.companyName}</h2>
        <p className="text-sm text-slate-500">{result.corpName}</p>
      </div>

      <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${gradeClass(result.grade)}`}>
        {gradeLabel(result.grade)} · {result.score}점
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="border border-slate-100 rounded-xl p-3">
          <p className="text-slate-500">머신러닝</p>
          <p className="text-lg font-semibold">{result.mlScore}점</p>
        </div>
        <div className="border border-slate-100 rounded-xl p-3">
          <p className="text-slate-500">딥러닝</p>
          <p className="text-lg font-semibold">{result.dlScore}점</p>
        </div>
        <div className="border border-slate-100 rounded-xl p-3">
          <p className="text-slate-500">현금배당률</p>
          <p className="text-lg font-semibold">{result.dividendRate}%</p>
        </div>
        <div className="border border-slate-100 rounded-xl p-3">
          <p className="text-slate-500">당기순이익</p>
          <p className="text-lg font-semibold">{result.netProfit.toLocaleString("ko-KR")}</p>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mb-2">공시 건수</h3>
        <ul className="grid grid-cols-2 gap-2 text-sm">
          {filings.map(([name, count]) => (
            <li key={name} className="border border-slate-100 rounded-lg px-3 py-2 flex justify-between">
              <span>{name}</span>
              <span>{count}건</span>
            </li>
          ))}
        </ul>
      </div>

      <p className="text-sm leading-6 whitespace-pre-wrap">{result.explanation}</p>
      <p className="text-xs text-slate-400">설명 출처: {result.explanationSource === "gemini" ? "Gemini" : "기본 문장"}</p>

      <Link
        to={`/allocate?company=${encodeURIComponent(result.companyName)}`}
        className="inline-block bg-indigo-700 text-white rounded-lg px-4 py-2 text-sm"
      >
        이 기업에 출자금 배분하기
      </Link>
    </div>
  );
}
