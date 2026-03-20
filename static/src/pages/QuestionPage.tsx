import type { ReactNode } from 'react';
import { useState } from 'react';
import { CheckCircle, Copy, Download, FileText, Loader2, Play, XCircle } from 'lucide-react';
import { api } from '../services/api';

export default function QuestionPage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [parsed, setParsed] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [model, setModel] = useState('doubao');

  const handleParse = async () => {
    if (!question.trim()) {
      setError('请输入题目内容');
      return;
    }

    setLoading(true);
    setError(null);
    setParsed(null);

    try {
      console.log('[QuestionPage] parseQuestion request', { model, question });
      const result = await api.parseQuestion(question, model);
      console.log('[QuestionPage] parseQuestion response', result);
      if (result.success && result.data) {
        setParsed(result.data);
      } else {
        const errorMsg = result.error?.message || result.error || result.message || '解析失败';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '解析失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSolve = async () => {
    if (!question.trim()) {
      setError('请输入题目内容');
      return;
    }

    setLoading(true);
    setError(null);
    setParsed(null);

    try {
      console.log('[QuestionPage] autoSolve request', { model, question });
      const result = await api.autoSolve(question, model);
      console.log('[QuestionPage] autoSolve response', result);
      if (result.success && result.data) {
        setParsed(result.data);
      } else {
        const errorMsg = result.error?.message || result.error || result.message || '求解失败';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '求解失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!parsed) {
      return;
    }
    await navigator.clipboard.writeText(JSON.stringify(parsed, null, 2));
    alert('已复制到剪贴板');
  };

  const handleDownload = () => {
    if (!parsed) {
      return;
    }
    const blob = new Blob([JSON.stringify(parsed, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'parsed_result.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <FileText className="w-6 h-6" />
          题目解析
        </h1>
        <p className="text-gray-600">输入偏微分方程题目，使用大模型自动解析为结构化 JSON。</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">题目输入</h2>

            <InputGroup label="模型选择">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="doubao">豆包 (Doubao)</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude">Claude</option>
              </select>
            </InputGroup>

            <InputGroup label="题目内容">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="例如：求解一维热传导方程 u_t = k * u_xx，在区间 [0, L] 上，边界条件 u(0,t)=u(L,t)=0，初始条件 u(x,0)=sin(pi*x/L)。"
                className="w-full h-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </InputGroup>

            <div className="flex gap-3">
              <ActionButton onClick={handleParse} loading={loading} label="解析题目" loadingLabel="解析中..." colorClass="bg-blue-600 hover:bg-blue-700" />
              <ActionButton onClick={handleAutoSolve} loading={loading} label="自动求解" loadingLabel="求解中..." colorClass="bg-green-600 hover:bg-green-700" />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 flex items-start gap-2">
              <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold">错误</div>
                <div>{error}</div>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          {parsed ? (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  解析结果
                </h2>
                <div className="flex gap-2">
                  <IconButton title="复制" onClick={handleCopy}>
                    <Copy className="w-4 h-4" />
                  </IconButton>
                  <IconButton title="下载" onClick={handleDownload}>
                    <Download className="w-4 h-4" />
                  </IconButton>
                </div>
              </div>

              <pre className="bg-gray-50 p-4 rounded-md overflow-auto max-h-96 text-sm">{JSON.stringify(parsed, null, 2)}</pre>
            </div>
          ) : (
            !loading && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="text-center text-gray-500 py-12">
                  <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>输入题目后点击“解析题目”或“自动求解”。</p>
                  <p className="text-sm mt-2">结果会显示在这里。</p>
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}

function InputGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      {children}
    </div>
  );
}

function ActionButton({
  onClick,
  loading,
  label,
  loadingLabel,
  colorClass,
}: {
  onClick: () => void;
  loading: boolean;
  label: string;
  loadingLabel: string;
  colorClass: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`flex-1 text-white py-2 px-4 rounded-md transition-colors disabled:bg-gray-400 flex items-center justify-center gap-2 ${colorClass}`}
    >
      {loading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          {loadingLabel}
        </>
      ) : (
        <>
          <Play className="w-4 h-4" />
          {label}
        </>
      )}
    </button>
  );
}

function IconButton({ title, onClick, children }: { title: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
      title={title}
    >
      {children}
    </button>
  );
}
