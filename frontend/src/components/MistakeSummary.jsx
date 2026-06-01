import { useState, useEffect } from 'react';
import { fetchMistakeSummary } from '../api/client';

export default function MistakeSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchMistakeSummary();
      setData(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="summary-loading">📊 加载统计中...</div>;
  if (error) return <div className="summary-error">❌ {error}</div>;
  if (!data || !data.summary) return <div className="summary-empty">暂无数据</div>;

  const entries = Object.entries(data.summary).sort((a, b) => b[1].count - a[1].count);

  return (
    <div className="mistake-summary">
      <div className="summary-header">
        <h3>📊 错题本统计</h3>
        <button className="summary-refresh" onClick={loadSummary} title="刷新">
          🔄
        </button>
      </div>

      {/* 概览卡片 */}
      <div className="summary-cards">
        <div className="summary-card total">
          <div className="summary-card-value">{data.total}</div>
          <div className="summary-card-label">总条目</div>
        </div>
        <div className="summary-card mistake">
          <div className="summary-card-value">{data.mistake_count}</div>
          <div className="summary-card-label">❌ 错题</div>
        </div>
        <div className="summary-card weak">
          <div className="summary-card-value">{data.weak_count}</div>
          <div className="summary-card-label">⚠️ 薄弱点</div>
        </div>
      </div>

      {/* 按知识点统计 */}
      <h4 style={{ marginTop: 20, marginBottom: 10 }}>📌 知识点分布</h4>
      {entries.length === 0 ? (
        <p className="summary-empty">暂无明显薄弱知识点</p>
      ) : (
        <table className="summary-table">
          <thead>
            <tr>
              <th>知识点</th>
              <th>数量</th>
              <th>主要类型</th>
              <th>涉及科目</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([topic, info]) => (
              <tr key={topic}>
                <td>
                  {topic}
                  {info.count >= 3 && <span className="hot-badge">🔥 高频</span>}
                </td>
                <td className="summary-count">{info.count}</td>
                <td>
                  <span className={`type-badge ${info.type === '薄弱点' ? 'weak' : 'mistake'}`}>
                    {info.type === '薄弱点' ? '⚠️ 薄弱点' : '❌ 错题'}
                  </span>
                </td>
                <td>{info.subjects?.join(', ') || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}