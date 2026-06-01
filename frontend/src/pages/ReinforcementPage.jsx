import { useState, useEffect } from 'react';
import SimilarQuestion from '../components/SimilarQuestion';
import ConceptCards from '../components/ConceptCards';
import { fetchExerciseList } from '../api/client';
import './ReinforcementPage.css';

const TABS = [
  { id: 'similar', label: '🎯 同类题生成', desc: '基于知识点生成同类选择题' },
  { id: 'cards', label: '🃏 概念卡片', desc: '核心概念 Q&A 问答卡片' },
  { id: 'bank', label: '📚 题库浏览', desc: '浏览 /data/exercise 选择题库' },
];

export default function ReinforcementPage() {
  const [activeTab, setActiveTab] = useState('similar');
  const [exerciseItems, setExerciseItems] = useState([]);
  const [exerciseLoading, setExerciseLoading] = useState(false);
  const [exerciseError, setExerciseError] = useState(null);
  const [bankFilter, setBankFilter] = useState({ subject: '', keyword: '' });
  const [bankSubjects, setBankSubjects] = useState([]);

  const loadExerciseBank = async () => {
    setExerciseLoading(true);
    setExerciseError(null);
    try {
      const data = await fetchExerciseList(bankFilter.subject, bankFilter.keyword, 50);
      setExerciseItems(data.items || []);
      if (data.subjects) setBankSubjects(data.subjects);
    } catch (err) {
      setExerciseError(err.response?.data?.detail || err.message || '加载失败');
    } finally {
      setExerciseLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'bank') loadExerciseBank();
  }, [activeTab]);

  return (
    <div className="reinforce-page">
      <h2>🎯 强化学习</h2>
      <p className="page-subtitle">同类题练习、概念卡片强化、选择题库浏览</p>

      {/* 选项卡导航 */}
      <div className="reinforce-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`reinforce-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="reinforce-tab-label">{tab.label}</span>
            <span className="reinforce-tab-desc">{tab.desc}</span>
          </button>
        ))}
      </div>

      {/* ── 同类题 ── */}
      {activeTab === 'similar' && (
        <div className="reinforce-panel">
          <SimilarQuestion />
        </div>
      )}

      {/* ── 概念卡片 ── */}
      {activeTab === 'cards' && (
        <div className="reinforce-panel">
          <ConceptCards />
        </div>
      )}

      {/* ── 题库浏览 ── */}
      {activeTab === 'bank' && (
        <div className="reinforce-panel">
          <h3>📚 408 选择题库</h3>
          <p className="section-desc">
            浏览 /data/exercise 目录下的 408 四科选择题，点击 🎯 可生成同类题，🃏 可生成概念卡片。
          </p>

          <div className="bank-filter-row">
            <select
              value={bankFilter.subject}
              onChange={(e) => setBankFilter((f) => ({ ...f, subject: e.target.value }))}
              className="bank-filter-select"
            >
              <option value="">全部科目</option>
              {bankSubjects.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <input
              type="text"
              placeholder="关键词搜索..."
              value={bankFilter.keyword}
              onChange={(e) => setBankFilter((f) => ({ ...f, keyword: e.target.value }))}
              className="bank-filter-input"
              onKeyDown={(e) => e.key === 'Enter' && loadExerciseBank()}
            />
            <button className="bank-filter-btn" onClick={loadExerciseBank} disabled={exerciseLoading}>
              {exerciseLoading ? '⏳' : '🔍 搜索'}
            </button>
          </div>

          {exerciseError && <div className="bank-error">❌ {exerciseError}</div>}

          {exerciseLoading ? (
            <div className="bank-loading">⏳ 加载中...</div>
          ) : exerciseItems.length === 0 ? (
            <div className="bank-empty">
              <p>📭 暂无匹配题目</p>
            </div>
          ) : (
            <div className="bank-list">
              <div className="bank-count">共 {exerciseItems.length} 道题目</div>
              {exerciseItems.map((item, idx) => (
                <div key={idx} className="bank-card">
                  <div className="bank-card-header">
                    <span className="bank-subject-tag">{item.subject || '未分类'}</span>
                    <span className="bank-source-tag">{item.source_file || ''}</span>
                    <div className="bank-card-actions">
                      <button
                        className="bank-action-btn"
                        title="生成同类题"
                        onClick={() => {
                          const topic = item.topic || item.question.slice(0, 20);
                          setActiveTab('similar');
                          // 将知识点传给 SimilarQuestion 组件的输入（通过 DOM 事件简化）
                          const input = document.querySelector('.similar-input');
                          if (input) { input.value = topic; input.dispatchEvent(new Event('input', { bubbles: true })); }
                        }}
                      >
                        🎯
                      </button>
                      <button
                        className="bank-action-btn"
                        title="生成概念卡片"
                        onClick={() => {
                          const concept = item.topic || item.question.slice(0, 20);
                          setActiveTab('cards');
                          const textarea = document.querySelector('.concept-input');
                          if (textarea) { textarea.value = concept; textarea.dispatchEvent(new Event('input', { bubbles: true })); }
                        }}
                      >
                        🃏
                      </button>
                    </div>
                  </div>
                  <div className="bank-question">
                    {item.question?.length > 300 ? item.question.slice(0, 300) + '...' : item.question}
                  </div>
                  <details className="bank-answer-details">
                    <summary>👁️ 查看答案</summary>
                    <div className="bank-answer">{item.answer}</div>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
