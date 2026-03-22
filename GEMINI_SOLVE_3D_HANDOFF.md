# Gemini Solve 3D Handoff

下面内容可直接复制给 Gemini。建议先发送 Prompt，再按顺序发送文件代码块。

## Prompt

我有一个现成项目，需要你只帮我做前端可视化增强和页面角色交互增强，不要重建项目，不要改后端接口定义。

项目背景：
- 项目名称：PDE 智能求解与金融分析平台
- 后端：FastAPI
- 前端：React + TypeScript + Vite
- 当前有 Solve 页面，底部已经有 Visualization 区域
- 我希望对 PDE 页面底部的可视化区域做更高级的 3D 交互增强
- 同时我还希望在其它页面加入“会动的二次元助手立绘/看板娘”式互动前端元素

你的任务边界：
- 只做前端
- 不要重建新项目
- 不要输出 Next.js / Vue / Svelte 版本
- 不要改后端接口字段
- 不要假设不存在的接口
- 输出必须能接入我现有 React + TypeScript + Vite 项目
- 优先增强现有 Solve 页面底部的 Visualization 区域，而不是重写整个页面
- 角色交互部分也必须是前端可落地方案，不要依赖后端新增接口

项目结构约束：
- 页面在：static/src/pages
- 组件在：static/src/components
- API 调用在：static/src/services/api.ts
- 类型定义在：static/src/types/index.ts
- 请严格按照这个结构输出

我的目标：
1. 在 Solve 页面底部的 Visualization 区域增加更强的 3D 交互能力
2. 对 3D PDE（heat3d / wave3d / poisson3d）做更直观、更高级的展示
3. 支持：
   - 鼠标拖拽旋转
   - 滚轮缩放
   - hover 提示
   - 视角重置
   - x / y / z 切片切换
   - 切片位置滑块
4. 对 2D PDE 保持热力图或 contour 风格，但可以增加更有趣的动态切换
5. 对 1D PDE 保持折线图，不要为了炫技强行 3D 化
6. 在其它页面加入一个可复用的“二次元互动助手”前端组件
7. 这个角色可以出现在 Home / Solve / Results / Finance 等页面边角或底部，不遮挡核心信息
8. 角色要有轻量互动反馈，例如：
   - 微笑
   - 眨眼
   - 头发轻微被风吹动
   - 鼠标靠近时看向鼠标方向
   - hover / 点击时轻微表情变化
   - 害羞 / 脸红 / 生气等状态切换
9. 角色必须“有趣、灵动”，但不能喧宾夺主，不要挡住表单和图表

我要的审美方向：
- 我就是想要更“好看、有趣、动态感强”
- 可以加入粒子效果、流动感、轻微场景氛围
- 但仍然要像科研可视化 / 数值分析平台，而不是游戏界面
- 不要做过度花哨、影响阅读和性能的特效
- 允许加入：
  - 轻粒子背景
  - hover 粒子响应
  - 3D 点云 / 粒子层叠
  - 细微发光
  - 切片切换动画
  - 视角过渡动画
- 但核心仍然是“让 PDE 数值结果更直观”
- 对页面角色部分，希望是“二次元原创助手 / 看板娘”风格，不要直接使用现成版权角色
- 角色风格要偏日系、清爽、科技感或研究助手感，而不是纯恋爱游戏界面

业务要求：
- 对不同 PDE 类型自动选择合适展示：
  - 1D：line chart
  - 2D：heatmap / contour
  - 3D：interactive 3D viewer / particle-enhanced slice explorer / surface-like view
- 如果后端只提供三维切片和数组，不要假设有真正体渲染数据
- 可以设计一个高质量的 3D slice viewer，把切片、点云、粒子层结合起来
- 必须兼容我当前已有的数据结构
- 不要要求后端新增接口
- 页面角色部分请设计成“可复用组件”，而不是每个页面各写一套
- 如果没有立绘素材，请先给我一个可运行的前端组件方案：
  - 可以用 SVG / CSS / Canvas / pseudo-live2d 风格实现
  - 或者预留 asset 插槽，让我后续替换立绘资源
