import { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  fetchMistakeList,
  deleteMistakeItem,
  exportMistakes,
  generateSimilarQuestion,
  generateCards,
  fetchMistakeSummary,
} from '../api/client';
import ItemDetail from '../components/ItemDetail';
import './MistakePage.css';

const SUBJECTS = ['', 'DS', 'CO', 'OS', 'CN'];
const SUBJECT_LABELS = { '': '全部科目', DS: '数据结构', CO: '计组原理', OS: '操作系统', CN: '计网' };

export default function WeaknessPage() {
  const [activeTab, setActiveTab] = useState('list');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [filters, setFilters] = useState({ subject: '', topic: '' });
  const [detailItem, setDetailItem] = useState(null);
  const [sidebarData, setSidebarData] = useState(null);
  const [sidebarType, setSidebarType] = useState(null);
  const [sidebarLoading, setSidebarLoading] = useState(false);
  // 全屏加载遮罩（同类题/卡片 LLM 生成期间阻止用户操作）
  const [fullPageLoading, setFullPageLoading] = useState(false);
  // 统计
  const [summary, setSummary] = useState(null);

  const loadItems = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMistakeList({ ...filters, type: '薄弱点' });
      setItems(result.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    if (activeTab === 'list') loadItems();
  }, [activeTab, loadItems]);

  useEffect(() => {
    if (activeTab === 'summary') {
      fetchMistakeSummary().then(setSummary).catch(() => {});
    }
  }, [activeTab]);

  const handleDelete = async (id) => {
    if (!window.confirm('确认删除此项？')) return;
    try {
      await deleteMistakeItem(id);
      setItems((prev) => prev.filter((i) => i.id !== id));
      setSelectedIds((prev) => { const s = new Set(prev); s.delete(id); return s; });
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id); else s.add(id);
      return s;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === items.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(items.map((i) => i.id)));
  };

  const handleExport = async () => {
    const ids = selectedIds.size > 0 ? Array.from(selectedIds) : null;
    try {
      const blob = await exportMistakes('markdown', ids);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `薄弱点导出.md`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('导出失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSimilar = async (item) => {
    setSidebarType('similar');
    setSidebarData(null);
    setFullPageLoading(true);
    try {
      const topic = item.topic || item.question.slice(0, 30);
      const data = await generateSimilarQuestion(topic);
      setSidebarData({ ...data, topic });
    } catch (err) {
      setSidebarData({ error: err.response?.data?.detail || err.message || '生成失败' });
    } finally {
      setFullPageLoading(false);
    }
  };

  const handleCards = async (item) => {
    setSidebarType('cards');
    setSidebarData(null);
    setFullPageLoading(true);
    try {
      const topic = item.topic || item.question.slice(0, 30);
      const concepts = topic.split(/[,，、]/).filter(Boolean);
      if (concepts.length === 0) concepts.push(topic);
      const data = await generateCards(concepts);
      setSidebarData(data);
    } catch (err) {
      setSidebarData({ error: err.response?.data?.detail || err.message || '生成失败' });
    } finally {
      setFullPageLoading(false);
    }
  };

  // 统计中仅显示薄弱点相关的知识点
  const weakTopics = summary ? Object.entries(summary.summary || {})
    .filter(([, info]) => info.type === '薄弱点')
    .sort((a, b) => b[1].count - a[1].count) : [];

  return (
    <div className="mistake-page">
      <h2>⚠️ 薄弱点管理</h2>
      <p className="page-subtitle">记录你掌握不牢固的知识点，针对性强化学习</p>

      <div className="mistake-tabs">
        <button className={`mistake-tab ${activeTab === 'list' ? 'active' : ''}`} onClick={() => setActiveTab('list')}>
          📋 薄弱点列表
        </button>
        <button className={`mistake-tab ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>
          📊 薄弱分布
        </button>
      </div>

      {error && <div className="mistake-error">❌ {error}</div>}

      {activeTab === 'list' && (
        <div className="mistake-list-view">
          <div className="filter-row">
            <select value={filters.subject} onChange={(e) => setFilters((f) => ({ ...f, subject: e.target.value }))}>
              {SUBJECTS.map((s) => (<option key={s} value={s}>{SUBJECT_LABELS[s]}</option>))}
            </select>
            <input type="text" placeholder="知识点关键词..." value={filters.topic}
              onChange={(e) => setFilters((f) => ({ ...f, topic: e.target.value }))} className="filter-input" />
            <button className="filter-btn" onClick={loadItems} disabled={loading}>🔍 筛选</button>
          </div>

          <div className="action-row">
            <label className="select-all-label">
              <input type="checkbox" checked={items.length > 0 && selectedIds.size === items.length}
                onChange={toggleSelectAll} />
              全选 ({selectedIds.size}/{items.length})
            </label>
            <button className="export-btn" onClick={handleExport} disabled={items.length === 0}>
              📄 导出 Markdown
            </button>
          </div>

          {loading ? (
            <div className="list-loading">⏳ 加载中...</div>
          ) : items.length === 0 ? (
            <div className="list-empty">
              <p>📭 暂无薄弱点记录</p>
              <p className="list-hint">在聊天或练习页面中点击「标记薄弱点」来添加</p>
            </div>
          ) : (
            <div className="item-list">
              {items.map((item) => (
                <div key={item.id} className={`item-card ${selectedIds.has(item.id) ? 'selected' : ''}`}>
                  <div className="item-checkbox">
                    <input type="checkbox" checked={selectedIds.has(item.id)} onChange={() => toggleSelect(item.id)} />
                  </div>
                  <div className="item-body" onClick={() => setDetailItem(item)} style={{ cursor: 'pointer' }}>
                    <div className="item-header">
                      <span className="type-tag weak">⚠️ 薄弱点</span>
                      <span className="item-subject">{item.subject}</span>
                      <span className="item-date">{item.created_at?.slice(0, 10)}</span>
                    </div>
                    <div className="item-question">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {item.question?.length > 150 ? item.question.slice(0, 150) + '...' : item.question}
                      </ReactMarkdown>
                    </div>
                    {item.topic && <span className="item-topic">🏷️ {item.topic}</span>}
                    {item.source && <span className="item-source">📎 {item.source}</span>}
                  </div>
                  <div className="item-actions">
                    <button className="item-action-btn" onClick={() => handleSimilar(item)} title="同类题">🎯</button>
                    <button className="item-action-btn" onClick={() => handleCards(item)} title="概念卡片">🃏</button>
                    <button className="item-action-btn delete" onClick={() => handleDelete(item.id)} title="删除">🗑️</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'summary' && (
        <div className="weakness-summary">
          {weakTopics.length === 0 ? (
            <p className="list-empty">暂无薄弱点数据</p>
          ) : (
            <table className="summary-table">
              <thead>
                <tr>
                  <th>知识点</th>
                  <th>出现次数</th>
                  <th>涉及科目</th>
                </tr>
              </thead>
              <tbody>
                {weakTopics.slice(0, 30).map(([topic, info]) => (
                  <tr key={topic}>
                    <td>{topic}{info.count >= 2 && <span className="hot-badge">🔥</span>}</td>
                    <td className="summary-count">{info.count}</td>
                    <td>{info.subjects?.join(', ') || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {detailItem && <ItemDetail item={detailItem} onClose={() => setDetailItem(null)}
        onSimilar={() => { const i = detailItem; setDetailItem(null); handleSimilar(i); }}
        onCards={() => { const i = detailItem; setDetailItem(null); handleCards(i); }}
      />}

      {/* ── 全屏加载遮罩（生成同类题/卡片期间阻止所有操作） ── */}
      {fullPageLoading && (
        <div className="loading-overlay">
          <div className="loading-overlay-content">
            <div className="loading-spinner"></div>
            <div className="loading-overlay-title">⏳ 正在生成{sidebarType === 'cards' ? '概念卡片' : '同类题'}</div>
            <div className="loading-overlay-hint">
              AI 正在参考题库和知识库分析出题…<br />
              请稍候，生成完成后会自动显示结果
            </div>
          </div>
        </div>
      )}

      {/* ── 同类题/卡片结果弹窗（仅在生成完成后显示） ── */}
      {sidebarData && !fullPageLoading && (
        <div className="modal-overlay" onClick={() => { setSidebarData(null); setSidebarType(null); }}>
          <div className="modal-content sidebar-result" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{sidebarType === 'similar' ? '🎯 同类题' : '🃏 概念卡片'}</h3>
              <button className="modal-close" onClick={() => { setSidebarData(null); setSidebarType(null); }}>✕</button>
            </div>
            <div className="modal-body">
              {sidebarData?.error ? (
                <p className="mistake-error">❌ {sidebarData.error}</p>
              ) : sidebarType === 'similar' ? (
                <div className="similar-result">
                  <div className="similar-source-tag">{sidebarData.source === 'exercise_db' ? '📚 题库' : '🤖 AI'}</div>
                  <div className="similar-topic-tag">📌 {sidebarData.topic}</div>
                  <h4>📝 题目</h4>
                  <div className="similar-question-text">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{sidebarData.question}</ReactMarkdown>
                  </div>
                  <details className="similar-answer-details">
                    <summary>👁️ 查看答案</summary>
                    <div className="similar-answer-text">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{sidebarData.answer}</ReactMarkdown>
                    </div>
                  </details>
                </div>
              ) : (
                <div className="cards-list-inline">
                  <p>共 {sidebarData.cards?.length || 0} 张卡片</p>
                  {(sidebarData.cards || []).map((card, idx) => (
                    <div key={idx} className="card-item" style={{ marginBottom: 10 }}>
                      <div className="card-concept-badge">{card.concept}</div>
                      <div className="card-question"><strong>Q:</strong> {card.question}</div>
                      <div className="card-answer"><strong>A:</strong> {card.answer}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
