import { useState } from 'react';
import { uploadFiles, requestAnalysis } from '../api/client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './DataPage.css';

export default function DataPage() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState(null);

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files || []));
    setUploadResult(null);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadResult(null);
    try {
      const result = await uploadFiles(files);
      setUploadResult(result);
    } catch (err) {
      setUploadResult({ files_processed: 0, chunks_added: 0, errors: [err.message] });
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setReport(null);
    try {
      const result = await requestAnalysis();
      setReport(result.report);
    } catch (err) {
      setReport(`❌ 分析请求失败：${err.response?.data?.detail || err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="data-container">
      <h2>📂 数据管理</h2>

      {/* 文件上传 */}
      <div className="data-section">
        <h3>📤 上传资料</h3>
        <p className="data-desc">支持 PDF、Markdown、TXT 格式文件，将自动分块并导入向量库。</p>
        <div className="upload-area">
          <input
            type="file"
            multiple
            accept=".pdf,.md,.txt"
            onChange={handleFileChange}
            className="file-input"
            id="file-input"
          />
          <label htmlFor="file-input" className="file-label">
            {files.length > 0
              ? `已选择 ${files.length} 个文件`
              : '📁 点击选择文件或拖拽到此处'}
          </label>
        </div>

        {files.length > 0 && (
          <ul className="file-list">
            {files.map((f, i) => (
              <li key={i}>{f.name} ({(f.size / 1024).toFixed(1)} KB)</li>
            ))}
          </ul>
        )}

        <button
          className="data-btn"
          onClick={handleUpload}
          disabled={files.length === 0 || uploading}
        >
          {uploading ? '⏳ 导入中...' : '🚀 开始导入'}
        </button>

        {uploadResult && (
          <div className="result-card">
            <h4>导入结果</h4>
            <p>✅ 处理文件：{uploadResult.files_processed} 个</p>
            <p>📦 新增块数：{uploadResult.chunks_added} 块</p>
            {uploadResult.errors?.length > 0 && (
              <div className="error-list">
                <p>⚠️ 错误：</p>
                {uploadResult.errors.map((e, i) => (
                  <p key={i} className="error-item">{e}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 考情分析 */}
      <div className="data-section">
        <h3>📊 考情分析</h3>
        <p className="data-desc">分析历年真题，生成四科高频考点 Top10、近 3 年趋势、冷门提醒。</p>
        <button
          className="data-btn"
          onClick={handleAnalyze}
          disabled={analyzing}
        >
          {analyzing ? '⏳ 生成报告中...' : '📈 生成考情报告'}
        </button>

        {report && (
          <div className="report-card">
            <h4>📋 考情分析报告</h4>
            <div className="report-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {report}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