- 角色组件至少要支持这些状态：
  - idle
  - happy
  - shy
  - angry
  - thinking
- 角色交互要与页面有一点联系，例如：
  - Solve 页：更偏“讲解助手”
  - Results 页：根据结果状态切换表情
  - Finance 页：更活泼一些

技术要求：
- 优先复用现有组件和现有接口
- 如果要新增组件，请放在 static/src/components
- 可以新增如：
  - static/src/components/PDE3DViewer.tsx
  - static/src/components/ParticleField.tsx
  - static/src/components/InteractiveSliceViewer.tsx
  - static/src/components/AnimeAssistant.tsx
  - static/src/components/AssistantBubble.tsx
  - static/src/components/AssistantScene.tsx
- 如果你需要新增依赖，请明确说明：
  - 为什么要加
  - 安装命令
  - 替代方案
- 我更倾向于轻量方案，但如果做 3D 交互必须用成熟库，也可以提议
- 所有异步区域都要有 loading / empty / error 状态
- TypeScript 类型要清晰
- 如果角色组件需要简单动画库，也请尽量轻量；能用 CSS / SVG / framer-motion 解决就不要引入重库
- 请明确区分：
  - Solve 页面底部 3D 可视化增强
  - 全站可复用的二次元角色互动系统

请按以下顺序输出：
1. 你准备修改/新增的文件列表
2. 每个文件修改目的
3. 新增组件结构说明
4. 先输出 Solve 页面 3D 可视化增强代码
5. 再输出二次元互动角色系统代码
6. 如果需要新增依赖，请单独列出
7. 如果太长，优先先输出第一阶段可运行版本

请特别注意：
- 我不是要你重写整个 Solve 页面
- 我只要你增强底部 Visualization 区域
- 输出必须贴近我现有项目，不要理想化 demo
- 我之后会把你的代码带回现有项目整合，所以要可落地
- 我希望最终效果更有“粒子感、流动感、交互感”，但仍然专业可读
- 我也希望页面角色是“可爱、会动、有情绪反馈”的，但不能破坏专业感
- 不要生成依赖复杂美术管线才能运行的方案
- 如果你使用占位立绘，请确保之后我能方便替换成自己的资源

下面是我当前项目关键文件，请严格基于它们修改。

---

## File: static/src/pages/SolvePage.tsx

