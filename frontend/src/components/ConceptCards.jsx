import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generateCards, exportCards } from '../api/client';

export default function ConceptCards() {
  const [conceptInput, setConceptInput] = useState('');
  const [cards, setCards] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [error, setError] = useState(null);

  const parseConcepts = (input) => {
    return input
      .split(/[,，、\n]/)
      .map((s) => s.trim())
      .filter(Boolean);
  };

  const handleGenerate = async () => {
    const concepts = parseConcepts(conceptInput);
    if (concepts.length === 0) {
      setError('请输入至少一个概念');
      return;
    }
    setLoading(true);
    setError(null);
    setCards(null);
    try {
      const data = await generateCards(concepts);
      setCards(data.cards);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '生成失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExportLoading(true);
    try {
      const blob = await exportCards(format);
      const ext = format === 'anki' ? 'csv' : 'md';
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `概念卡片.${ext}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('导出失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setExportLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="concept-cards">
      <h3>🃏 核心概念 Q&A 卡片</h3>
      <p className="section-desc">
        输入核心概念，自动生成问答对卡片，支持导出为 Markdown 或 Anki 格式。
      </p>

      <div className="concept-input-row">
        <textarea
          value={conceptInput}
          onChange={(e) => setConceptInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入概念，用逗号或换行分隔，如：&#10;LRU替换&#10;TCP三次握手&#10;死锁的四个必要条件"
          rows={3}
          className="concept-input"
        />
        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={!conceptInput.trim() || loading}
        >
          {loading ? '⏳ 生成中...' : '🃏 生成卡片'}
        </button>
      </div>

      {error && <div className="cards-error">❌ {error}</div>}

      {/* 卡片列表 */}
      {cards && cards.length > 0 && (
        <div className="cards-list">
          <div className="cards-header">
            <span className="cards-count">共 {cards.length} 张卡片</span>
            <div className="cards-export-buttons">
              <button
                className="export-btn"
                onClick={() => handleExport('markdown')}
                disabled={exportLoading}
              >
                📄 导出 Markdown
              </button>
              <button
                className="export-btn anki"
                onClick={() => handleExport('anki')}
                disabled={exportLoading}
              >
                🗂️ 导出 Anki CSV
              </button>
            </div>
          </div>

          <div className="cards-grid">
            {cards.map((card, idx) => (
              <div key={idx} className="card-item">
                <div className="card-index">#{idx + 1}</div>
                <div className="card-concept-badge">{card.concept}</div>
                <div className="card-question">
                  <strong>Q:</strong>{' '}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {card.question}
                  </ReactMarkdown>
                </div>
                <div className="card-answer">
                  <strong>A:</strong>{' '}
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {card.answer}
                  </ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 常用概念快速选择 */}
      <div className="quick-topics">
        <span className="quick-label">常用概念：</span>
        {[
          'LRU替换, Cache映射方式, 写策略',
          'TCP三次握手, 四次挥手, 拥塞控制',
          'PV操作, 死锁必要条件, 银行家算法',
          '页面置换, 虚拟内存, 缺页中断',
        ].map((group) => (
          <button
            key={group}
            className="quick-topic-btn"
            onClick={() => { setConceptInput(group); setCards(null); setError(null); }}
          >
            {group}
          </button>
        ))}
      </div>
    </div>
  );
}