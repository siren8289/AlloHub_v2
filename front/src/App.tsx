import { Link, Route, Routes } from "react-router-dom";
import AllocatePage from "./pages/AllocatePage";
import ResultPage from "./pages/ResultPage";
import ScreenPage from "./pages/ScreenPage";

// 화면 뼈대: 위쪽 메뉴 + 주소(URL)에 따라 바뀌는 본문
export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <header className="bg-white border-b border-slate-200 h-16 flex items-center px-6">
        <div className="w-full max-w-3xl mx-auto flex items-center gap-6">
          <span className="font-bold text-xl text-indigo-700">AlloHub</span>
          <Link to="/" className="text-sm hover:text-indigo-700">기업 진단</Link>
          <Link to="/allocate" className="text-sm hover:text-indigo-700">출자 배분</Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<ScreenPage />} />
          <Route path="/screens/:id" element={<ResultPage />} />
          <Route path="/allocate" element={<AllocatePage />} />
        </Routes>
        <p className="mt-8 text-xs text-slate-400">
          출처: 금융위원회 KRX상장종목정보, 공시정보 (공공데이터포털). 진단 점수는 투자 권유가 아닌 참고값입니다.
        </p>
      </main>
    </div>
  );
}