```tsx
import type { ReactNode } from 'react';
import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { Activity, BarChart3, Play, Settings, TrendingUp, Zap } from 'lucide-react';
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
    } catch (recommendError) {
      setError(recommendError instanceof Error ? recommendError.message : 'Algorithm recommendation failed');
    } finally {
      setRecommending(false);
    }
  };

  const handleSolve = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.solve({
        ...params,
        return_full_solution: params.return_full_solution || isThreeDimensional,
      });
      setResult(response);
    } catch (solveError) {
      setError(solveError instanceof Error ? solveError.message : 'Solve failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">PDE Solver <span className="text-lg font-medium text-gray-500">鍋忓井鍒嗘柟绋嬫眰瑙ｇ晫闈?/span></h1>
        <p className="text-gray-600">
          Configure PDE parameters manually, choose a selection strategy, and run 1D/2D/3D heat, 1D/2D/3D wave,
          1D/3D Poisson, and 2D nonlinear Poisson demos.
        </p>
        <p className="mt-2 text-sm text-gray-500">涓枃璇存槑锛氬乏渚у～鍐欏弬鏁帮紝鍙充晶鏌ョ湅鎺ㄨ崘绠楁硶銆佽宸寚鏍囧拰缁撴灉鍥惧儚锛涗笁缁撮棶棰樻敮鎸佸垏鐗囨煡鐪嬨€?/p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <Settings className="h-5 w-5" />
              Solve Parameters
            </h2>
            <p className="text-sm text-gray-500">涓枃璇存槑锛氬厛閫夋柟绋嬶紝鍐嶉€夌畻娉曪紱濡傛灉涓嶇‘瀹氱畻娉曪紝鍙厛鐐光€淩ecommend Algorithm鈥濊幏鍙栨帹鑽愩€?/p>

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

            {equationNote && <div className="rounded-md bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-500">鏂圭▼璇存槑锛歿equationNote}</div>}

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

            <div className="text-xs text-gray-500">Recommended strategy: {STRATEGY_LABELS[recommendedStrategy]}銆備腑鏂囨彁绀猴細杩欐槸褰撳墠鏂圭▼杈冮€傚悎浼樺厛灏濊瘯鐨勯€夋嫨绛栫暐銆?/div>

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
                <div className="mt-1 text-xs text-blue-600">涓枃鎻愮ず锛氭帹鑽愮粨鏋滄潵鑷壒寰佹彁鍙栧拰绠楁硶閫夋嫨妯″潡锛岃€屼笉鏄墜宸ュ啓姝汇€?/div>
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
            <p className="text-xs text-gray-500">涓枃璇存槑锛氱偣鍑诲悗浼氳皟鐢ㄥ悗绔眰瑙ｆ帴鍙ｏ紱涓夌淮鏂圭▼浼氳嚜鍔ㄨ姹傚畬鏁寸粨鏋滀互鏀寔鎴潰鐑姏鍥俱€?/p>
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
                <p className="mb-4 text-sm text-gray-500">涓枃璇存槑锛氳繖閲岀粺璁″綋鍓嶆眰瑙ｇ粨鏋滅殑鏈€灏忓€笺€佹渶澶у€笺€佸潎鍊煎拰鏍囧噯宸紝鐢ㄦ潵蹇€熷垽鏂暟鍊艰妯°€?/p>
                <StatsChart stats={preview?.stats} />
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <TrendingUp className="h-5 w-5" />
                  Visualization
                </h2>
                <p className="mb-4 text-sm text-gray-500">涓枃璇存槑锛氫竴缁存樉绀烘姌绾垮浘锛屼簩缁存樉绀虹儹鍔涘浘锛屼笁缁存樉绀哄垏鐗囩儹鍔涘浘銆?/p>

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
                    <div className="mt-2 text-xs text-gray-500">涓枃鎻愮ず锛氬垏鎹?`x / y / z` 鏂瑰悜鍙互鏌ョ湅涓夌淮瑙ｅ湪涓嶅悓鎴潰涓婄殑鍒嗗竷鎯呭喌銆?/div>
                  </div>
                )}

                {isHeatmap2d ? (
                  <Suspense fallback={<div className="text-sm text-gray-500">Loading heatmap...</div>}>
                    <Heatmap solution={chartData} nx={params.nx || 41} ny={params.ny || 41} title={`${equationTitle} Heatmap`} />
                  </Suspense>
                ) : isThreeDimensional && sliceView ? (
                  <Suspense fallback={<div className="text-sm text-gray-500">Loading heatmap...</div>}>
                    <Heatmap solution={sliceView.values} nx={sliceView.nx} ny={sliceView.ny} title={`${equationTitle} 3D Slice`} />
                  </Suspense>
                ) : (
                  <SolutionChart solution={chartData} title={isThreeDimensional ? `${equationTitle} Slice Preview` : `${equationTitle} Solution`} />
                )}
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold">
                  <Zap className="h-5 w-5" />
                  Solution Preview
                </h2>
                <p className="mb-4 text-sm text-gray-500">涓枃璇存槑锛氳繖閲屽彧鏄剧ず缁撴灉鏁扮粍鍓嶅悗鑻ュ共椤癸紝閫傚悎蹇€熺‘璁よ竟鐣屽€煎拰鏁翠綋瓒嬪娍銆?/p>
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

```

