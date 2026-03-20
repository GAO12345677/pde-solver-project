import type { ReactNode } from 'react';
import { useEffect, useRef, useState } from 'react';
import { Activity, BarChart3, Loader2, Play, Settings, TrendingUp, XCircle, Zap } from 'lucide-react';
import { api } from '../services/api';
import type { SolveRequest, SolveResponse } from '../types';
import Heatmap from '../components/Heatmap';
import SolutionChart from '../components/SolutionChart';
import StatsChart from '../components/StatsChart';
import { useWebSocket } from '../hooks/useWebSocket';

export default function SolvePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState('');
  const [params, setParams] = useState<SolveRequest>({
    equation_type: 'heat1d',
    accuracy: 'medium',
    realtime: 'medium',
    resource_budget: 0.75,
    boundary_condition: 'dirichlet',
    nx: 101,
    k: 1.0,
    L: 1.0,
    t0: 0.0,
    t1: 0.1,
    left_bc: 0.0,
    right_bc: 0.0,
    algorithm_key: 'fdm',
    return_full_solution: false,
  });

  const { progress, status, result: wsResult, error: wsError, sendMessage, disconnect, reset } = useWebSocket(taskId);
  const wsResultRef = useRef<any>(null);
  const wsErrorRef = useRef<string | null>(null);

  useEffect(() => {
    wsResultRef.current = wsResult;
    wsErrorRef.current = wsError;

    if (wsResult) {
      setResult({
        status: 'ok',
        success: true,
        error: null,
        data: wsResult,
      });
      setError(null);
      setLoading(false);
    }
  }, [wsResult, wsError]);

  const handleSolve = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    reset();

    const nextTaskId = `task_${Date.now()}`;
    setTaskId(nextTaskId);

    sendMessage({
      action: 'solve',
      params,
    });

    window.setTimeout(async () => {
      if (wsResultRef.current) {
        return;
      }

      try {
        const httpResult = await api.solve(params);
        if (!wsResultRef.current) {
          setResult(httpResult);
          setError(null);
          setLoading(false);
        }
      } catch (httpError) {
        if (!wsResultRef.current) {
          setError(httpError instanceof Error ? httpError.message : '求解失败');
          setLoading(false);
        }
      }
    }, 800);
  };

  const handleCancel = () => {
    sendMessage({ action: 'cancel' });
    disconnect();
    reset();
    setLoading(false);
  };

  const preview = result?.data?.solution_preview;
  const chartData = preview ? [...preview.head, ...preview.tail] : [];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PDE 求解器</h1>
        <p className="text-gray-600">配置参数并求解偏微分方程。</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Settings className="w-5 h-5" />
              求解参数
            </h2>

            <div className="space-y-4">
              <Field label="方程类型">
                <select
                  value={params.equation_type}
                  onChange={(e) => setParams({ ...params, equation_type: e.target.value as SolveRequest['equation_type'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="heat1d">1D 热传导方程</option>
                  <option value="poisson2d_nonlinear">2D 非线性 Poisson 方程</option>
                </select>
              </Field>

              <Field label="算法">
                <select
                  value={params.algorithm_key}
                  onChange={(e) => setParams({ ...params, algorithm_key: e.target.value as SolveRequest['algorithm_key'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="fdm">有限差分法 (FDM)</option>
                  <option value="fem">有限元法 (FEM)</option>
                  <option value="spectral">谱方法 (Spectral)</option>
                </select>
              </Field>

              <Field label="精度要求">
                <select
                  value={params.accuracy}
                  onChange={(e) => setParams({ ...params, accuracy: e.target.value as SolveRequest['accuracy'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </Field>

              <Field label="实时性要求">
                <select
                  value={params.realtime}
                  onChange={(e) => setParams({ ...params, realtime: e.target.value as SolveRequest['realtime'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="high">高</option>
                  <option value="medium">中</option>
                  <option value="low">低</option>
                </select>
              </Field>

              <Field label={`资源预算: ${params.resource_budget.toFixed(2)}`}>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={params.resource_budget}
                  onChange={(e) => setParams({ ...params, resource_budget: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </Field>

              <Field label="边界条件">
                <select
                  value={params.boundary_condition}
                  onChange={(e) => setParams({ ...params, boundary_condition: e.target.value as SolveRequest['boundary_condition'] })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="dirichlet">Dirichlet</option>
                  <option value="neumann">Neumann</option>
                  <option value="mixed">Mixed</option>
                </select>
              </Field>

              <Field label="网格点数 (nx)">
                <input
                  type="number"
                  value={params.nx}
                  onChange={(e) => setParams({ ...params, nx: parseInt(e.target.value, 10) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </Field>

              <Field label="扩散系数 (k)">
                <input
                  type="number"
                  step="0.1"
                  value={params.k}
                  onChange={(e) => setParams({ ...params, k: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </Field>

              {loading && (
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600">求解进度</span>
                    <span className="text-sm font-medium">{(progress * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" style={{ width: `${progress * 100}%` }} />
                  </div>
                  <div className="mt-2 text-sm text-gray-600 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    {status}
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleSolve}
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  {loading ? '求解中...' : '开始求解'}
                </button>
                {loading && (
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 flex items-center justify-center gap-2"
                  >
                    <XCircle className="w-4 h-4" />
                    取消
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">{error}</div>}

          {result && (
            <>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  求解信息
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <MetricCard label="算法" value={result.data?.solve_info?.algorithm || 'N/A'} />
                  <MetricCard label="耗时" value={result.data?.solve_info?.elapsed_s != null ? `${result.data.solve_info.elapsed_s.toFixed(4)}s` : 'N/A'} />
                  <MetricCard label="评估次数" value={String(result.data?.solve_info?.nfev ?? 'N/A')} />
                  <MetricCard label="状态" value={result.data?.solve_info?.status || 'N/A'} />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  解的统计信息
                </h2>
                <StatsChart stats={preview?.stats} />
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  结果可视化
                </h2>
                {params.equation_type === 'heat1d' ? (
                  <SolutionChart solution={chartData} title="1D 热传导方程求解结果" />
                ) : (
                  <Heatmap solution={chartData} nx={params.nx || 41} ny={params.ny || 41} title="2D Poisson 方程热力图" />
                )}
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  解的预览
                </h2>
                <div className="bg-gray-50 p-4 rounded-md">
                  <div className="text-sm text-gray-600 mb-2">
                    前 50 个点: {preview?.head?.slice(0, 10).map((v) => v.toFixed(4)).join(', ') || 'N/A'}...
                  </div>
                  <div className="text-sm text-gray-600">
                    后 50 个点: ...{preview?.tail?.slice(-10).map((v) => v.toFixed(4)).join(', ') || 'N/A'}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-medium text-gray-700 mb-1">
      <span className="block mb-1">{label}</span>
      {children}
    </label>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 p-3 rounded-md">
      <div className="text-sm text-gray-600">{label}</div>
      <div className="font-semibold">{value}</div>
    </div>
  );
}
