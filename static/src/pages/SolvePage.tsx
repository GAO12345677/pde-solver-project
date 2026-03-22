import type { ReactNode } from 'react';
import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { Activity, BarChart3, Play, Settings, TrendingUp, Zap } from 'lucide-react';
import AnimeAssistant, { type AssistantMood } from '../components/AnimeAssistant';
import PDE3DViewer from '../components/PDE3DViewer';
import SolutionChart from '../components/SolutionChart';
import StatsChart from '../components/StatsChart';
import { api } from '../services/api';
import type { SolveRequest, SolveResponse, SupportedEquationInfo } from '../types';

const Heatmap = lazy(() => import('../components/Heatmap'));

type StrategyKey = 'static_rf' | 'static_xgb' | 'dynamic_rl' | 'mlp_nn' | 'gnn_selector';
type SliceAxis = 'x' | 'y' | 'z';

type SliceView = {
  axis: SliceAxis;
  index: number;
  nx: number;
  ny: number;
  values: number[];
  meta: string;
} | null;

const STRATEGY_LABELS: Record<StrategyKey, string> = {
  static_rf: 'Random Forest',
  static_xgb: 'XGBoost',
  dynamic_rl: 'Reinforcement Learning',
  mlp_nn: 'MLP Neural Network',
  gnn_selector: 'GNN Selector',
};

const EQUATION_LABELS: Record<SolveRequest['equation_type'], string> = {
  heat1d: '1D Heat Equation',
  heat2d: '2D Heat Equation',
  heat3d: '3D Heat Equation',
  wave1d: '1D Wave Equation',
  wave2d: '2D Wave Equation',
  wave3d: '3D Wave Equation',
  poisson1d: '1D Poisson Equation',
  poisson3d: '3D Poisson Equation',
  poisson2d_nonlinear: '2D Nonlinear Poisson Equation',
};

const ALGORITHM_LABELS: Record<string, string> = {
  fdm: 'Finite Difference Method (FDM)',
  fvm: 'Finite Volume Method (FVM)',
  fem: 'Finite Element Method (FEM)',
  spectral: 'Spectral Method',
  pinn: 'PINN',
  bem: 'Boundary Element Method (BEM)',
};

function getRecommendedStrategy(equationType: SolveRequest['equation_type']): StrategyKey {
  if (equationType === 'wave1d' || equationType === 'poisson1d') {
    return 'mlp_nn';
  }
  if (equationType === 'heat2d' || equationType === 'wave2d') {
    return 'gnn_selector';
  }
  if (equationType === 'poisson2d_nonlinear') {
    return 'dynamic_rl';
  }
  return 'static_rf';
}