---

## File: static/src/components/Heatmap.tsx

```tsx
import Plot from 'react-plotly.js';

interface HeatmapProps {
  solution: number[];
  nx: number;
  ny: number;
  title?: string;
}

export default function Heatmap({ solution, nx, ny, title = 'Heatmap' }: HeatmapProps) {
  const z = [];
  for (let i = 0; i < ny; i += 1) {
    z.push(solution.slice(i * nx, (i + 1) * nx));
  }

  return (
    <div className="w-full">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <Plot
        data={[
          {
            z,
            type: 'heatmap',
            colorscale: 'Viridis',
          },
        ]}
        layout={{
          title,
          xaxis: { title: 'x' },
          yaxis: { title: 'y' },
          margin: { l: 60, r: 20, b: 50, t: 60 },
          autosize: true,
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
        }}
        style={{ width: '100%', height: '500px' }}
        useResizeHandler
      />
    </div>
  );
}

```

---

## File: static/src/components/SolutionChart.tsx

```tsx
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface SolutionChartProps {
  solution: number[];
  title?: string;
  color?: string;
}

export default function SolutionChart({ solution, title = 'Solution', color = '#2563eb' }: SolutionChartProps) {
  const data = solution.map((value, index) => ({
    x: index,
    y: value,
  }));

  return (
    <div className="w-full">
      <h3 className="mb-4 text-lg font-semibold">{title}</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" label={{ value: 'Grid index', position: 'insideBottom', offset: -5 }} />
          <YAxis label={{ value: 'Value', angle: -90, position: 'insideLeft' }} />
          <Tooltip formatter={(value: number) => value.toFixed(6)} labelFormatter={(label: number) => `Index: ${label}`} />
          <Legend />
          <Line type="monotone" dataKey="y" stroke={color} dot={false} name="Numerical solution" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

```

---

## File: static/src/services/api.ts

