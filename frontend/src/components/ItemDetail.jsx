import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ItemDetail.css';

export default function ItemDetail({ item, onClose, onSimilar, onCards }) {
  if (!item) return null;

  const getTypeBadge = () => {
    if (item.type === '薄弱点') return <span className="detail-type-badge weak">⚠️ 薄弱点</span>;
    return <span className="detail-type-badge mistake">❌ 错题</span>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content item-detail-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>📄 题目详情</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* 元信息 */}
          <div className="detail-meta">
            {getTypeBadge()}
            {item.subject && <span className="detail-subject">{item.subject}</span>}
            <span className="detail-date">{item.created_at?.slice(0, 10)}</span>
          </div>

          {/* 知识点标签 */}
          {item.topic && (
            <div className="detail-topic">
              <span>🏷️ 知识点：</span><strong>{item.topic}</strong>
            </div>
          )}

          {/* 来源 */}
          {item.source && (
            <div className="detail-source">
              <span>📎 来源：{item.source}</span>
            </div>
          )}

          {/* 全文题目 */}
          <div className="detail-section">
            <h4>📝 题目</h4>
            <div className="detail-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {item.question}
              </ReactMarkdown>
            </div>
          </div>

          {/* 正确答案 */}
          <div className="detail-section">
            <h4>✅ 正确答案</h4>
            <div className="detail-content detail-answer">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {item.answer || '（无答案记录）'}
              </ReactMarkdown>
            </div>
          </div>

          {/* 用户答案 */}
          {item.user_answer && (
            <div className="detail-section">
              <h4>✍️ 你的答案</h4>
              <div className="detail-content detail-user-answer">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {item.user_answer}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="modal-footer detail-actions">
          <button className="detail-action-btn similar" onClick={onSimilar}>
            🎯 同类题练习
          </button>
          <button className="detail-action-btn cards" onClick={onCards}>
            🃏 概念卡片
          </button>
          <button className="modal-btn cancel" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
