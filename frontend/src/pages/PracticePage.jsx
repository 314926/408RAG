import { useEffect, useState, useMemo } from 'react';
import { fetchCalculationTypes, fetchCalculation, fetchComprehensiveTypes, fetchComprehensive, addMistakeItem } from '../api/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './PracticePage.css';

export default function PracticePage() {
  const [calcTopics, setCalcTopics] = useState([]);
  const [compTopics, setCompTopics] = useState([]);
  const [practiceType, setPracticeType] = useState('calculation');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('');
  const [problem, setProblem] = useState(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showMistakeForm, setShowMistakeForm] = useState(false);
  const [mistakeType, setMistakeType] = useState('错题');
  const [formLoading, setFormLoading] = useState(false);
  const [mistakeTopic, setMistakeTopic] = useState('');

  useEffect(() => {
    fetchCalculationTypes()
      .then((d) => setCalcTopics(d.topics || []))
      .catch(() => {});
    fetchComprehensiveTypes()
      .then((d) => setCompTopics(d.topics || []))
      .catch(() => {});
  }, []);

  const topics = practiceType === 'calculation' ? calcTopics : compTopics;
  const fetchFn = practiceType === 'calculation' ? fetchCalculation : fetchComprehensive;

  // 从题型列表中提取唯一的科目列表
  const subjects = useMemo(() => {
    const set = new Set(topics.map((t) => t.subject).filter(Boolean));
    return Array.from(set).sort();
  }, [topics]);

  // 根据选中的科目过滤题型
  const filteredTopics = useMemo(() => {
    if (!selectedSubject) return topics;
    return topics.filter((t) => t.subject === selectedSubject);
  }, [topics, selectedSubject]);

  // 切换练习类型或科目时重置选择
  const handleTypeChange = (e) => {
    setPracticeType(e.target.value);
    setProblem(null);
    setSelectedSubject('');
    setSelectedTopic('');
  };

  const handleSubjectChange = (e) => {
    setSelectedSubject(e.target.value);
    setSelectedTopic('');
  };

  const handleGenerate = async () => {
    if (!selectedTopic) return;
    setLoading(true);
    setShowAnswer(false);
    try {
      const data = await fetchFn(selectedTopic);
      setProblem(data);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || '未知错误';
      setProblem({
        question: `❌ **请求失败**：${msg}`,
        solution_steps: [],
        answer: '',
        type_name: '错误',
        subject: '',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="practice-container">
      <h2>📝 专项练习</h2>

      {/* ── 控制区：两行布局 ── */}
      <div className="practice-controls">
        <div className="control-row">
          <div className="control-group">
            <label>练习类型：</label>
            <select value={practiceType} onChange={handleTypeChange}>
              <option value="calculation">🧮 计算题</option>
              <option value="comprehensive">📝 大题</option>
            </select>
          </div>

          <button
            className="practice-btn"
            onClick={handleGenerate}
            disabled={!selectedTopic || loading}
          >
            {loading ? '⏳ 生成中...' : '🎲 生成题目'}
          </button>

          <button
            className="practice-btn secondary"
            onClick={handleGenerate}
            disabled={!selectedTopic || loading}
            style={{ marginLeft: '8px' }}
          >
            🔄 换一题
          </button>
        </div>

        <div className="control-row">
          <div className="control-group">
            <label>科目：</label>
            <select value={selectedSubject} onChange={handleSubjectChange}>
              <option value="">全部科目</option>
              {subjects.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>题型：</label>
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
            >
              <option value="">
                {selectedSubject
                  ? '-- 本科目题型 --'
                  : '-- 全部题型 --'}
              </option>
              {filteredTopics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ── 题目展示 ── */}
      {problem && (
        <div className="problem-card">
          <div className="problem-header">
            <span className="problem-type">
              {problem.subject && `【${problem.subject}】`}
              {problem.type_name || selectedTopic}
            </span>
          </div>

          <div className="problem-question">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {problem.question}
            </ReactMarkdown>
          </div>

          {!showAnswer ? (
            <button
              className="practice-btn secondary"
              onClick={() => setShowAnswer(true)}
            >
              👁️ 显示答案
            </button>
          ) : (
            <>
              <div className="problem-solution">
                <h4>📖 解题步骤</h4>
                {problem.solution_steps.map((step, i) => (
                  <ReactMarkdown key={i} remarkPlugins={[remarkGfm]}>
                    {step}
                  </ReactMarkdown>
                ))}
                <div className="problem-answer">
                  <strong>✅ 答案：</strong>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {problem.answer}
                  </ReactMarkdown>
                </div>
              </div>
              <button
                className="practice-btn secondary"
                onClick={() => setShowAnswer(false)}
              >
                🙈 隐藏答案
              </button>
            </>
          )}

          {/* 错题/薄弱点按钮区 */}
          <div className="practice-mistake-actions">
            <button
              className="practice-mistake-btn mistake"
              onClick={() => {
                setMistakeType('错题');
                setMistakeTopic(problem.type_name || selectedTopic);
                setShowMistakeForm(true);
              }}
              title="加入错题本"
            >
              ❌ 加入错题本
            </button>
            <button
              className="practice-mistake-btn weak"
              onClick={() => {
                setMistakeType('薄弱点');
                setMistakeTopic(problem.type_name || selectedTopic);
                setShowMistakeForm(true);
              }}
              title="标记薄弱点"
            >
              ⚠️ 标记薄弱点
            </button>
          </div>
        </div>
      )}

      {/* 错题表单弹窗 */}
      {showMistakeForm && problem && (
        <div className="modal-overlay" onClick={() => !formLoading && setShowMistakeForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{mistakeType === '错题' ? '❌ 加入错题本' : '⚠️ 标记薄弱点'}</h3>
              <button className="modal-close" onClick={() => setShowMistakeForm(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label>题目</label>
                <textarea
                  value={problem.question}
                  readOnly
                  rows={2}
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>答案</label>
                <textarea
                  value={problem.answer}
                  readOnly
                  rows={2}
                  className="form-input"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>科目</label>
                  <input type="text" value={problem.subject || ''} readOnly className="form-input" />
                </div>
                <div className="form-group">
                  <label>知识点标签</label>
                  <input
                    type="text"
                    value={mistakeTopic}
                    onChange={(e) => setMistakeTopic(e.target.value)}
                    className="form-input"
                    placeholder="如：进程同步"
                  />
                </div>
                <div className="form-group">
                  <label>来源</label>
                  <input type="text" value="专项练习" readOnly className="form-input" />
                </div>
              </div>
              <div className="form-type-badge">
                <span className={mistakeType === '错题' ? 'badge-mistake' : 'badge-weak'}>
                  {mistakeType === '错题' ? '❌ 错题' : '⚠️ 薄弱点'}
                </span>
              </div>
            </div>
            <div className="modal-footer">
              <button className="modal-btn cancel" onClick={() => setShowMistakeForm(false)} disabled={formLoading}>
                取消
              </button>
              <button
                className="modal-btn confirm"
                onClick={async () => {
                  setFormLoading(true);
                  try {
                    await addMistakeItem({
                      question: problem.question,
                      answer: problem.answer,
                      subject: problem.subject || '',
                      topic: mistakeTopic,
                      type: mistakeType,
                      source: '专项练习',
                    });
                    setShowMistakeForm(false);
                    alert('✅ 已成功保存！');
                  } catch (err) {
                    alert('❌ 保存失败：' + (err.response?.data?.detail || err.message));
                  } finally {
                    setFormLoading(false);
                  }
                }}
                disabled={formLoading}
              >
                {formLoading ? '⏳ 保存中...' : '✅ 确认保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