```ts
import type {
  SolveRequest,
  SolveResponse,
  FeatureExtractionRequest,
  FeatureExtractionResponse,
  AlgorithmSelectionRequest,
  AlgorithmSelectionResponse,
  LLMConfig,
  LLMQuota,
  BenchmarkResponse,
  SupportedEquationsResponse,
  StockSimulationRequest,
  StockSimulationResponse,
  BlackScholes1DRequest,
  BlackScholes1DResponse,
  BlackScholes2DRequest,
  BlackScholes2DResponse,
  MarketStockResponse,
  MarketPairResponse,
  AShareStockResponse,
  ASharePairResponse,
  AShareETFOptionRequest,
  AShareETFOptionResponse,
  AShareIndexOptionRequest,
  AShareIndexOptionResponse,
  OptionCompareMarketRequest,
  OptionCompareMarketResponse,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function buildApiUrl(endpoint: string): string {
  if (!API_BASE_URL) {
    return endpoint;
  }
  return `${API_BASE_URL}${endpoint}`;
}

function extractErrorMessage(payload: unknown, status: number): string {
  if (typeof payload === 'string' && payload.trim()) {
    return payload;
  }

  if (payload && typeof payload === 'object') {
    const record = payload as Record<string, unknown>;
    const directMessage = record.message;
    if (typeof directMessage === 'string' && directMessage.trim()) {
      return directMessage;
    }

    if (directMessage && typeof directMessage === 'object') {
      const nestedMessage = directMessage as Record<string, unknown>;
      const nestedError = nestedMessage.error;
      if (nestedError && typeof nestedError === 'object') {
        const errorRecord = nestedError as Record<string, unknown>;
        if (typeof errorRecord.message === 'string' && errorRecord.message.trim()) {
          return errorRecord.message;
        }
      }
      if (typeof nestedMessage.message === 'string' && nestedMessage.message.trim()) {
        return nestedMessage.message;
      }
    }

    const detail = record.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (detail && typeof detail === 'object') {
      return extractErrorMessage(detail, status);
    }
  }

  return `HTTP ${status}`;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = buildApiUrl(endpoint);
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed.' }));
    throw new Error(extractErrorMessage(error, response.status));
  }

  return response.json();
}

export const api = {
  solve: async (data: SolveRequest): Promise<SolveResponse> => {
    return request<SolveResponse>('/solve_equation', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  extractFeature: async (data: FeatureExtractionRequest): Promise<FeatureExtractionResponse> => {
    return request<FeatureExtractionResponse>('/extract_feature', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  selectAlgorithm: async (data: AlgorithmSelectionRequest): Promise<AlgorithmSelectionResponse> => {
    return request<AlgorithmSelectionResponse>('/select_algorithm', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  autoSolve: async (question: string, model: string = 'doubao', returnFull: boolean = false): Promise<any> => {
    return request('/api/auto_solve', {
      method: 'POST',
      body: JSON.stringify({ 
        question, 
        parser_model: model,
        return_full_solution: returnFull 
      }),
    });
  },

  parseQuestion: async (question: string, model: string = 'doubao'): Promise<any> => {
    return request('/api/parse_question', {
      method: 'POST',
      body: JSON.stringify({ 
        question, 
        model_name: model 
      }),
    });
  },

  llm: {
    getConfig: async (): Promise<{ code: number; data: Record<string, LLMConfig> }> => {
      return request('/llm/config/get');
    },

    saveConfig: async (config: LLMConfig): Promise<{ code: number; message: string }> => {
      return request('/llm/config/save', {
        method: 'POST',
        body: JSON.stringify(config),
      });
    },

    testConfig: async (config: LLMConfig): Promise<{ code: number; message: string }> => {
      console.log('testConfig - 鍙戦€佺殑 config 瀵硅薄:', JSON.stringify(config, null, 2));
      return request('/llm/config/test', {
        method: 'POST',
        body: JSON.stringify(config),
      });
    },

    getQuota: async (): Promise<{ code: number; data: LLMQuota[] }> => {
      return request('/llm/quota/get');
    },
  },

  health: async (): Promise<{ status: string }> => {
    return request('/health');
  },

  getSupportedEquations: async (): Promise<SupportedEquationsResponse> => {
    return request('/supported_equations');
  },

  getLatestBenchmark: async (): Promise<BenchmarkResponse> => {
    return request('/benchmark/latest');
  },

  finance: {
    simulateStocks: async (data: StockSimulationRequest): Promise<StockSimulationResponse> => {
      return request('/finance/stocks/simulate', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    priceBlackScholes1D: async (data: BlackScholes1DRequest): Promise<BlackScholes1DResponse> => {
      return request('/finance/options/black_scholes_1d', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    priceBlackScholes2D: async (data: BlackScholes2DRequest): Promise<BlackScholes2DResponse> => {
      return request('/finance/options/black_scholes_2d', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    getStockMarketData: async (symbol: string, lookbackDays: number = 252): Promise<MarketStockResponse> => {
      return request(`/finance/market/stock/${encodeURIComponent(symbol)}?lookback_days=${lookbackDays}`);
    },

    getAshareStockData: async (
      symbol: string,
      lookbackDays: number = 252,
      forceHistoryOnly: boolean = false,
    ): Promise<AShareStockResponse> => {
      return request(
        `/finance/ashare/stock/${encodeURIComponent(symbol)}?lookback_days=${lookbackDays}&force_history_only=${forceHistoryOnly ? 'true' : 'false'}`,
      );
    },

    getAsharePairData: async (symbol1: string, symbol2: string, lookbackDays: number = 252): Promise<ASharePairResponse> => {
      return request(
        `/finance/ashare/pair?symbol1=${encodeURIComponent(symbol1)}&symbol2=${encodeURIComponent(symbol2)}&lookback_days=${lookbackDays}`,
      );
    },

    getAshareEtfOptionData: async (data: AShareETFOptionRequest): Promise<AShareETFOptionResponse> => {
      return request('/finance/ashare/etf_option', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    getAshareIndexOptionData: async (data: AShareIndexOptionRequest): Promise<AShareIndexOptionResponse> => {
      return request('/finance/ashare/index_option', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    getPairMarketData: async (symbol1: string, symbol2: string, lookbackDays: number = 252): Promise<MarketPairResponse> => {
      return request(
        `/finance/market/pair?symbol1=${encodeURIComponent(symbol1)}&symbol2=${encodeURIComponent(symbol2)}&lookback_days=${lookbackDays}`,
      );
    },

    compareOptionWithMarket: async (data: OptionCompareMarketRequest): Promise<OptionCompareMarketResponse> => {
      return request('/finance/options/compare_market', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },
};

```