export default function SolvePage() {
  const [loading, setLoading] = useState(false);
  const [recommending, setRecommending] = useState(false);
  const [result, setResult] = useState<SolveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<StrategyKey>('static_rf');
  const [selectionSummary, setSelectionSummary] = useState<string | null>(null);
  const [supportedEquations, setSupportedEquations] = useState<Record<string, SupportedEquationInfo>>({});
  const [sliceAxis, setSliceAxis] = useState<SliceAxis>('z');
  const [sliceIndex, setSliceIndex] = useState(0);
  const [assistantMood, setAssistantMood] = useState<AssistantMood>('idle');
  const [assistantMsg, setAssistantMsg] = useState('欢迎来到 PDE 智能求解平台！\n需要我帮忙选算法吗？');
  const [params, setParams] = useState<SolveRequest>({
    equation_type: 'heat1d',
    accuracy: 'medium',
    realtime: 'medium',
    resource_budget: 0.75,
    boundary_condition: 'dirichlet',
    nx: 101,
    ny: 41,
    nz: 21,
    k: 1,
    c: 1,
    L: 1,
    Lx: 1,
    Ly: 1,
    Lz: 1,
    t0: 0,
    t1: 0.1,
    nt: 100,
    left_bc: 0,
    right_bc: 0,
    initial_velocity: 0,
    algorithm_key: 'fdm',
    return_full_solution: false,
  });

  const preview = result?.data?.solution_preview;
  const fullSolution = result?.data?.solution || [];
  const solveInfo = result?.data?.solve_info;
  const trainingSummary = solveInfo?.details?.training_summary;
  const equationTitle = EQUATION_LABELS[params.equation_type];
  const equationNote = supportedEquations[params.equation_type]?.note;
  const recommendedStrategy = getRecommendedStrategy(params.equation_type);
  const chartData = preview ? [...preview.head, ...preview.tail] : [];
  const isHeatmap2d =
    params.equation_type === 'heat2d' ||
    params.equation_type === 'wave2d' ||
    params.equation_type === 'poisson2d_nonlinear';
  const isThreeDimensional =
    params.equation_type === 'heat3d' ||
    params.equation_type === 'wave3d' ||
    params.equation_type === 'poisson3d';

  useEffect(() => {
    let active = true;
    void api
      .getSupportedEquations()
      .then((response) => {
        if (active && response.success && response.data?.equations) {
          setSupportedEquations(response.data.equations);
        }
      })
      .catch(() => {
        // Keep local fallback options when the capability endpoint is unavailable.
      });

    return () => {
      active = false;
    };
  }, []);

  const equationOptions = useMemo(() => {
    const fallbackOrder: SolveRequest['equation_type'][] = [
      'heat1d',
      'heat2d',
      'heat3d',
      'wave1d',
      'wave2d',
      'wave3d',
      'poisson1d',
      'poisson3d',
      'poisson2d_nonlinear',
    ];
    return fallbackOrder.filter((key) => supportedEquations[key] || EQUATION_LABELS[key]);
  }, [supportedEquations]);

  const algorithmOptions = useMemo(() => {
    const remoteOptions = supportedEquations[params.equation_type]?.algorithms;
    if (remoteOptions && remoteOptions.length > 0) {
      return remoteOptions as ReadonlyArray<NonNullable<SolveRequest['algorithm_key']>>;
    }

    switch (params.equation_type) {
      case 'heat1d':
        return ['fdm', 'fvm', 'fem', 'spectral', 'pinn'] as const;
      case 'heat2d':
      case 'heat3d':
        return ['fdm', 'fvm', 'fem'] as const;
      case 'wave1d':
      case 'wave2d':
      case 'wave3d':
        return ['fdm', 'fem', 'spectral'] as const;
      case 'poisson1d':
        return ['fdm', 'fem', 'spectral', 'bem'] as const;
      case 'poisson3d':
        return ['fdm', 'fem', 'bem'] as const;
      case 'poisson2d_nonlinear':
      default:
        return ['fdm'] as const;
    }
  }, [params.equation_type, supportedEquations]);

  useEffect(() => {
    if (params.algorithm_key && algorithmOptions.includes(params.algorithm_key)) {
      return;
    }
    setParams((current) => ({
      ...current,
      algorithm_key: algorithmOptions[0] || 'fdm',
    }));
  }, [algorithmOptions, params.algorithm_key]);

  const sliceView = useMemo<SliceView>(() => {
    if (!isThreeDimensional) {
      return null;
    }

    const nx = params.nx || 0;
    const ny = params.ny || 0;
    const nz = params.nz || 0;
    if (nx <= 0 || ny <= 0 || nz <= 0 || fullSolution.length !== nx * ny * nz) {
      return null;
    }

    const maxIndex = sliceAxis === 'x' ? nx - 1 : sliceAxis === 'y' ? ny - 1 : nz - 1;
    const clampedIndex = Math.min(Math.max(sliceIndex, 0), maxIndex);
    const values: number[] = [];

    if (sliceAxis === 'z') {
      const offset = clampedIndex * nx * ny;
      for (let row = 0; row < ny; row += 1) {
        values.push(...fullSolution.slice(offset + row * nx, offset + (row + 1) * nx));
      }
      return { axis: 'z', index: clampedIndex, nx, ny, values, meta: `z = ${clampedIndex + 1} / ${nz}` };
    }

    if (sliceAxis === 'y') {
      for (let z = 0; z < nz; z += 1) {
        for (let x = 0; x < nx; x += 1) {
          values.push(fullSolution[(z * ny + clampedIndex) * nx + x]);
        }
      }
      return { axis: 'y', index: clampedIndex, nx, ny: nz, values, meta: `y = ${clampedIndex + 1} / ${ny}` };
    }

    for (let z = 0; z < nz; z += 1) {
      for (let y = 0; y < ny; y += 1) {
        values.push(fullSolution[(z * ny + y) * nx + clampedIndex]);
      }
    }
    return { axis: 'x', index: clampedIndex, nx: ny, ny: nz, values, meta: `x = ${clampedIndex + 1} / ${nx}` };
  }, [fullSolution, isThreeDimensional, params.nx, params.ny, params.nz, sliceAxis, sliceIndex]);

  useEffect(() => {
    if (!isThreeDimensional) {
      setSliceAxis('z');
      setSliceIndex(0);
      return;
    }

    const maxIndex =
      sliceAxis === 'x'
        ? Math.max((params.nx || 1) - 1, 0)
        : sliceAxis === 'y'
          ? Math.max((params.ny || 1) - 1, 0)
          : Math.max((params.nz || 1) - 1, 0);

    if (sliceIndex > maxIndex) {
      setSliceIndex(maxIndex);
    }
  }, [isThreeDimensional, params.nx, params.ny, params.nz, sliceAxis, sliceIndex]);

  const handleRecommendAlgorithm = async () => {
    setRecommending(true);
    setError(null);
    setSelectionSummary(null);
    setAssistantMood('thinking');
    setAssistantMsg('正在分析物理特征与硬件算力...\n请稍等！');

    try {
      const features = await api.extractFeature({
        equation_type: params.equation_type,
        accuracy: params.accuracy,
        realtime: params.realtime,
        resource_budget: params.resource_budget,
        boundary_condition: params.boundary_condition,
        nx: params.nx,
        ny: params.ny,
        nz: params.nz,
      });

      const selection = await api.selectAlgorithm({
        strategy,
        physics: features.data.physics,
        hardware: features.data.hardware,
        domain: features.data.domain,
      });

      const algorithm = selection.data.algorithm_key as NonNullable<SolveRequest['algorithm_key']>;
      setParams((current) => ({ ...current, algorithm_key: algorithm }));
      setSelectionSummary(`${selection.data.algorithm_name || ALGORITHM_LABELS[algorithm] || algorithm} (${algorithm})`);
      setAssistantMood('happy');
      setAssistantMsg(`推荐完成！我觉得 ${selection.data.algorithm_key} 最适合现在的参数哦~`);
    } catch (recommendError) {
      setAssistantMood('angry');
      setAssistantMsg('哎呀，算法推荐服务似乎开小差了...');
      setError(recommendError instanceof Error ? recommendError.message : 'Algorithm recommendation failed');
    } finally {
      setRecommending(false);
    }
  };

  const handleSolve = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setAssistantMood('thinking');
    setAssistantMsg('开始执行数值求解！\n正在网格迭代中...');

    try {
      const response = await api.solve({
        ...params,
        return_full_solution: params.return_full_solution || isThreeDimensional,
      });
      setResult(response);
      setAssistantMood('happy');
      setAssistantMsg(`求解完成啦！耗时 ${response.data.solve_info.elapsed_s.toFixed(3)} 秒。\n快看下面的可视化结果吧！`);
      window.setTimeout(() => setAssistantMood('idle'), 5000);
    } catch (solveError) {
      setAssistantMood('shy');
      setAssistantMsg('求解器返回了错误...\n要不要检查一下边界条件和步长？');
      setError(solveError instanceof Error ? solveError.message : 'Solve failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      <AnimeAssistant mood={assistantMood} message={assistantMsg} />

      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">PDE Solver <span className="text-lg font-medium text-gray-500">偏微分方程求解界面</span></h1>
        <p className="text-gray-600">
          Configure PDE parameters manually, choose a selection strategy, and run 1D/2D/3D heat, 1D/2D/3D wave,
          1D/3D Poisson, and 2D nonlinear Poisson demos.
        </p>
        <p className="mt-2 text-sm text-gray-500">中文说明：左侧填写参数，右侧查看推荐算法、误差指标和结果图像；三维问题支持切片查看。</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Settings className="h-5 w-5" />
              Solve Parameters
            </h2>
            <p className="text-sm text-gray-500">中文说明：先选方程，再选算法；如果不确定算法，可先点“Recommend Algorithm”获取推荐。</p>

            <Field label="Equation Type">
              <select
                value={params.equation_type}
                onChange={(e) => setParams((current) => ({ ...current, equation_type: e.target.value as SolveRequest['equation_type'] }))}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                {equationOptions.map((key) => (
                  <option key={key} value={key}>
                    {EQUATION_LABELS[key] || key}
                  </option>
                ))}
              </select>
            </Field>

            {equationNote && <div className="rounded-md bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-500">方程说明：{equationNote}</div>}

            <Field label="Algorithm">
              <select
                value={params.algorithm_key}
                onChange={(e) => setParams((current) => ({ ...current, algorithm_key: e.target.value as SolveRequest['algorithm_key'] }))}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                {algorithmOptions.map((key) => (
                  <option key={key} value={key}>
                    {ALGORITHM_LABELS[key] || key}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Strategy">
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value as StrategyKey)}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                {(Object.keys(STRATEGY_LABELS) as StrategyKey[]).map((key) => (
                  <option key={key} value={key}>
                    {STRATEGY_LABELS[key]}
                  </option>
                ))}
              </select>
            </Field>

            <div className="text-xs text-gray-500">Recommended strategy: {STRATEGY_LABELS[recommendedStrategy]}。中文提示：这是当前方程较适合优先尝试的选择策略。</div>

            <button
              onClick={handleRecommendAlgorithm}
              disabled={loading || recommending}
              className="w-full rounded-md border border-blue-200 px-4 py-2 text-blue-700 hover:bg-blue-50 disabled:bg-gray-100"
            >
              <span className="inline-flex items-center gap-2">
                <Zap className="h-4 w-4" />
                {recommending ? 'Recommending...' : 'Recommend Algorithm'}
              </span>
            </button>

            {selectionSummary && (
              <div className="rounded-md border border-blue-100 bg-blue-50 px-3 py-2 text-sm text-blue-700">
                Current recommendation: {selectionSummary}
                <div className="mt-1 text-xs text-blue-600">中文提示：推荐结果来自特征提取和算法选择模块，而不是手工写死。</div>
              </div>
            )}

            <Field label="Accuracy">
              <SelectLevel value={params.accuracy} onChange={(value) => setParams((current) => ({ ...current, accuracy: value }))} />
            </Field>

            <Field label="Realtime">
              <SelectLevel value={params.realtime} onChange={(value) => setParams((current) => ({ ...current, realtime: value }))} />
            </Field>

            <Field label={`Resource Budget: ${params.resource_budget.toFixed(2)}`}>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={params.resource_budget}
                onChange={(e) => setParams((current) => ({ ...current, resource_budget: parseFloat(e.target.value) || 0.1 }))}
                className="w-full"
              />
            </Field>

            <Field label="Boundary Condition">
              <select
                value={params.boundary_condition}
                onChange={(e) => setParams((current) => ({ ...current, boundary_condition: e.target.value as SolveRequest['boundary_condition'] }))}
                className="w-full rounded-md border border-gray-300 px-3 py-2"
              >
                <option value="dirichlet">Dirichlet</option>
                <option value="neumann">Neumann</option>
                <option value="mixed">Mixed</option>
              </select>
            </Field>

            <NumberField label="Grid Points (nx)" value={params.nx || 0} onChange={(value) => setParams((current) => ({ ...current, nx: value }))} />

            {(params.equation_type === 'heat2d' ||
              params.equation_type === 'wave2d' ||
              params.equation_type === 'poisson2d_nonlinear' ||
              params.equation_type === 'poisson3d' ||
              params.equation_type === 'heat3d' ||
              params.equation_type === 'wave3d') && (
              <NumberField label="Grid Points (ny)" value={params.ny || 0} onChange={(value) => setParams((current) => ({ ...current, ny: value }))} />
            )}

            {isThreeDimensional && (
              <NumberField label="Grid Points (nz)" value={params.nz || 0} onChange={(value) => setParams((current) => ({ ...current, nz: value }))} />
            )}

            {(params.equation_type === 'heat1d' || params.equation_type === 'wave1d' || params.equation_type === 'poisson1d') && (
              <NumberField label="Domain Length (L)" step="0.1" value={params.L || 0} onChange={(value) => setParams((current) => ({ ...current, L: value }))} />
            )}

            {(params.equation_type === 'heat2d' ||
              params.equation_type === 'heat3d' ||
              params.equation_type === 'wave2d' ||
              params.equation_type === 'wave3d' ||
              params.equation_type === 'poisson3d') && (
              <>
                <NumberField label="Domain Length (Lx)" step="0.1" value={params.Lx || 0} onChange={(value) => setParams((current) => ({ ...current, Lx: value }))} />
                <NumberField label="Domain Length (Ly)" step="0.1" value={params.Ly || 0} onChange={(value) => setParams((current) => ({ ...current, Ly: value }))} />
              </>
            )}

            {isThreeDimensional && (
              <NumberField label="Domain Length (Lz)" step="0.1" value={params.Lz || 0} onChange={(value) => setParams((current) => ({ ...current, Lz: value }))} />
            )}

            {params.equation_type === 'heat1d' && (
              <>
                <NumberField label="Diffusion Coefficient (k)" step="0.1" value={params.k || 0} onChange={(value) => setParams((current) => ({ ...current, k: value }))} />
                <NumberField label="Start Time (t0)" step="0.1" value={params.t0 || 0} onChange={(value) => setParams((current) => ({ ...current, t0: value }))} />
                <NumberField label="End Time (t1)" step="0.1" value={params.t1 || 0} onChange={(value) => setParams((current) => ({ ...current, t1: value }))} />
              </>
            )}

            {(params.equation_type === 'heat2d' ||
              params.equation_type === 'heat3d' ||
              params.equation_type === 'wave2d' ||
              params.equation_type === 'wave3d') && (
              <>
                <NumberField
                  label={params.equation_type === 'heat2d' || params.equation_type === 'heat3d' ? 'Diffusion Coefficient (k)' : 'Wave Speed (c)'}
                  step="0.1"
                  value={params.equation_type === 'heat2d' || params.equation_type === 'heat3d' ? params.k || 0 : params.c || 0}
                  onChange={(value) =>
                    setParams((current) => ({
                      ...current,
                      ...(params.equation_type === 'heat2d' || params.equation_type === 'heat3d' ? { k: value } : { c: value }),
                    }))
                  }
                />
                <NumberField label="Start Time (t0)" step="0.1" value={params.t0 || 0} onChange={(value) => setParams((current) => ({ ...current, t0: value }))} />
                <NumberField label="End Time (t1)" step="0.1" value={params.t1 || 0} onChange={(value) => setParams((current) => ({ ...current, t1: value }))} />
                <NumberField label="Time Steps (nt)" value={params.nt || 0} onChange={(value) => setParams((current) => ({ ...current, nt: value }))} />
              </>
            )}

            {params.equation_type === 'wave1d' && (
              <>
                <NumberField label="Wave Speed (c)" step="0.1" value={params.c || 0} onChange={(value) => setParams((current) => ({ ...current, c: value }))} />
                <NumberField label="Start Time (t0)" step="0.1" value={params.t0 || 0} onChange={(value) => setParams((current) => ({ ...current, t0: value }))} />
                <NumberField label="End Time (t1)" step="0.1" value={params.t1 || 0} onChange={(value) => setParams((current) => ({ ...current, t1: value }))} />
                <NumberField label="Time Steps (nt)" value={params.nt || 0} onChange={(value) => setParams((current) => ({ ...current, nt: value }))} />
                <NumberField label="Initial Velocity" step="0.1" value={params.initial_velocity || 0} onChange={(value) => setParams((current) => ({ ...current, initial_velocity: value }))} />
              </>
            )}

            {(params.equation_type === 'heat1d' ||
              params.equation_type === 'wave1d' ||
              params.equation_type === 'wave2d' ||
              params.equation_type === 'wave3d' ||
              params.equation_type === 'poisson3d' ||
              params.equation_type === 'heat3d') && (
              <>
                <NumberField label="Left Boundary Value" step="0.1" value={params.left_bc || 0} onChange={(value) => setParams((current) => ({ ...current, left_bc: value }))} />
                <NumberField label="Right Boundary Value" step="0.1" value={params.right_bc || 0} onChange={(value) => setParams((current) => ({ ...current, right_bc: value }))} />
              </>
            )}

            <button
              onClick={handleSolve}
              disabled={loading}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              <span className="inline-flex items-center justify-center gap-2">
                <Play className="h-4 w-4" />
                {loading ? 'Solving...' : 'Start Solve'}
              </span>
            </button>
            <p className="text-xs text-gray-500">中文说明：点击后会调用后端求解接口；三维方程会自动请求完整结果以支持截面热力图。</p>
          </div>
        </div>

        <div className="space-y-6 lg:col-span-2">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>}

          {result && (
            <>
              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <Activity className="h-5 w-5" />
                  Solve Summary
                </h2>
                <div className="grid grid-cols-2 gap-4">
                  <MetricCard label="Equation Type" value={equationTitle} />
                  <MetricCard label="Recommended Algorithm" value={result.data?.recommended_algorithm || solveInfo?.algorithm || 'N/A'} />
                  <MetricCard label="Executed Algorithm" value={result.data?.executed_algorithm || solveInfo?.algorithm || 'N/A'} />
                  <MetricCard label="Elapsed Time" value={solveInfo?.elapsed_s != null ? `${solveInfo.elapsed_s.toFixed(4)}s` : 'N/A'} />
                  <MetricCard label="Status" value={solveInfo?.status || 'N/A'} />
                  {solveInfo?.estimated_error != null && <MetricCard label="Estimated Error" value={solveInfo.estimated_error.toExponential(3)} />}
                  {'l2_error' in (solveInfo || {}) && <MetricCard label="L2 Error" value={Number(solveInfo?.l2_error).toExponential(3)} />}
                  {'linf_error' in (solveInfo || {}) && <MetricCard label="Linf Error" value={Number(solveInfo?.linf_error).toExponential(3)} />}
                  {'boundary_residual' in (solveInfo || {}) && <MetricCard label="Boundary Residual" value={Number(solveInfo?.boundary_residual).toExponential(3)} />}
                  {solveInfo?.algorithm === 'pinn' && (
                    <>
                      <MetricCard label="PINN Cache" value={trainingSummary?.cache_hit ? `Hit (${trainingSummary.cache_origin || 'unknown'})` : 'Miss'} />
                      <MetricCard
                        label="PINN Training"
                        value={
                          trainingSummary?.cache_hit
                            ? `Adam ${trainingSummary.cached_adam_epochs_run || 0} / LBFGS ${trainingSummary.cached_lbfgs_steps_run || 0}`
                            : `Adam ${trainingSummary?.adam_epochs_run || 0} / LBFGS ${trainingSummary?.lbfgs_steps_run || 0}`
                        }
                      />
                    </>
                  )}
                </div>
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <BarChart3 className="h-5 w-5" />
                  Result Statistics
                </h2>
                <p className="mb-4 text-sm text-gray-500">中文说明：这里统计当前求解结果的最小值、最大值、均值和标准差，用来快速判断数值规模。</p>
                <StatsChart stats={preview?.stats} />
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <TrendingUp className="h-5 w-5" />
                  Visualization
                </h2>
                <p className="mb-4 text-sm text-gray-500">中文说明：一维显示折线图，二维显示热力图，三维显示切片热力图。</p>

                {isThreeDimensional && sliceView && (
                  <div className="mb-4 rounded-md border border-gray-200 bg-gray-50 p-4">
                    <div className="mb-3 flex flex-wrap items-center gap-3">
                      <label className="text-sm font-medium text-gray-700">
                        Slice Axis
                        <select
                          value={sliceAxis}
                          onChange={(e) => {
                            setSliceAxis(e.target.value as SliceAxis);
                            setSliceIndex(0);
                          }}
                          className="ml-2 rounded-md border border-gray-300 px-2 py-1"
                        >
                          <option value="x">x</option>
                          <option value="y">y</option>
                          <option value="z">z</option>
                        </select>
                      </label>
                      <label className="text-sm font-medium text-gray-700">
                        Slice Index
                        <input
                          type="range"
                          min={0}
                          max={sliceAxis === 'x' ? Math.max((params.nx || 1) - 1, 0) : sliceAxis === 'y' ? Math.max((params.ny || 1) - 1, 0) : Math.max((params.nz || 1) - 1, 0)}
                          step={1}
                          value={sliceView.index}
                          onChange={(e) => setSliceIndex(parseInt(e.target.value, 10) || 0)}
                          className="ml-2 align-middle"
                        />
                      </label>
                    </div>
                    <div className="text-sm text-gray-600">
                      Current slice: {sliceView.meta}, size {sliceView.ny} x {sliceView.nx}
                    </div>
                    <div className="mt-2 text-xs text-gray-500">中文提示：切换 `x / y / z` 方向可以查看三维解在不同截面上的分布情况。</div>
                  </div>
                )}

                {isHeatmap2d ? (
                  <Suspense fallback={<div className="text-sm text-gray-500">Loading heatmap...</div>}>
                    <Heatmap solution={chartData} nx={params.nx || 41} ny={params.ny || 41} title={`${equationTitle} Heatmap`} />
                  </Suspense>
                ) : isThreeDimensional && sliceView ? (
                  <PDE3DViewer
                    solution={fullSolution}
                    nx={params.nx || 0}
                    ny={params.ny || 0}
                    nz={params.nz || 0}
                    sliceAxis={sliceAxis}
                    sliceIndex={sliceIndex}
                  />
                ) : (
                  <SolutionChart solution={chartData} title={isThreeDimensional ? `${equationTitle} Slice Preview` : `${equationTitle} Solution`} />
                )}
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <Zap className="h-5 w-5" />
                  Solution Preview
                </h2>
                <p className="mb-4 text-sm text-gray-500">中文说明：这里只显示结果数组前后若干项，适合快速确认边界值和整体趋势。</p>
                <div className="space-y-2 rounded-md bg-gray-50 p-4 text-sm text-gray-700">
                  <div>First 10 values: {preview?.head?.slice(0, 10).map((value) => value.toFixed(4)).join(', ') || 'N/A'}</div>
                  <div>Last 10 values: {preview?.tail?.slice(-10).map((value) => value.toFixed(4)).join(', ') || 'N/A'}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function SelectLevel({
  value,
  onChange,
}: {
  value: 'high' | 'medium' | 'low';
  onChange: (value: 'high' | 'medium' | 'low') => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value as 'high' | 'medium' | 'low')} className="w-full rounded-md border border-gray-300 px-3 py-2">
      <option value="high">High</option>
      <option value="medium">Medium</option>
      <option value="low">Low</option>
    </select>
  );
}

function NumberField({
  label,
  value,
  onChange,
  step,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: string;
}) {
  return (
    <Field label={label}>
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(step ? parseFloat(e.target.value) || 0 : parseInt(e.target.value, 10) || 0)}
        className="w-full rounded-md border border-gray-300 px-3 py-2"
      />
    </Field>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      <span className="mb-1 block">{label}</span>
      {children}
    </label>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
      <div className="mb-1 text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="break-all text-sm font-semibold text-gray-900">{value}</div>
    </div>
  );
}
