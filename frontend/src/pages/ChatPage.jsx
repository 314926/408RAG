import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  sendMessage,
  sendImageMessage,
  addMistakeItem,
  fetchChatSessions,
  fetchChatSessionDetail,
  deleteChatSession,
  exportChatSession,
  sendFollowUp,
  generateSimilarQuestion,
} from '../api/client';
import './ChatPage.css';

function genSessionId() {
  return Math.random().toString(36).slice(2, 10);
}

export default function ChatPage() {
  // ── 消息与会话状态 ──
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(genSessionId());

  // ── 图片 ──
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  // ── 错题表单 ──
  const [showMistakeForm, setShowMistakeForm] = useState(false);
  const [mistakeFormData, setMistakeFormData] = useState({
    question: '', answer: '', subject: '', topic: '', type: '错题', source: '问答',
  });
  const [formLoading, setFormLoading] = useState(false);

  // ── 历史对话侧边栏 ──
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ── 追问状态 ──
  const [lastQuestion, setLastQuestion] = useState('');
  const [lastAnswer, setLastAnswer] = useState('');

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── 加载历史会话列表 ──
  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await fetchChatSessions();
      setSessions(data.sessions || []);
    } catch (e) {
      console.error('加载历史失败', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  const toggleHistory = () => {
    if (!showHistory) loadHistory();
    setShowHistory(!showHistory);
  };

  // ── 加载指定会话 ──
  const loadSession = async (sid) => {
    try {
      const data = await fetchChatSessionDetail(sid);
      const session = data.session;
      if (session) {
        setSessionId(session.session_id);
        setMessages(session.messages || []);
        setShowHistory(false);
        // 记录最后一条问答用于追问
        const msgs = session.messages || [];
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant') {
            setLastAnswer(msgs[i].content || '');
            // 找对应的前面问题
            if (i > 0 && msgs[i - 1].role === 'user') {
              setLastQuestion(msgs[i - 1].content || '');
            }
            break;
          }
        }
      }
    } catch (e) {
      console.error('加载会话失败', e);
    }
  };

  // ── 删除会话 ──
  const handleDeleteSession = async (sid, e) => {
    e.stopPropagation();
    if (!window.confirm('删除此会话？')) return;
    try {
      await deleteChatSession(sid);
      setSessions((prev) => prev.filter((s) => s.session_id !== sid));
    } catch (err) {
      alert('删除失败');
    }
  };

  // ── 导出当前会话 ──
  const handleExportChat = async () => {
    if (messages.length === 0) {
      alert('当前会话没有消息可以导出');
      return;
    }
    try {
      const blob = await exportChatSession(sessionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `对话记录_${sessionId}.md`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      // 如果服务器没有记录，本地生成
      const lines = [
        '# 💬 408 考研知识库 - 对话记录\n',
        `> 导出时间：${new Date().toISOString().slice(0, 19)}\n`,
        `> 消息数：${messages.length}\n`,
        '---\n',
      ];
      for (const msg of messages) {
        if (msg.role === 'user') {
          lines.push(`### 🧑‍🎓 提问\n\n${msg.content}\n---\n`);
        } else {
          lines.push(`### 🤖 回答\n\n${msg.content}\n`);
          if (msg.sources?.length) {
            lines.push(`**参考来源**：${msg.sources.join(', ')}\n`);
          }
          lines.push('---\n');
        }
      }
      const blob = new Blob([lines.join('')], { type: 'text/markdown;charset=utf-8' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `对话记录.md`;
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };

  // ── 开始新对话 ──
  const handleNewChat = () => {
    setSessionId(genSessionId());
    setMessages([]);
    setLastQuestion('');
    setLastAnswer('');
  };

  // ── 图片选择 ──
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ── 发送消息 ──
  const handleSend = async () => {
    const question = input.trim();
    if (!question && !selectedImage) return;
    if (loading) return;

    const userMessage = {
      role: 'user',
      content: question || (selectedImage ? `📷 已上传图片：${selectedImage.name}` : ''),
      hasImage: !!selectedImage,
      imageName: selectedImage?.name,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLastQuestion(question);
    setInput('');
    setLoading(true);

    try {
      let data;
      if (selectedImage) {
        data = await sendImageMessage(selectedImage, question);
        removeImage();
      } else {
        data = await sendMessage(question);
      }

      const aiMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        question: question,
      };
      setMessages((prev) => [...prev, aiMessage]);
      setLastAnswer(data.answer);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: `❌ **请求失败**：${err.response?.data?.detail || err.message || '请稍后重试'}`,
        sources: [],
        question: question,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // ── 追问 ──
  const handleFollowUp = async (prevQ, prevA) => {
    const followUpText = prompt('请输入追问内容：');
    if (!followUpText || !followUpText.trim()) return;

    const userMsg = { role: 'user', content: `📎 追问：${followUpText}` };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendFollowUp(followUpText, sessionId, prevQ, prevA);
      const aiMsg = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        question: followUpText,
      };
      setMessages((prev) => [...prev, aiMsg]);
      setLastAnswer(data.answer);
      setLastQuestion(followUpText);
    } catch (err) {
      const errMsg = {
        role: 'assistant',
        content: `❌ 追问失败：${err.response?.data?.detail || err.message}`,
        sources: [],
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  // ── 出同类题 ──
  const handleSimilarFromChat = async (text) => {
    const topic = text?.slice(0, 40) || '408知识点';
    const userMsg = { role: 'user', content: `🎯 请出一道关于「${topic}」的同类题` };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendFollowUp('出同类题', sessionId, topic, '');
      const aiMsg = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      // 回退到直接调用同类题 API
      try {
        const similarData = await generateSimilarQuestion(topic);
        const answer = `### 🎯 同类题\n\n**知识点**：${topic}\n\n${similarData.question}\n\n---\n**答案**：\n${similarData.answer}\n\n*来源：${similarData.source || 'AI'}*`;
        setMessages((prev) => [...prev, { role: 'assistant', content: answer, sources: [similarData.source || '同类题'] }]);
      } catch (e2) {
        setMessages((prev) => [...prev, { role: 'assistant', content: `❌ 生成同类题失败：${e2.message}`, sources: [] }]);
      }
    } finally {
      setLoading(false);
    }
  };

  // ── 错题表单 ──
  const openMistakeForm = (msg, type) => {
    setMistakeFormData({
      question: msg.question || '',
      answer: msg.content?.slice(0, 2000) || '',
      subject: '',
      topic: msg.question?.slice(0, 30) || '',
      type: type,
      source: msg.sources?.[0] || '问答',
    });
    setShowMistakeForm(true);
  };

  const handleMistakeFormSubmit = async () => {
    setFormLoading(true);
    try {
      await addMistakeItem(mistakeFormData);
      setShowMistakeForm(false);
      alert('✅ 已成功保存！');
    } catch (err) {
      alert('❌ 保存失败：' + (err.response?.data?.detail || err.message));
    } finally {
      setFormLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-page-layout">
      {/* ── 历史会话侧边栏 ── */}
      {showHistory && (
        <div className="chat-history-sidebar">
          <div className="history-header">
            <h3>📋 历史对话</h3>
            <button className="history-close-btn" onClick={() => setShowHistory(false)}>✕</button>
          </div>
          <div className="history-actions">
            <button className="history-new-btn" onClick={handleNewChat}>➕ 新对话</button>
            <button className="history-refresh-btn" onClick={loadHistory} disabled={historyLoading}>
              🔄 {historyLoading ? '加载中' : '刷新'}
            </button>
          </div>
          <div className="history-list">
            {historyLoading ? (
              <p className="history-loading">⏳ 加载中...</p>
            ) : sessions.length === 0 ? (
              <p className="history-empty">暂无历史对话</p>
            ) : (
              sessions.map((s) => (
                <div key={s.session_id} className="history-item" onClick={() => loadSession(s.session_id)}>
                  <div className="history-item-top">
                    <span className="history-item-count">{s.message_count} 条消息</span>
                    <button className="history-item-delete" onClick={(e) => handleDeleteSession(s.session_id, e)}>🗑️</button>
                  </div>
                  <div className="history-item-preview">{s.preview || '（空）'}</div>
                  <div className="history-item-time">{s.timestamp?.slice(0, 16) || ''}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ── 主聊天区域 ── */}
      <div className="chat-container">
        {/* ── 顶部操作栏 ── */}
        <div className="chat-topbar">
          <button className="chat-topbar-btn" onClick={toggleHistory} title="历史对话">
            📋 历史
          </button>
          <h3 className="chat-topbar-title">💬 对话</h3>
          <div className="chat-topbar-right">
            <button className="chat-topbar-btn" onClick={handleExportChat} title="导出当前对话" disabled={messages.length === 0}>
              📤 导出
            </button>
            <button className="chat-topbar-btn" onClick={handleNewChat} title="新对话">
              ➕ 新对话
            </button>
          </div>
        </div>

        {/* ── 消息列表 ── */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <h2>👋 408 考研知识库</h2>
              <p>你好！我是你的 408 计算机考研助手。</p>
              <p>你可以问我任何关于数据结构、组成原理、操作系统、计算机网络的问题。</p>
              <p>支持上传题目截图、追问、生成同类题。</p>
              <p className="chat-hint">💡 输入问题或上传图片开始对话</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-avatar">
                {msg.role === 'user' ? '🧑‍🎓' : '🤖'}
              </div>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                ) : (
                  <>
                    {msg.hasImage && <div className="message-image-badge">📷 已上传图片</div>}
                    <p>{msg.content}</p>
                  </>
                )}

                {/* 来源 */}
                {msg.sources && msg.sources.length > 0 && (
                  <div className="message-sources">
                    <span>📚 参考来源：</span>
                    {msg.sources.map((src, i) => (
                      <span key={i} className="source-tag">{src}</span>
                    ))}
                  </div>
                )}

                {/* AI 回答的操作按钮：错题本、薄弱点、追问、同类题 */}
                {msg.role === 'assistant' && msg.content && !msg.content.startsWith('❌') && (
                  <>
                    {/* 错题/薄弱点 */}
                    <div className="mistake-actions">
                      <button className="mistake-btn mistake-type" onClick={() => openMistakeForm(msg, '错题')}>❌ 错题本</button>
                      <button className="mistake-btn weak-type" onClick={() => openMistakeForm(msg, '薄弱点')}>⚠️ 薄弱点</button>
                    </div>
                    {/* 追问/同类题 */}
                    <div className="followup-actions">
                      <button className="followup-btn" onClick={() => handleFollowUp(msg.question || lastQuestion, msg.content)} disabled={loading}>
                        💬 追问
                      </button>
                      <button className="followup-btn similar" onClick={() => handleSimilarFromChat(msg.question || lastQuestion)} disabled={loading}>
                        🎯 出同类题
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content thinking">
                <span className="thinking-dot">.</span>
                <span className="thinking-dot">.</span>
                <span className="thinking-dot">.</span>
                <span className="thinking-text">思考中</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ── 图片预览 ── */}
        {imagePreview && (
          <div className="image-preview-bar">
            <img src={imagePreview} alt="预览" className="image-preview-thumb" />
            <div className="image-preview-info">
              {selectedImage?.name}
              <button className="image-remove-btn" onClick={removeImage}>✕</button>
            </div>
          </div>
        )}

        {/* ── 输入区域 ── */}
        <div className="chat-input-area">
          <button className="chat-upload-btn" onClick={() => fileInputRef.current?.click()} disabled={loading} title="上传图片">📷</button>
          <input ref={fileInputRef} type="file" accept="image/*" onChange={handleImageSelect} style={{ display: 'none' }} />
          <textarea className="chat-input" value={input} onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={selectedImage ? '输入关于这张图片的问题（可选）...' : '输入你的 408 问题...'}
            rows={2} disabled={loading} />
          <button className={`chat-send-btn ${selectedImage ? 'has-image' : ''}`}
            onClick={handleSend} disabled={(!input.trim() && !selectedImage) || loading}>
            {loading ? '⏳' : selectedImage ? '📤' : '发送'}
          </button>
        </div>
      </div>

      {/* ── 错题表单弹窗 ── */}
      {showMistakeForm && (
        <div className="modal-overlay" onClick={() => !formLoading && setShowMistakeForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{mistakeFormData.type === '错题' ? '❌ 加入错题本' : '⚠️ 标记薄弱点'}</h3>
              <button className="modal-close" onClick={() => setShowMistakeForm(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>问题</label>
                <textarea value={mistakeFormData.question} onChange={(e) => setMistakeFormData((f) => ({ ...f, question: e.target.value }))} rows={2} className="form-input" />
              </div>
              <div className="form-group">
                <label>答案</label>
                <textarea value={mistakeFormData.answer} onChange={(e) => setMistakeFormData((f) => ({ ...f, answer: e.target.value }))} rows={3} className="form-input" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>科目</label>
                  <select value={mistakeFormData.subject} onChange={(e) => setMistakeFormData((f) => ({ ...f, subject: e.target.value }))} className="form-input">
                    <option value="">自动识别</option>
                    <option value="DS">数据结构</option>
                    <option value="CO">计算机组成原理</option>
                    <option value="OS">操作系统</option>
                    <option value="CN">计算机网络</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>知识点标签</label>
                  <input type="text" value={mistakeFormData.topic} onChange={(e) => setMistakeFormData((f) => ({ ...f, topic: e.target.value }))} className="form-input" placeholder="如：进程同步" />
                </div>
                <div className="form-group">
                  <label>来源</label>
                  <input type="text" value={mistakeFormData.source} onChange={(e) => setMistakeFormData((f) => ({ ...f, source: e.target.value }))} className="form-input" />
                </div>
              </div>
              <div className="form-type-badge">
                <span className={mistakeFormData.type === '错题' ? 'badge-mistake' : 'badge-weak'}>
                  {mistakeFormData.type === '错题' ? '❌ 错题' : '⚠️ 薄弱点'}
                </span>
              </div>
            </div>
            <div className="modal-footer">
              <button className="modal-btn cancel" onClick={() => setShowMistakeForm(false)} disabled={formLoading}>取消</button>
              <button className="modal-btn confirm" onClick={handleMistakeFormSubmit} disabled={formLoading || !mistakeFormData.question.trim()}>
                {formLoading ? '⏳ 保存中...' : '✅ 确认保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
