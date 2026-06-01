import { BrowserRouter as Router, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import ChatPage from './pages/ChatPage';
import PracticePage from './pages/PracticePage';
import DataPage from './pages/DataPage';
import MistakePage from './pages/MistakePage';
import WeaknessPage from './pages/WeaknessPage';
import ReinforcementPage from './pages/ReinforcementPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-layout">
        {/* 导航栏 */}
        <nav className="nav-bar">
          <div className="nav-brand">
            <span className="nav-logo">📚</span>
            <span className="nav-title">408 考研知识库</span>
          </div>
          <div className="nav-links">
            <NavLink to="/chat" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              💬 聊天
            </NavLink>
            <NavLink to="/practice" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              📝 练习
            </NavLink>
            <NavLink to="/mistakes" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              ❌ 错题本
            </NavLink>
            <NavLink to="/weakness" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              ⚠️ 薄弱点
            </NavLink>
            <NavLink to="/reinforce" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              🎯 强化
            </NavLink>
            <NavLink to="/data" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              📂 数据
            </NavLink>
          </div>
        </nav>

        {/* 页面内容 */}
        <main className="main-content">
          <Routes>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/practice" element={<PracticePage />} />
            <Route path="/mistakes" element={<MistakePage />} />
            <Route path="/weakness" element={<WeaknessPage />} />
            <Route path="/reinforce" element={<ReinforcementPage />} />
            <Route path="/data" element={<DataPage />} />
            <Route path="/" element={<Navigate to="/chat" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
