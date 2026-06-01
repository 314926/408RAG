import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generateSimilarQuestion } from '../api/client';

export default function SimilarQuestion() {
  const [topic, setTopic] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await generateSimilarQuestion(topic.trim());
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '生成失败');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleGenerate();
  };

  return (
    <div className="similar-question">
      <h3>🎯 同类题生成</h3>
      <p className="section-desc">输入一个知识点，AI 会基于该知识点生成一道同类题目以检测掌握程度。</p>

      <div className="similar-input-row">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入知识点，如「进程同步」「LRU替换」..."
          className="similar-input"
        />
        <button
          className="generate-btn"
          onClick={handleGenerate}
          disabled={!topic.trim() || loading}
        >
          {loading ? '⏳ 生成中...' : '🎲 生成同类题'}
        </button>
      </div>

      {error && <div className="similar-error">❌ {error}</div>}

      {result && (
        <div className="similar-result">
          <div className="similar-source-tag">
            {result.source === 'exercise_db'
              ? '📚 来自练习题库'
              : '🤖 AI 生成'}
          </div>
          <div className="similar-topic-tag">📌 {result.topic}</div>

          <h4>📝 题目</h4>
          <div className="similar-question-text">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {result.question}
            </ReactMarkdown>
          </div>

          <details className="similar-answer-details">
            <summary>👁️ 查看答案</summary>
            <div className="similar-answer-text">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {result.answer}
              </ReactMarkdown>
            </div>
          </details>
        </div>
      )}

      {/* 常见知识点快速选择 */}
      <div className="quick-topics">
        <span className="quick-label">快速选择：</span>
        {['进程同步', 'Cache替换', 'TCP拥塞控制', '页面置换', '死锁', 'KMP算法'].map((t) => (
          <button
            key={t}
            className="quick-topic-btn"
            onClick={() => { setTopic(t); setResult(null); setError(null); }}
          >
            {t}
          </button>
        ))}
      </div>
    </div>
  );
}