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
      setError('Please enter a PDE question. 请输入题目内容。');
      return;
    }

    setLoading(true);
    setError(null);
    setParsed(null);

    try {
      const result = await api.parseQuestion(question, model);
      if (result.success && result.data) {
        setParsed(result.data);
      } else {
        const errorMsg = result.error?.message || result.error || result.message || 'Parsing failed. 解析失败。';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Parsing failed. 解析失败。');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSolve = async () => {
    if (!question.trim()) {
      setError('Please enter a PDE question. 请输入题目内容。');
      return;
    }

    setLoading(true);
    setError(null);
    setParsed(null);

    try {
      const result = await api.autoSolve(question, model);
      if (result.success && result.data) {
        setParsed(result.data);
      } else {
        const errorMsg = result.error?.message || result.error || result.message || 'Auto solve failed. 自动求解失败。';
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auto solve failed. 自动求解失败。');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!parsed) {
      return;
    }
    await navigator.clipboard.writeText(JSON.stringify(parsed, null, 2));
    alert('Copied to clipboard. 已复制到剪贴板。');
  };

  const handleDownload = () => {
    if (!parsed) {
      return;
    }
    const blob = new Blob([JSON.stringify(parsed, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'parsed_result.json';
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-6">
        <h1 className="mb-2 flex items-center gap-2 text-2xl font-bold text-gray-900">
          <FileText className="h-6 w-6" />
          PDE Question Parsing
        </h1>
        <p className="text-gray-600">Parse or auto-solve a natural-language PDE prompt. 自然语言题目解析与自动求解。</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold">Prompt Input 输入区域</h2>

            <InputGroup label="Model 模型选择">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="doubao">Doubao 豆包</option>
                <option value="gpt-4">GPT-4</option>
                <option value="claude">Claude</option>
              </select>
            </InputGroup>

            <InputGroup label="Question 题目内容">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Example: Solve the 1D heat equation u_t = k u_xx on [0, L] with zero Dirichlet boundaries and initial value u(x,0)=sin(pi x / L). 例如：求解一维热传导方程……"
                className="h-64 w-full resize-none rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </InputGroup>

            <div className="flex gap-3">
              <ActionButton
                onClick={handleParse}
                loading={loading}
                label="Parse 解析"
                loadingLabel="Parsing 解析中"
                colorClass="bg-blue-600 hover:bg-blue-700"
              />
              <ActionButton
                onClick={handleAutoSolve}
                loading={loading}
                label="Auto Solve 自动求解"
                loadingLabel="Solving 求解中"
                colorClass="bg-green-600 hover:bg-green-700"
              />
            </div>
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
              <XCircle className="mt-0.5 h-5 w-5 flex-shrink-0" />
              <div>
                <div className="font-semibold">Error 错误</div>
                <div>{error}</div>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          {parsed ? (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-lg font-semibold">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  Parsed Result 解析结果
                </h2>
                <div className="flex gap-2">
                  <IconButton title="Copy 复制" onClick={handleCopy}>
                    <Copy className="h-4 w-4" />
                  </IconButton>
                  <IconButton title="Download 下载" onClick={handleDownload}>
                    <Download className="h-4 w-4" />
                  </IconButton>
                </div>
              </div>

              <pre className="max-h-96 overflow-auto rounded-md bg-gray-50 p-4 text-sm">{JSON.stringify(parsed, null, 2)}</pre>
            </div>
          ) : (
            !loading && (
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <div className="py-12 text-center text-gray-500">
                  <FileText className="mx-auto mb-4 h-12 w-12 text-gray-300" />
                  <p>Enter a question and choose Parse or Auto Solve. 输入题目后点击解析或自动求解。</p>
                  <p className="mt-2 text-sm">The JSON result will appear here. 结构化结果会显示在这里。</p>
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
      <label className="mb-2 block text-sm font-medium text-gray-700">{label}</label>
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
      className={`flex flex-1 items-center justify-center gap-2 rounded-md px-4 py-2 text-white transition-colors disabled:bg-gray-400 ${colorClass}`}
    >
      {loading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          {loadingLabel}
        </>
      ) : (
        <>
          <Play className="h-4 w-4" />
          {label}
        </>
      )}
    </button>
  );
}

function IconButton({ title, onClick, children }: { title: string; onClick: () => void; children: ReactNode }) {
  return (
    <button onClick={onClick} className="rounded-md p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900" title={title}>
      {children}
    </button>
  );
}
