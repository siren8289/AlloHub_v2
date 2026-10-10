import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createScreen } from "../api/api";

const INPUT = "mt-1 w-full border border-slate-200 rounded-lg px-3 py-2";

// 기능 1: 상장기업 이름을 넣고 위험 진단을 요청하는 화면
export default function ScreenPage() {
  const navigate = useNavigate();
  const [companyName, setCompanyName] = useState("삼성전자");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (!companyName.trim()) {
      setError("회사 이름을 입력하세요.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await createScreen(companyName.trim());
      navigate(`/screens/${result.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "진단에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 space-y-4">
      <h2 className="text-xl font-bold">상장기업 위험 진단</h2>
      <p className="text-sm text-slate-500">
        종목명을 입력하면 공공데이터 공시와 머신러닝·딥러닝 점수를 함께 보여 줍니다.
      </p>

      <label className="block text-sm">
        종목명
        <input
          className={INPUT}
          value={companyName}
          onChange={(e) => setCompanyName(e.target.value)}
          placeholder="예: 삼성전자"
        />
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={loading}
        className="bg-indigo-700 text-white rounded-lg px-4 py-2 disabled:opacity-50"
      >
        {loading ? "진단 중..." : "진단하기"}
      </button>
    </div>
  );
}
