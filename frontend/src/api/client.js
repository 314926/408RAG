/**
 * 408 考研知识库 — API 客户端
 *
 * 封装所有后端接口调用，React 组件通过此模块与 FastAPI 后端通信。
 * 在开发环境下，请求通过 Vite proxy 转发到 http://localhost:8000/api/...。
 * 在生产环境下，将 BASE_URL 改为实际后端地址。
 */

import axios from 'axios';

// ── 基础配置 ──
// 开发环境：Vite proxy 将 /api 转发到后端
// 生产环境：修改为实际后端地址（如 https://api.example.com/api）
const BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,          // 2 分钟超时（LLM 回答可能较慢）
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── 请求/响应拦截器（可选，用于统一错误处理） ──
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || '请求失败，请稍后重试';
    console.error('[API Error]', message);
    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════
//  问答接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 发送文本问题，获取 AI 回答。
 * @param {string} question - 用户问题
 * @param {string} [sessionId] - 会话 ID（可选）
 * @returns {Promise<{answer: string, sources: string[], retry_count: number}>}
 */
export async function sendMessage(question, sessionId) {
  const { data } = await apiClient.post('/chat', {
    question,
    session_id: sessionId || null,
  });
  return data;
}

/**
 * 上传图片并提问（multipart/form-data 方式）。
 * @param {File} imageFile - 图片文件
 * @param {string} [question] - 可选问题文本
 * @returns {Promise<{answer: string, sources: string[], retry_count: number}>}
 */
export async function sendImageMessage(imageFile, question = '') {
  const formData = new FormData();
  formData.append('file', imageFile);
  if (question) formData.append('question', question);
  const { data } = await apiClient.post('/chat/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000, // 图片问答可能需要更长时间（3分钟）
  });
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  练习接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 获取计算题（按题型）。
 * @param {string} type - 题型 id（如 'cache_hit', 'pipeline'）
 * @returns {Promise<{question: string, solution_steps: string[], answer: string, type_name: string, subject: string}>}
 */
export async function fetchCalculation(type) {
  const { data } = await apiClient.get('/practice/calculation', {
    params: { type },
  });
  return data;
}

/**
 * 获取计算题题型列表。
 * @returns {Promise<{topics: {id: string, name: string, subject: string}[]}>}
 */
export async function fetchCalculationTypes() {
  const { data } = await apiClient.get('/practice/calculation/list');
  return data;
}

/**
 * 获取大题（按题型）。
 * @param {string} type - 题型 id（如 'os_pv_producer_consumer'）
 * @returns {Promise<{question: string, solution_steps: string[], answer: string, type_name: string, subject: string}>}
 */
export async function fetchComprehensive(type) {
  const { data } = await apiClient.get('/practice/comprehensive', {
    params: { type },
  });
  return data;
}

/**
 * 获取大题题型列表。
 * @returns {Promise<{topics: {id: string, name: string, subject: string}[]}>}
 */