---

## File: static/src/types/index.ts

```ts
export interface SolveRequest {
  equation_type: 'heat1d' | 'heat2d' | 'heat3d' | 'wave1d' | 'wave2d' | 'wave3d' | 'poisson1d' | 'poisson3d' | 'poisson2d_nonlinear';
  accuracy: 'high' | 'medium' | 'low';
  realtime: 'high' | 'medium' | 'low';
  resource_budget: number;
  boundary_condition: 'dirichlet' | 'neumann' | 'mixed';
  nx?: number;
  ny?: number;
  nz?: number;
  k?: number;
  c?: number;
  L?: number;
  Lx?: number;
  Ly?: number;
  Lz?: number;
  t0?: number;
  t1?: number;
  nt?: number;
  left_bc?: number;
  right_bc?: number;
  initial_velocity?: number;
  algorithm_key?: 'fdm' | 'fvm' | 'fem' | 'spectral' | 'pinn' | 'bem';
  return_full_solution?: boolean;
}

export interface SolveResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    equation_type?: string;
    recommended_algorithm?: string;
    executed_algorithm?: string;
    solve_info: {
      algorithm: string;
      elapsed_s: number;
      nfev: number;
      status: string;
      estimated_error?: number;
      l2_error?: number;
      linf_error?: number;
      boundary_residual?: number;
      resource_proxy?: number;
      details?: {
        training_summary?: {
          cache_hit?: boolean;
          cache_origin?: string;
          adam_epochs_run?: number;
          adam_epochs_configured?: number;
          cached_adam_epochs_run?: number;
          lbfgs_steps_run?: number;
          lbfgs_steps_configured?: number;
          cached_lbfgs_steps_run?: number;
          best_loss?: number;
          early_stopped?: boolean;
        };
      };
    };
    validation?: any;
    solution_preview: {
      count: number;
      head: number[];
      tail: number[];
      stats: {
        min: number;
        max: number;
        mean: number;
        std: number;
      };
    };
    solution?: number[];
  };
}

export interface FeatureExtractionRequest {
  equation_type: 'heat1d' | 'heat2d' | 'heat3d' | 'wave1d' | 'wave2d' | 'wave3d' | 'poisson1d' | 'poisson3d' | 'poisson2d_nonlinear';
  accuracy: 'high' | 'medium' | 'low';
  realtime: 'high' | 'medium' | 'low';
  resource_budget: number;
  boundary_condition: 'dirichlet' | 'neumann' | 'mixed';
  nx?: number;
  ny?: number;
  nz?: number;
}

export interface FeatureExtractionResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    equation_type: string;
    physics: number[];
    hardware: number[];
    domain: number[];
    x13: number[];
    hardware_extra: {
      gpu_name?: string;
    };
  };
}

export interface AlgorithmSelectionRequest {
  strategy: 'static_rf' | 'static_xgb' | 'dynamic_rl' | 'mlp_nn' | 'gnn_selector';
  physics: number[];
  hardware: number[];
  domain: number[];
}

export interface AlgorithmSelectionResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    algorithm_key: string;
    algorithm_name?: string;
    selected_algorithm: string;
    algorithm_scores: {
      accuracy: number;
      convergence: number;
      resource: number;
      total: number;
    };
    score?: {
      accuracy: number;
      convergence: number;
      resource: number;
      total: number;
    };
    rationale: string;
    reason?: string;
  };
}

export interface LLMConfig {
  model_name: string;
  api_key: string;
  base_url?: string;
  model_id?: string;  // 鐏北鏂硅垷妯″瀷鍚嶇О锛屼緥濡傦細doubao-seed-1-8-251228
}

export interface LLMQuota {
  model_name: string;
  provider: string;
  total_quota: number;
  remaining_quota: number;
  status: string;
  update_time: string;
  message: string;
}

export interface SupportedEquationInfo {
  name: string;
  algorithms: string[];
  strategies: string[];
  note: string;
}

export interface SupportedEquationsResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    equations: Record<string, SupportedEquationInfo>;
  };
}

export interface SelectorBenchmark {
  strategy: string;
  accuracy: number;
  num_test_samples: number;
  details: Record<string, any>;
}

export interface SolverBenchmark {
  equation_type: string;
  algorithm: string;
  l2_error: number;
  linf_error: number;
  elapsed_s: number;
  solver_status: string;
  details?: Record<string, any>;
}

export interface SolverSweepRun {
  nx: number;
  ny?: number;
  nz?: number;
  nt?: number;
  l2_error: number;
  elapsed_s: number;
}

export interface SolverSweepSummary {
  runs: SolverSweepRun[];
  mean_l2_error: number;
  max_l2_error: number;
  mean_elapsed_s: number;
}

export interface BenchmarkReport {
  generated_at: number;
  selector_accuracy: SelectorBenchmark[];
  solver_accuracy: SolverBenchmark[];
  solver_sweeps?: Record<string, Record<string, SolverSweepSummary>>;
  recommendation_examples: Record<
    string,
    Record<
      string,
      {
        algorithm_key: string;
        score_total: number;
        reason: string;
      }
    >
  >;
  notes: string[];
}

export interface BenchmarkResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    report: BenchmarkReport;
    path: string;
  };
}

export interface StockSimulationRequest {
  initial_price: number;
  drift: number;
  volatility: number;
  horizon: number;
  steps: number;
  paths: number;
}

export interface StockSimulationResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    inputs: StockSimulationRequest;
    sample_path_data: Array<Record<string, number | string>>;
    terminal_histogram: Array<{ bin: string; count: number }>;
    summary: {
      min: number;
      max: number;
      mean: number;
      std: number;
      p05: number;
      median: number;
      p95: number;
    };
  };
}

export interface BlackScholes1DRequest {
  spot: number;
  strike: number;
  maturity: number;
  volatility: number;
  rate: number;
}

export interface BlackScholes1DResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    inputs: BlackScholes1DRequest;
    curve: Array<{
      spot: number;
      callPrice: number;
      putPrice: number;
      callPayoff: number;
      putPayoff: number;
    }>;
    summary: {
      callAtSpot: number;
      putAtSpot: number;
      intrinsicCall: number;
      intrinsicPut: number;
      timeValueCall: number;
      timeValuePut: number;
      greeks: {
        call: {
          delta: number;
          gamma: number;
          theta: number;
          vega: number;
          rho: number;
        };
        put: {
          delta: number;
          gamma: number;
          theta: number;
          vega: number;
          rho: number;
        };
      };
    };
  };
}

export interface BlackScholes2DRequest {
  spot1: number;
  spot2: number;
  strike: number;
  maturity: number;
  volatility1: number;
  volatility2: number;
  rate: number;
  correlation: number;
  grid_size: number;
}

export interface BlackScholes2DResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    inputs: BlackScholes2DRequest;
    surface: number[];
    x_values: number[];
    y_values: number[];
    summary: {
      effectiveVolatility: number;
      basketSpot: number;
      callAtCurrentPair: number;
      surfaceMin: number;
      surfaceMax: number;
    };
  };
}

export interface MarketStockResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    symbol: string;
    spot: number;
    historical_volatility: number;
    drift: number;
    risk_free_rate: number;
    history_preview: Array<{ date: string; close: number }>;
    data_source: string;
  };
}

export interface MarketPairResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    symbol1: string;
    symbol2: string;
    spot1: number;
    spot2: number;
    historical_volatility1: number;
    historical_volatility2: number;
    correlation: number;
    data_source: string;
  };
}

export interface AShareStockResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    symbol: string;
    raw_symbol: string;
    name: string;
    latest_price: number;
    latest_close: number;
    open: number | null;
    high: number | null;
    low: number | null;
    prev_close: number | null;
    average_price: number | null;
    change_percent: number | null;
    change_amount: number | null;
    volume: number | null;
    amount: number | null;
    quote_timestamp: string | null;
    latest_trade_date: string;
    market_clock: {
      timezone: string;
      local_time: string;
      is_trading_day: boolean;
      market_open: boolean;
      phase: string;
      phase_label: string;
    };
    volatility: {
      hv20: number | null;
      hv60: number | null;
      hv252: number | null;
    };
    annualized_drift: number;
    history_preview: Array<{ date: string; close: number }>;
    data_source: string;
    realtime_available?: boolean;
    notes: string[];
  };
}

export interface ASharePairResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    symbol1: string;
    symbol2: string;
    name1: string;
    name2: string;
    latest_price1: number;
    latest_price2: number;
    correlation: number;
    hv252_1: number | null;
    hv252_2: number | null;
    pair_history: Array<{ date: string; close1: number; close2: number }>;
    rolling_correlation: Array<{ date: string; correlation: number }>;
    data_source: string;
  };
}

export interface AShareETFOptionRequest {
  underlying: string;
  option_type: 'call' | 'put';
  expiry?: string;
  strike?: number;
  contract_code?: string;
}

export interface AShareETFOptionResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    underlying: string;
    available_expiries: string[];
    available_strikes: number[];
    underlying_name: string;
    underlying_price: number;
    underlying_prev_close: number;
    underlying_open: number;
    underlying_high: number;
    underlying_low: number;
    underlying_quote_time: string;
    option_type: string;
    contract_code: string;
    trading_code: string;
    contract_name: string;
    expiry: string;
    strike: number;
    latest_price: number;
    bid: number;
    ask: number;
    midpoint: number;
    change_percent: number;
    open_interest: number;
    volume: number;
    quote_time: string;
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    implied_volatility: number;
    theoretical_value: number;
    pricing_gap: number;
    moneyness: number;
    data_source: string;
    notes: string[];
  };
}

export interface AShareIndexOptionRequest {
  market: string;
  option_type: 'call' | 'put';
  contract_month?: string;
  strike?: number;
}

export interface AShareIndexOptionResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    market: string;
    market_name: string;
    available_months: string[];
    available_strikes: number[];
    contract_month: string;
    option_type: string;
    contract_code: string;
    strike: number;
    latest_price: number;
    bid: number;
    ask: number;
    midpoint: number;
    open_interest: number;
    change_amount: number;
    data_source: string;
    notes: string[];
  };
}

export interface OptionCompareMarketRequest {
  symbol: string;
  expiry?: string;
  strike?: number;
  option_type: 'call' | 'put';
  maturity_years?: number;
  use_market_iv?: boolean;
}

export interface OptionCompareMarketResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    symbol: string;
    spot: number;
    expiry: string;
    strike: number;
    option_type: string;
    market_price: number;
    model_price: number;
    implied_volatility: number;
    risk_free_rate: number;
    pricing_gap: number;
    contract_symbol: string;
    notes: string[];
  };
}

```