export async function fetchComprehensiveTypes() {
  const { data } = await apiClient.get('/practice/comprehensive/list');
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  资料导入接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 上传文件并导入向量库。
 * @param {File[]} files - 文件列表（PDF/MD/TXT）
 * @param {string} [category='uploaded'] - 分类标记
 * @returns {Promise<{files_processed: number, chunks_added: number, errors: string[]}>}
 */
export async function uploadFiles(files, category = 'uploaded') {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  formData.append('category', category);
  const { data } = await apiClient.post('/ingest', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000, // 上传+导入可能需要较长时间（5分钟）
  });
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  考情分析接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 请求考情分析，生成报告。
 * @returns {Promise<{report: string, stats: object}>}
 */
export async function requestAnalysis() {
  const { data } = await apiClient.post('/analyze', {}, {
    timeout: 300000, // 分析可能需要较长时间（5分钟）
  });
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  错题本与薄弱点接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 添加错题或薄弱点。
 * @param {{
 *   question: string,
 *   answer: string,
 *   subject?: string,
 *   topic?: string,
 *   type?: string,        // "错题" 或 "薄弱点"
 *   source?: string,
 *   user_answer?: string,
 *   image_base64?: string
 * }} entry
 * @returns {Promise<{id: string, status: string}>}
 */
export async function addMistakeItem(entry) {
  const { data } = await apiClient.post('/mistake/add', entry);
  return data;
}

/**
 * 获取错题/薄弱点列表（支持筛选）。
 * @param {object} [filters]
 * @param {string} [filters.type] - "错题" / "薄弱点" / ""
 * @param {string} [filters.subject] - "DS" / "CO" / "OS" / "CN" / ""
 * @param {string} [filters.topic] - 知识点标签
 * @returns {Promise<{items: object[], count: number}>}
 */
export async function fetchMistakeList(filters = {}) {
  const params = {};
  if (filters.type) params.type = filters.type;
  if (filters.subject) params.subject = filters.subject;
  if (filters.topic) params.topic = filters.topic;
  const { data } = await apiClient.get('/mistake/list', { params });
  return data;
}

/**
 * 删除指定错题/薄弱点。
 * @param {string} itemId
 * @returns {Promise<{status: string, id: string}>}
 */
export async function deleteMistakeItem(itemId) {
  const { data } = await apiClient.delete(`/mistake/${itemId}`);
  return data;
}

/**
 * 导出错题/薄弱点。
 * @param {string} format - "markdown" 或 "pdf"
 * @param {string[]} [itemIds] - 指定导出的条目 ID（可选）
 * @returns {Promise<Blob>} 返回文件 Blob
 */
export async function exportMistakes(format = 'markdown', itemIds = null) {
  const { data } = await apiClient.post('/mistake/export',
    { format, item_ids: itemIds },
    { responseType: 'blob', timeout: 60000 }
  );
  return data;
}

/**
 * 获取错题本分类统计。
 * @returns {Promise<{summary: object, total: number, weak_count: number, mistake_count: number}>}
 */
export async function fetchMistakeSummary() {
  const { data } = await apiClient.get('/mistake/summary');
  return data;
}

/**
 * 生成同类题。
 * @param {string} topic - 知识点
 * @returns {Promise<{question: string, answer: string, source: string, topic: string}>}
 */
export async function generateSimilarQuestion(topic) {
  const { data } = await apiClient.post('/mistake/similar', { topic });
  return data;
}

/**
 * 生成 Q&A 概念卡片。
 * @param {string[]} concepts - 概念列表
 * @returns {Promise<{cards: object[], count: number}>}
 */
export async function generateCards(concepts) {
  const { data } = await apiClient.post('/mistake/cards', { concepts });
  return data;
}

/**
 * 导出 Q&A 卡片。
 * @param {string} format - "markdown" 或 "anki"
 * @returns {Promise<Blob>}
 */
export async function exportCards(format = 'markdown') {
  const { data } = await apiClient.get('/mistake/cards/export', {
    params: { format },
    responseType: 'blob',
    timeout: 60000,
  });
  return data;
}

// ── 向后兼容的旧接口 ──

/**
 * （旧）添加错题。
 * @deprecated 改用 addMistakeItem
 */
export async function addMistake(entry) {
  const { data } = await apiClient.post('/mistake_book', entry);
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  聊天历史 & 追问接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 获取所有聊天会话列表。
 * @returns {Promise<{sessions: object[], count: number}>}
 */
export async function fetchChatSessions() {
  const { data } = await apiClient.get('/chat/history');
  return data;
}

/**
 * 获取指定会话的详细消息。
 * @param {string} sessionId
 * @returns {Promise<{session: object}>}
 */
export async function fetchChatSessionDetail(sessionId) {
  const { data } = await apiClient.get(`/chat/history/${sessionId}`);
  return data;
}

/**
 * 删除指定聊天会话。
 * @param {string} sessionId
 * @returns {Promise<object>}
 */
export async function deleteChatSession(sessionId) {
  const { data } = await apiClient.delete(`/chat/history/${sessionId}`);
  return data;
}

/**
 * 导出指定会话为 Markdown。
 * @param {string} sessionId
 * @returns {Promise<Blob>}
 */
export async function exportChatSession(sessionId) {
  const { data } = await apiClient.post('/chat/export',
    { session_id: sessionId },
    { responseType: 'blob', timeout: 30000 }
  );
  return data;
}

/**
 * 追问接口：基于上下文继续对话或出同类题。
 * @param {string} question - 追问内容
 * @param {string} sessionId - 会话ID
 * @param {string} previousQuestion - 之前的问题
 * @param {string} previousAnswer - 之前的回答
 * @returns {Promise<{answer: string, sources: string[]}>}
 */
export async function sendFollowUp(question, sessionId, previousQuestion, previousAnswer) {
  const { data } = await apiClient.post('/chat/follow-up', {
    question,
    session_id: sessionId,
    previous_question: previousQuestion,
    previous_answer: previousAnswer,
  });
  return data;
}

/**
 * 导出同类题为 Markdown。
 * @param {string} topic - 知识点
 * @returns {Promise<Blob>}
 */
export async function exportSimilarQuestion(topic) {
  const { data } = await apiClient.post('/mistake/similar/export',
    { topic, format: 'markdown' },
    { responseType: 'blob', timeout: 30000 }
  );
  return data;
}

/**
 * （旧）获取错题列表。
 * @deprecated 改用 fetchMistakeList
 */
export async function fetchMistakes() {
  const { data } = await apiClient.get('/mistake_book');
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  健康检查
// ═══════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
//  练习题库接口
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 获取练习题库列表。
 * @param {string} [subject] - 科目筛选（DS/CO/OS/CN）
 * @param {string} [keyword] - 关键词搜索
 * @param {number} [limit=50] - 最大返回数
 * @returns {Promise<{items: object[], count: number, subjects: string[]}>}
 */
export async function fetchExerciseList(subject = '', keyword = '', limit = 50) {
  const params = {};
  if (subject) params.subject = subject;
  if (keyword) params.keyword = keyword;
  if (limit) params.limit = limit;
  const { data } = await apiClient.get('/exercise/list', { params });
  return data;
}

/**
 * 搜索练习题库。
 * @param {string} q - 搜索关键词
 * @param {number} [limit=20] - 最大返回数
 * @returns {Promise<{items: object[], count: number, keyword: string}>}
 */
export async function searchExercise(q, limit = 20) {
  const { data } = await apiClient.get('/exercise/search', {
    params: { q, limit },
  });
  return data;
}

// ═══════════════════════════════════════════════════════════════════════════
//  健康检查
// ═══════════════════════════════════════════════════════════════════════════

/**
 * 健康检查。
 * @returns {Promise<{status: string, api_key_configured: boolean, vectorstore_ready: boolean, ...}>}
 */
export async function checkHealth() {
  const { data } = await apiClient.get('/health');
  return data;
}

export default apiClient;
