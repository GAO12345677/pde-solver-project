# Gemini Finance Frontend Handoff

下面内容可直接复制给 Gemini。建议先发送“Prompt”部分，再依次发送三个文件代码块。

## Prompt

我有一个现成项目，需要你只帮我做前端页面和前端交互优化，不要重建项目，不要改后端接口定义。

项目背景：
- 项目名称：PDE 智能求解与金融分析平台
- 后端：FastAPI
- 前端：React + TypeScript + Vite
- 现有页面包括：Home / Parse / Solve / Results / Finance / LLM Config
- 我现在最想优化的是 Finance 页面，也可以顺带优化 Solve / Results 的视觉表现
- 这个项目不是营销官网，而是一个“数值分析 + 金融实践 + 教学展示”系统

你的任务边界：
- 只做前端
- 不要重建新项目
- 不要输出 Next.js / Vue / Svelte 版本
- 不要假设不存在的后端接口
- 不要擅自修改 API 字段名
- 不要引入重量级新依赖，除非非常必要
- 输出必须能接入现有 React + TypeScript + Vite 项目
- 优先给我“可直接替换的页面/组件代码”

我当前项目结构约束：
- 页面在：static/src/pages
- 组件在：static/src/components
- API 调用在：static/src/services/api.ts
- 类型定义在：static/src/types/index.ts
- 请严格按照这个结构设计代码

页面风格目标：
- 想要更动态、更直观、更高级
- 但不要花哨，不要像营销站
- 要有工程感、专业感、分析仪表盘感
- 适合桌面端展示，也适合答辩演示
- 文案风格使用：英文主标题 + 中文辅助说明
- 保留我项目的“学习/展示”属性，不要只追求酷炫

重点优化目标：
1. Finance 页面做成更有层次的动态分析面板
2. 指标卡片增加更明显的状态感（loading / success / degraded / error）
3. 图表区域更直观，能体现“数据正在变化”或“当前模式变化”
4. A股股票部分要能明显区分：
   - 实时模式
   - 历史日线模式
   - 数据源失败时的降级状态
5. 期权部分要更像专业分析面板：
   - 价格摘要
   - Greeks
   - market vs model
   - ETF/index options 的信息分区更清晰
6. 可以加入适量动效：
   - 页面区块渐入
   - 卡片数字刷新动画
   - tab 切换动画
   - loading skeleton
   - 状态 badge 过渡
7. 不要加入复杂炫技动画，不要影响读取信息

设计要求：
- 不要使用默认平庸布局
- 要像专业分析平台，而不是普通表单页
- 可以适度使用：
  - 分区卡片
  - sticky summary area
  - section status badges
  - compact tooltip
  - subtle gradient / subtle grid background
- 字体和配色要稳重、清晰、现代，不要紫色审美
- 保持可读性优先

工程要求：
- 所有异步数据区域都要有：loading / empty / error / degraded/fallback 状态
- 不要把后端错误对象直接显示成 [object Object]
- 代码尽量模块化
- 组件命名清楚
- TypeScript 类型尽量明确
- 如果需要新增组件，请放在 static/src/components
- 如果需要新增轻量样式文件，请说明路径
- 如果你建议使用 CSS Modules 或独立 CSS 文件，请保持简单可接入

请按以下顺序输出：
1. 你准备修改/新增的文件列表
2. 每个文件修改目的
3. 然后给出完整可落地代码
4. 如果某些代码依赖我现有文件内容，请明确告诉我应该把哪些现有文件内容再发给你
5. 优先先做 Finance 页面
6. 如果篇幅太长，先完整输出第一阶段：Finance 页面改造

请特别注意：
- 我之后会把你写的代码拿回我现有项目里整合
- 所以你输出的代码必须尽量贴近现有工程，而不是理想化 demo
- 请不要只给设计建议，我要代码
- 下面是我的现有项目关键文件，请严格基于它们修改

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

---

## File: static/src/pages/FinancePage.tsx

```tsx
import { BarChart3, CandlestickChart, CircleDollarSign, Landmark, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api } from '../services/api';
import Heatmap from '../components/Heatmap';

type FinanceTab = 'stocks' | 'options';

interface StockFormState {
  initialPrice: number;
  drift: number;
  volatility: number;
  horizon: number;
  steps: number;
  paths: number;
}

interface OptionFormState {
  spot: number;
  strike: number;
  maturity: number;
  volatility: number;
  rate: number;
}

interface Option2DFormState {
  spot1: number;
  spot2: number;
  strike: number;
  maturity: number;
  volatility1: number;
  volatility2: number;
  rate: number;
  correlation: number;
  gridSize: number;
}

interface SummaryStats {
  min: number;
  max: number;
  mean: number;
  std: number;
  p05: number;
  median: number;
  p95: number;
}

interface StockSimulationResult {
  samplePathData: Array<Record<string, number | string>>;
  terminalHistogram: Array<{ bin: string; count: number }>;
  summary: SummaryStats;
}

interface OptionPoint {
  spot: number;
  callPrice: number;
  putPrice: number;
  callPayoff: number;
  putPayoff: number;
}

interface OptionPricingResult {
  curve: OptionPoint[];
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
}

interface Option2DPricingResult {
  surface: number[];
  xValues: number[];
  yValues: number[];
  summary: {
    effectiveVolatility: number;
    basketSpot: number;
    callAtCurrentPair: number;
    surfaceMin: number;
    surfaceMax: number;
  };
}

interface MarketStockState {
  symbol: string;
  spot: number;
  historicalVolatility: number;
  drift: number;
  riskFreeRate: number;
}

interface MarketCompareFormState {
  symbol: string;
  optionType: 'call' | 'put';
  maturityYears: number;
  useMarketIv: boolean;
}

interface MarketCompareState {
  symbol: string;
  spot: number;
  expiry: string;
  strike: number;
  optionType: string;
  marketPrice: number;
  modelPrice: number;
  impliedVolatility: number;
  riskFreeRate: number;
  pricingGap: number;
  contractSymbol: string;
  notes: string[];
}

interface AShareFormState {
  symbol: string;
  lookbackDays: number;
  forceHistoryOnly: boolean;
}

interface ASharePairFormState {
  symbol1: string;
  symbol2: string;
  lookbackDays: number;
}

interface AShareStockState {
  symbol: string;
  rawSymbol: string;
  name: string;
  latestPrice: number;
  latestClose: number;
  open: number | null;
  high: number | null;
  low: number | null;
  prevClose: number | null;
  averagePrice: number | null;
  changePercent: number | null;
  changeAmount: number | null;
  volume: number | null;
  amount: number | null;
  quoteTimestamp: string | null;
  latestTradeDate: string;
  marketClock: {
    timezone: string;
    localTime: string;
    isTradingDay: boolean;
    marketOpen: boolean;
    phase: string;
    phaseLabel: string;
  };
  volatility: {
    hv20: number | null;
    hv60: number | null;
    hv252: number | null;
  };
  annualizedDrift: number;
  historyPreview: Array<{ date: string; close: number }>;
  dataSource: string;
  realtimeAvailable?: boolean;
  notes: string[];
}

interface ASharePairState {
  symbol1: string;
  symbol2: string;
  name1: string;
  name2: string;
  latestPrice1: number;
  latestPrice2: number;
  correlation: number;
  hv252_1: number | null;
  hv252_2: number | null;
  pairHistory: Array<{ date: string; close1: number; close2: number }>;
  rollingCorrelation: Array<{ date: string; correlation: number }>;
  dataSource: string;
}

interface AShareETFOptionFormState {
  underlying: string;
  optionType: 'call' | 'put';
  expiry: string;
  strike: string;
}

interface AShareETFOptionState {
  underlying: string;
  availableExpiries: string[];
  availableStrikes: number[];
  underlyingName: string;
  underlyingPrice: number;
  underlyingPrevClose: number;
  underlyingOpen: number;
  underlyingHigh: number;
  underlyingLow: number;
  underlyingQuoteTime: string;
  optionType: string;
  contractCode: string;
  tradingCode: string;
  contractName: string;
  expiry: string;
  strike: number;
  latestPrice: number;
  bid: number;
  ask: number;
  midpoint: number;
  changePercent: number;
  openInterest: number;
  volume: number;
  quoteTime: string;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  impliedVolatility: number;
  theoreticalValue: number;
  pricingGap: number;
  moneyness: number;
  dataSource: string;
  notes: string[];
}

interface AShareIndexOptionFormState {
  market: string;
  optionType: 'call' | 'put';
  contractMonth: string;
  strike: string;
}

interface AShareIndexOptionState {
  market: string;
  marketName: string;
  availableMonths: string[];
  availableStrikes: number[];
  contractMonth: string;
  optionType: string;
  contractCode: string;
  strike: number;
  latestPrice: number;
  bid: number;
  ask: number;
  midpoint: number;
  openInterest: number;
  changeAmount: number;
  dataSource: string;
  notes: string[];
}

const DEFAULT_STOCK_FORM: StockFormState = {
  initialPrice: 100,
  drift: 0.08,
  volatility: 0.2,
  horizon: 1,
  steps: 252,
  paths: 2000,
};

const DEFAULT_OPTION_FORM: OptionFormState = {
  spot: 100,
  strike: 105,
  maturity: 0.5,
  volatility: 0.25,
  rate: 0.02,
};

const DEFAULT_OPTION_2D_FORM: Option2DFormState = {
  spot1: 100,
  spot2: 95,
  strike: 100,
  maturity: 0.5,
  volatility1: 0.25,
  volatility2: 0.22,
  rate: 0.02,
  correlation: 0.3,
  gridSize: 16,
};

const DEFAULT_MARKET_COMPARE_FORM: MarketCompareFormState = {
  symbol: 'MSFT',
  optionType: 'call',
  maturityYears: 0.25,
  useMarketIv: true,
};

const DEFAULT_ASHARE_FORM: AShareFormState = {
  symbol: '000001',
  lookbackDays: 252,
  forceHistoryOnly: false,
};

const DEFAULT_ASHARE_PAIR_FORM: ASharePairFormState = {
  symbol1: '000001',
  symbol2: '600519',
  lookbackDays: 252,
};

const DEFAULT_ASHARE_ETF_OPTION_FORM: AShareETFOptionFormState = {
  underlying: '510050',
  optionType: 'call',
  expiry: '',
  strike: '',
};

const DEFAULT_ASHARE_INDEX_OPTION_FORM: AShareIndexOptionFormState = {
  market: 'hs300',
  optionType: 'call',
  contractMonth: '',
  strike: '',
};

const STOCK_INPUTS = [
  {
    key: 'initialPrice',
    label: 'Initial Price 鍒濆浠锋牸',
    note: '鑲＄エ鎴栨寚鏁板湪璧风偣鏃跺埢鐨勪环鏍硷紝涔熸槸鏁存妯℃嫙鐨勮捣濮嬪€笺€?,
  },
  {
    key: 'drift',
    label: 'Drift 婕傜Щ鐜?,
    note: '琛ㄧず浠锋牸闀挎湡骞冲潎澧為暱瓒嬪娍锛屽彲绮楃暐鐞嗚В涓哄钩鍧囧悜涓婂闀跨殑鍊惧悜銆?,
  },
  {
    key: 'volatility',
    label: 'Volatility 娉㈠姩鐜?,
    note: '琛ㄧず浠锋牸涓婁笅璧蜂紡鐨勫己搴︼紝鏄闄╁拰涓嶇‘瀹氭€х殑鏍稿績鏉ユ簮銆?,
  },
  {
    key: 'horizon',
    label: 'Horizon 鏃堕棿鑼冨洿',
    note: '琛ㄧず鍚戞湭鏉ユā鎷熷涔咃紝榛樿 1 浠ｈ〃 1 骞淬€?,
  },
  {
    key: 'steps',
    label: 'Steps 鏃堕棿姝ユ暟',
    note: '鎶婃暣涓椂闂村尯闂村垏鎴愬灏戜釜绂绘暎姝ワ紝姝ユ暟瓒婂锛岃矾寰勮秺骞虫粦銆?,
  },
  {
    key: 'paths',
    label: 'Paths 璺緞鏁?,
    note: '钂欑壒鍗℃礇鏍锋湰鏁帮紝瓒婂ぇ缁熻瓒婄ǔ瀹氾紝浣嗚绠楅噺涔熶細涓婂崌銆?,
  },
] as const;

const OPTION_INPUTS = [
  {
    key: 'spot',
    label: 'Spot Price 鏍囩殑浠锋牸',
    note: '褰撳墠鑲＄エ浠锋牸锛屾槸鏈熸潈瀹氫环鐨勮捣鐐广€?,
  },
  {
    key: 'strike',
    label: 'Strike 琛屾潈浠?,
    note: '绾﹀畾鐨勪拱鍗栦环鏍硷紝鍐冲畾鏈熸潈鏀剁泭鐨勫叧閿槇鍊笺€?,
  },
  {
    key: 'maturity',
    label: 'Maturity 鍒版湡鏃堕棿',
    note: '浠庣幇鍦ㄥ埌鍚堢害鍒版湡杩樺墿澶氫箙锛屽崟浣嶈繖閲屾寜骞村鐞嗐€?,
  },
  {
    key: 'volatility',
    label: 'Volatility 娉㈠姩鐜?,
    note: '鎺у埗鏈潵浠锋牸涓嶇‘瀹氭€х殑寮哄害锛屾槸 Black-Scholes 鐨勫叧閿緭鍏ャ€?,
  },
  {
    key: 'rate',
    label: 'Risk-free Rate 鏃犻闄╁埄鐜?,
    note: '甯哥敤鐨勮创鐜扮巼鍙傛暟锛岀敤鏉ユ妸鏈潵鏀剁泭鎶樼畻鍥炵幇鍦ㄣ€?,
  },
] as const;

const OPTION_2D_INPUTS = [
  { key: 'spot1', label: 'Asset 1 Spot 璧勪骇1浠锋牸', note: '绗竴鍙祫浜у綋鍓嶄环鏍笺€? },
  { key: 'spot2', label: 'Asset 2 Spot 璧勪骇2浠锋牸', note: '绗簩鍙祫浜у綋鍓嶄环鏍笺€? },
  { key: 'strike', label: 'Strike 琛屾潈浠?, note: '浜岀淮绡瓙鏈熸潈杩戜技涓殑鍏卞悓闃堝€笺€? },
  { key: 'maturity', label: 'Maturity 鍒版湡鏃堕棿', note: '浠庣幇鍦ㄥ埌鍚堢害鍒版湡杩樺墿澶氫箙銆? },
  { key: 'volatility1', label: 'Vol 1 璧勪骇1娉㈠姩鐜?, note: '绗竴鍙祫浜х殑娉㈠姩鐜囥€? },
  { key: 'volatility2', label: 'Vol 2 璧勪骇2娉㈠姩鐜?, note: '绗簩鍙祫浜х殑娉㈠姩鐜囥€? },
  { key: 'correlation', label: 'Correlation 鐩稿叧绯绘暟', note: '涓ゅ彧璧勪骇鍚屾定鍚岃穼鐨勮仈鍔ㄥ己寮便€? },
  { key: 'gridSize', label: 'Grid Size 缃戞牸澶у皬', note: '浜岀淮浠锋牸鏇查潰绂绘暎绮惧害銆? },
] as const;

const PATH_COLORS = ['#2563eb', '#16a34a', '#dc2626', '#9333ea', '#ea580c', '#0891b2'];

export default function FinancePage() {
  const [tab, setTab] = useState<FinanceTab>('stocks');
  const [stockForm, setStockForm] = useState<StockFormState>(DEFAULT_STOCK_FORM);
  const [aShareForm, setAShareForm] = useState<AShareFormState>(DEFAULT_ASHARE_FORM);
  const [aSharePairForm, setASharePairForm] = useState<ASharePairFormState>(DEFAULT_ASHARE_PAIR_FORM);
  const [aShareEtfOptionForm, setAShareEtfOptionForm] = useState<AShareETFOptionFormState>(DEFAULT_ASHARE_ETF_OPTION_FORM);
  const [aShareIndexOptionForm, setAShareIndexOptionForm] = useState<AShareIndexOptionFormState>(DEFAULT_ASHARE_INDEX_OPTION_FORM);
  const [optionForm, setOptionForm] = useState<OptionFormState>(DEFAULT_OPTION_FORM);
  const [option2DForm, setOption2DForm] = useState<Option2DFormState>(DEFAULT_OPTION_2D_FORM);
  const [marketCompareForm, setMarketCompareForm] = useState<MarketCompareFormState>(DEFAULT_MARKET_COMPARE_FORM);
  const [stockResult, setStockResult] = useState<StockSimulationResult>(() => simulateStockDynamics(DEFAULT_STOCK_FORM));
  const [optionResult, setOptionResult] = useState<OptionPricingResult>(() => computeOptionPricing(DEFAULT_OPTION_FORM));
  const [option2DResult, setOption2DResult] = useState<Option2DPricingResult>(() => computeOptionPricing2D(DEFAULT_OPTION_2D_FORM));
  const [aShareState, setAShareState] = useState<AShareStockState | null>(null);
  const [aSharePairState, setASharePairState] = useState<ASharePairState | null>(null);
  const [aShareEtfOptionState, setAShareEtfOptionState] = useState<AShareETFOptionState | null>(null);
  const [aShareIndexOptionState, setAShareIndexOptionState] = useState<AShareIndexOptionState | null>(null);
  const [marketStockState, setMarketStockState] = useState<MarketStockState | null>(null);
  const [marketCompareState, setMarketCompareState] = useState<MarketCompareState | null>(null);
  const [aShareLoading, setAShareLoading] = useState(false);
  const [aSharePairLoading, setASharePairLoading] = useState(false);
  const [aShareEtfOptionLoading, setAShareEtfOptionLoading] = useState(false);
  const [aShareIndexOptionLoading, setAShareIndexOptionLoading] = useState(false);
  const [stockLoading, setStockLoading] = useState(false);
  const [optionLoading, setOptionLoading] = useState(false);
  const [option2DLoading, setOption2DLoading] = useState(false);
  const [marketLoading, setMarketLoading] = useState(false);
  const [aShareError, setAShareError] = useState<string | null>(null);
  const [aSharePairError, setASharePairError] = useState<string | null>(null);
  const [aShareEtfOptionError, setAShareEtfOptionError] = useState<string | null>(null);
  const [aShareIndexOptionError, setAShareIndexOptionError] = useState<string | null>(null);
  const [stockError, setStockError] = useState<string | null>(null);
  const [optionError, setOptionError] = useState<string | null>(null);
  const [option2DError, setOption2DError] = useState<string | null>(null);
  const [marketError, setMarketError] = useState<string | null>(null);

  const summary = useMemo(() => {
    if (tab === 'stocks') {
      return {
        title: 'Stocks 鑲＄エ婕斿寲',
        subtitle: '鍏堜粠鑲＄エ浠锋牸璺緞鍜岀粓鐐瑰垎甯冨叆鎵嬶紝鏇磋创杩戦殢鏈鸿繃绋嬪拰鎵╂暎鐨勭洿瑙夈€?,
      };
    }

    return {
      title: 'Options 鏈熸潈瀹氫环',
      subtitle: '鎶婇噾铻?PDE 搴旂敤鎵╁睍鍒?Black-Scholes 1D锛屽苟鐢ㄥ浘琛ㄨВ閲婁环鏍煎拰鏀剁泭銆?,
    };
  }, [tab]);

  const handleStockInput = (key: keyof StockFormState, value: string) => {
    const numericValue = Number(value);
    setStockForm((current) => ({
      ...current,
      [key]: Number.isFinite(numericValue) ? numericValue : current[key],
    }));
  };

  const handleAShareInput = (key: keyof AShareFormState, value: string | boolean) => {
    setAShareForm((current) => ({
      ...current,
      [key]:
        key === 'symbol'
          ? String(value).toUpperCase()
          : key === 'forceHistoryOnly'
            ? Boolean(value)
            : Number(value),
    }));
  };

  const handleASharePairInput = (key: keyof ASharePairFormState, value: string) => {
    setASharePairForm((current) => ({
      ...current,
      [key]: key === 'symbol1' || key === 'symbol2' ? value.toUpperCase() : Number(value),
    }));
  };

  const handleAShareEtfOptionInput = (key: keyof AShareETFOptionFormState, value: string) => {
    setAShareEtfOptionForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleAShareIndexOptionInput = (key: keyof AShareIndexOptionFormState, value: string) => {
    setAShareIndexOptionForm((current) => ({
      ...current,
      [key]: value,
    }));
  };

  const handleOptionInput = (key: keyof OptionFormState, value: string) => {
    const numericValue = Number(value);
    setOptionForm((current) => ({
      ...current,
      [key]: Number.isFinite(numericValue) ? numericValue : current[key],
    }));
  };

  const handleOption2DInput = (key: keyof Option2DFormState, value: string) => {
    const numericValue = Number(value);
    setOption2DForm((current) => ({
      ...current,
      [key]: Number.isFinite(numericValue) ? numericValue : current[key],
    }));
  };

  const handleMarketCompareInput = (key: keyof MarketCompareFormState, value: string | boolean) => {
    setMarketCompareForm((current) => ({
      ...current,
      [key]: typeof value === 'boolean' ? value : key === 'symbol' || key === 'optionType' ? value : Number(value),
    }));
  };

  const handleRunStockSimulation = async () => {
    setStockLoading(true);
    setStockError(null);
    try {
      const response = await api.finance.simulateStocks({
        initial_price: stockForm.initialPrice,
        drift: stockForm.drift,
        volatility: stockForm.volatility,
        horizon: stockForm.horizon,
        steps: stockForm.steps,
        paths: stockForm.paths,
      });
      setStockResult({
        samplePathData: response.data.sample_path_data,
        terminalHistogram: response.data.terminal_histogram,
        summary: response.data.summary,
      });
    } catch (error) {
      setStockError(error instanceof Error ? error.message : 'Failed to simulate stocks.');
      setStockResult(simulateStockDynamics(stockForm));
    } finally {
      setStockLoading(false);
    }
  };

  const handleRunAShareAnalysis = async () => {
    setAShareLoading(true);
    setAShareError(null);
    try {
      const response = await api.finance.getAshareStockData(aShareForm.symbol, aShareForm.lookbackDays, aShareForm.forceHistoryOnly);
      setAShareState({
        symbol: response.data.symbol,
        rawSymbol: response.data.raw_symbol,
        name: response.data.name,
        latestPrice: response.data.latest_price,
        latestClose: response.data.latest_close,
        open: response.data.open,
        high: response.data.high,
        low: response.data.low,
        prevClose: response.data.prev_close,
        averagePrice: response.data.average_price,
        changePercent: response.data.change_percent,
        changeAmount: response.data.change_amount,
        volume: response.data.volume,
        amount: response.data.amount,
        quoteTimestamp: response.data.quote_timestamp,
        latestTradeDate: response.data.latest_trade_date,
        marketClock: {
          timezone: response.data.market_clock.timezone,
          localTime: response.data.market_clock.local_time,
          isTradingDay: response.data.market_clock.is_trading_day,
          marketOpen: response.data.market_clock.market_open,
          phase: response.data.market_clock.phase,
          phaseLabel: response.data.market_clock.phase_label,
        },
        volatility: {
          hv20: response.data.volatility.hv20,
          hv60: response.data.volatility.hv60,
          hv252: response.data.volatility.hv252,
        },
        annualizedDrift: response.data.annualized_drift,
        historyPreview: response.data.history_preview,
        dataSource: response.data.data_source,
        realtimeAvailable: response.data.realtime_available,
        notes: response.data.notes,
      });
    } catch (error) {
      setAShareError(error instanceof Error ? error.message : 'Failed to load A-share analysis.');
    } finally {
      setAShareLoading(false);
    }
  };

  const handleRunASharePairAnalysis = async () => {
    setASharePairLoading(true);
    setASharePairError(null);
    try {
      const response = await api.finance.getAsharePairData(aSharePairForm.symbol1, aSharePairForm.symbol2, aSharePairForm.lookbackDays);
      setASharePairState({
        symbol1: response.data.symbol1,
        symbol2: response.data.symbol2,
        name1: response.data.name1,
        name2: response.data.name2,
        latestPrice1: response.data.latest_price1,
        latestPrice2: response.data.latest_price2,
        correlation: response.data.correlation,
        hv252_1: response.data.hv252_1,
        hv252_2: response.data.hv252_2,
        pairHistory: response.data.pair_history,
        rollingCorrelation: response.data.rolling_correlation,
        dataSource: response.data.data_source,
      });
    } catch (error) {
      setASharePairError(error instanceof Error ? error.message : 'Failed to load A-share pair analysis.');
    } finally {
      setASharePairLoading(false);
    }
  };

  const handleRunAShareEtfOption = async () => {
    setAShareEtfOptionLoading(true);
    setAShareEtfOptionError(null);
    try {
      const response = await api.finance.getAshareEtfOptionData({
        underlying: aShareEtfOptionForm.underlying,
        option_type: aShareEtfOptionForm.optionType,
        expiry: aShareEtfOptionForm.expiry || undefined,
        strike: aShareEtfOptionForm.strike ? Number(aShareEtfOptionForm.strike) : undefined,
      });
      setAShareEtfOptionState({
        underlying: response.data.underlying,
        availableExpiries: response.data.available_expiries,
        availableStrikes: response.data.available_strikes,
        underlyingName: response.data.underlying_name,
        underlyingPrice: response.data.underlying_price,
        underlyingPrevClose: response.data.underlying_prev_close,
        underlyingOpen: response.data.underlying_open,
        underlyingHigh: response.data.underlying_high,
        underlyingLow: response.data.underlying_low,
        underlyingQuoteTime: response.data.underlying_quote_time,
        optionType: response.data.option_type,
        contractCode: response.data.contract_code,
        tradingCode: response.data.trading_code,
        contractName: response.data.contract_name,
        expiry: response.data.expiry,
        strike: response.data.strike,
        latestPrice: response.data.latest_price,
        bid: response.data.bid,
        ask: response.data.ask,
        midpoint: response.data.midpoint,
        changePercent: response.data.change_percent,
        openInterest: response.data.open_interest,
        volume: response.data.volume,
        quoteTime: response.data.quote_time,
        delta: response.data.delta,
        gamma: response.data.gamma,
        theta: response.data.theta,
        vega: response.data.vega,
        impliedVolatility: response.data.implied_volatility,
        theoreticalValue: response.data.theoretical_value,
        pricingGap: response.data.pricing_gap,
        moneyness: response.data.moneyness,
        dataSource: response.data.data_source,
        notes: response.data.notes,
      });
      setAShareEtfOptionForm((current) => ({
        ...current,
        expiry: current.expiry || response.data.expiry,
        strike: current.strike || String(response.data.strike),
      }));
    } catch (error) {
      setAShareEtfOptionError(error instanceof Error ? error.message : 'Failed to load ETF option data.');
    } finally {
      setAShareEtfOptionLoading(false);
    }
  };

  const handleRunAShareIndexOption = async () => {
    setAShareIndexOptionLoading(true);
    setAShareIndexOptionError(null);
    try {
      const response = await api.finance.getAshareIndexOptionData({
        market: aShareIndexOptionForm.market,
        option_type: aShareIndexOptionForm.optionType,
        contract_month: aShareIndexOptionForm.contractMonth || undefined,
        strike: aShareIndexOptionForm.strike ? Number(aShareIndexOptionForm.strike) : undefined,
      });
      setAShareIndexOptionState({
        market: response.data.market,
        marketName: response.data.market_name,
        availableMonths: response.data.available_months,
        availableStrikes: response.data.available_strikes,
        contractMonth: response.data.contract_month,
        optionType: response.data.option_type,
        contractCode: response.data.contract_code,
        strike: response.data.strike,
        latestPrice: response.data.latest_price,
        bid: response.data.bid,
        ask: response.data.ask,
        midpoint: response.data.midpoint,
        openInterest: response.data.open_interest,
        changeAmount: response.data.change_amount,
        dataSource: response.data.data_source,
        notes: response.data.notes,
      });
      setAShareIndexOptionForm((current) => ({
        ...current,
        contractMonth: current.contractMonth || response.data.contract_month,
        strike: current.strike || String(response.data.strike),
      }));
    } catch (error) {
      setAShareIndexOptionError(error instanceof Error ? error.message : 'Failed to load index option data.');
    } finally {
      setAShareIndexOptionLoading(false);
    }
  };

  const handleRunOptionPricing = async () => {
    setOptionLoading(true);
    setOptionError(null);
    try {
      const response = await api.finance.priceBlackScholes1D({
        spot: optionForm.spot,
        strike: optionForm.strike,
        maturity: optionForm.maturity,
        volatility: optionForm.volatility,
        rate: optionForm.rate,
      });
      setOptionResult({
        curve: response.data.curve,
        summary: response.data.summary,
      });
    } catch (error) {
      setOptionError(error instanceof Error ? error.message : 'Failed to price the option.');
      setOptionResult(computeOptionPricing(optionForm));
    } finally {
      setOptionLoading(false);
    }
  };

  const handleRunOptionPricing2D = async () => {
    setOption2DLoading(true);
    setOption2DError(null);
    try {
      const response = await api.finance.priceBlackScholes2D({
        spot1: option2DForm.spot1,
        spot2: option2DForm.spot2,
        strike: option2DForm.strike,
        maturity: option2DForm.maturity,
        volatility1: option2DForm.volatility1,
        volatility2: option2DForm.volatility2,
        rate: option2DForm.rate,
        correlation: option2DForm.correlation,
        grid_size: option2DForm.gridSize,
      });
      setOption2DResult({
        surface: response.data.surface,
        xValues: response.data.x_values,
        yValues: response.data.y_values,
        summary: response.data.summary,
      });
    } catch (error) {
      setOption2DError(error instanceof Error ? error.message : 'Failed to price the 2D option.');
      setOption2DResult(computeOptionPricing2D(option2DForm));
    } finally {
      setOption2DLoading(false);
    }
  };

  const handleRunMarketComparison = async () => {
    setMarketLoading(true);
    setMarketError(null);
    try {
      const [stockResponse, compareResponse] = await Promise.all([
        api.finance.getStockMarketData(marketCompareForm.symbol),
        api.finance.compareOptionWithMarket({
          symbol: marketCompareForm.symbol,
          option_type: marketCompareForm.optionType,
          maturity_years: marketCompareForm.maturityYears,
          use_market_iv: marketCompareForm.useMarketIv,
        }),
      ]);
      setMarketStockState({
        symbol: stockResponse.data.symbol,
        spot: stockResponse.data.spot,
        historicalVolatility: stockResponse.data.historical_volatility,
        drift: stockResponse.data.drift,
        riskFreeRate: stockResponse.data.risk_free_rate,
      });
      setMarketCompareState({
        symbol: compareResponse.data.symbol,
        spot: compareResponse.data.spot,
        expiry: compareResponse.data.expiry,
        strike: compareResponse.data.strike,
        optionType: compareResponse.data.option_type,
        marketPrice: compareResponse.data.market_price,
        modelPrice: compareResponse.data.model_price,
        impliedVolatility: compareResponse.data.implied_volatility,
        riskFreeRate: compareResponse.data.risk_free_rate,
        pricingGap: compareResponse.data.pricing_gap,
        contractSymbol: compareResponse.data.contract_symbol,
        notes: compareResponse.data.notes,
      });
    } catch (error) {
      setMarketError(error instanceof Error ? error.message : 'Failed to load market comparison.');
    } finally {
      setMarketLoading(false);
    }
  };

  useEffect(() => {
    void handleRunAShareAnalysis();
    void handleRunASharePairAnalysis();
    void handleRunAShareEtfOption();
    void handleRunAShareIndexOption();
    void handleRunStockSimulation();
    void handleRunOptionPricing();
    void handleRunOptionPricing2D();
    void handleRunMarketComparison();
  }, []);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-4xl">
            <h1 className="text-3xl font-bold text-gray-900">
              Finance Module <span className="text-lg font-medium text-gray-500">閲戣瀺瀹炶返鏉垮潡</span>
            </h1>
            <p className="mt-3 text-gray-600">
              Use finance as an application extension of the PDE platform without replacing the thesis core.
              <span className="block text-sm text-gray-500">
                杩欓噷鎶婇噾铻嶄綔涓哄簲鐢ㄦ渚嬫墿灞曪紝鑰屼笉鏄浛浠ｅ師鏈夌殑 `heat / wave / poisson` 涓荤嚎銆?
              </span>
            </p>
            <p className="mt-3 text-sm text-gray-500">
              涓枃璇存槑锛氬缓璁厛鍋?`Stocks`锛屽洜涓哄畠鏇存帴杩戦殢鏈鸿繃绋嬪拰鎵╂暎鐨勭墿鐞嗙洿瑙夛紱鍐嶅仛 `Options`锛屽洜涓哄畠鏇磋创杩戞爣鍑嗛噾铻?PDE銆?
            </p>
          </div>
          <div className="rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <div className="flex items-center gap-2 font-semibold">
              <Landmark className="h-4 w-4" />
              Module status 妯″潡鐘舵€?
            </div>
            <p className="mt-2">Stocks and Options first versions are both interactive now.</p>
            <p className="mt-1">鑲＄エ鍜屾湡鏉冧袱涓瓙鏉垮潡鐜板湪閮藉凡缁忚繘鍏モ€滃彲杩愯銆佸彲灞曠ず鈥濈殑绗竴鐗堢姸鎬併€?/p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SummaryCard
          icon={<CandlestickChart className="h-5 w-5" />}
          title="Stocks First"
          subtitle="鍏堝仛鑲＄エ婕斿寲"
          description="Build intuition with price paths, terminal distribution, and Monte Carlo statistics."
        />
        <SummaryCard
          icon={<CircleDollarSign className="h-5 w-5" />}
          title="Options Next"
          subtitle="鍐嶅仛鏈熸潈瀹氫环"
          description="Move into Black-Scholes 1D and use price/payoff charts to explain the contract value."
        />
        <SummaryCard
          icon={<BarChart3 className="h-5 w-5" />}
          title="Thesis Safe"
          subtitle="涓嶅亸绂昏鏂囦富绾?
          description="Finance remains a separate application area under the same numerical-analysis framework."
        />
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap gap-3">
          <TabButton active={tab === 'stocks'} onClick={() => setTab('stocks')}>
            Stocks 鑲＄エ婕斿寲
          </TabButton>
          <TabButton active={tab === 'options'} onClick={() => setTab('options')}>
            Options 鏈熸潈瀹氫环
          </TabButton>
        </div>

        <div className="mt-5 rounded-lg border border-blue-100 bg-blue-50 p-4 text-blue-900">
          <p className="font-semibold">{summary.title}</p>
          <p className="mt-2 text-sm">{summary.subtitle}</p>
        </div>

        {tab === 'stocks' ? (
          <StocksPanel
            aShareForm={aShareForm}
            aSharePairForm={aSharePairForm}
            aShareState={aShareState}
            aSharePairState={aSharePairState}
            aShareLoading={aShareLoading}
            aSharePairLoading={aSharePairLoading}
            aShareError={aShareError}
            aSharePairError={aSharePairError}
            form={stockForm}
            result={stockResult}
            loading={stockLoading}
            error={stockError}
            onAShareChange={handleAShareInput}
            onASharePairChange={handleASharePairInput}
            onRunAShare={handleRunAShareAnalysis}
            onRunASharePair={handleRunASharePairAnalysis}
            onChange={handleStockInput}
            onRun={handleRunStockSimulation}
          />
        ) : (
          <OptionsPanel
            form={optionForm}
            result={optionResult}
            option2DForm={option2DForm}
            option2DResult={option2DResult}
            loading={optionLoading}
            error={optionError}
            option2DLoading={option2DLoading}
            option2DError={option2DError}
            marketCompareForm={marketCompareForm}
            marketStockState={marketStockState}
            marketCompareState={marketCompareState}
            aShareEtfOptionForm={aShareEtfOptionForm}
            aShareEtfOptionState={aShareEtfOptionState}
            aShareIndexOptionForm={aShareIndexOptionForm}
            aShareIndexOptionState={aShareIndexOptionState}
            marketLoading={marketLoading}
            marketError={marketError}
            aShareEtfOptionLoading={aShareEtfOptionLoading}
            aShareEtfOptionError={aShareEtfOptionError}
            aShareIndexOptionLoading={aShareIndexOptionLoading}
            aShareIndexOptionError={aShareIndexOptionError}
            onChange={handleOptionInput}
            onRun={handleRunOptionPricing}
            onChange2D={handleOption2DInput}
            onRun2D={handleRunOptionPricing2D}
            onMarketCompareInput={handleMarketCompareInput}
            onRunMarketComparison={handleRunMarketComparison}
            onAShareEtfOptionInput={handleAShareEtfOptionInput}
            onRunAShareEtfOption={handleRunAShareEtfOption}
            onAShareIndexOptionInput={handleAShareIndexOptionInput}
            onRunAShareIndexOption={handleRunAShareIndexOption}
          />
        )}
      </section>
    </div>
  );
}

function StocksPanel({
  aShareForm,
  aSharePairForm,
  aShareState,
  aSharePairState,
  aShareLoading,
  aSharePairLoading,
  aShareError,
  aSharePairError,
  form,
  result,
  loading,
  error,
  onAShareChange,
  onASharePairChange,
  onRunAShare,
  onRunASharePair,
  onChange,
  onRun,
}: {
  aShareForm: AShareFormState;
  aSharePairForm: ASharePairFormState;
  aShareState: AShareStockState | null;
  aSharePairState: ASharePairState | null;
  aShareLoading: boolean;
  aSharePairLoading: boolean;
  aShareError: string | null;
  aSharePairError: string | null;
  form: StockFormState;
  result: StockSimulationResult;
  loading: boolean;
  error: string | null;
  onAShareChange: (key: keyof AShareFormState, value: string | boolean) => void;
  onASharePairChange: (key: keyof ASharePairFormState, value: string) => void;
  onRunAShare: () => Promise<void>;
  onRunASharePair: () => Promise<void>;
  onChange: (key: keyof StockFormState, value: string) => void;
  onRun: () => Promise<void>;
}) {
  return (
    <div className="mt-6 space-y-6">
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <InfoCard
          title="What this module does 杩欎釜鏉垮潡鍋氫粈涔?
          icon={<CandlestickChart className="h-5 w-5 text-blue-600" />}
        >
          It simulates stock-price evolution, sample paths, and terminal-price distributions using a geometric-Brownian-motion baseline.
          <span className="block text-sm text-gray-500">
            杩欎竴鍧椾富瑕佸仛鑲＄エ浠锋牸璺緞銆佺粓鐐瑰垎甯冨拰鍩虹椋庨櫓缁熻锛屼笉寮鸿皟鑽愯偂锛岃€屾槸寮鸿皟鈥滀环鏍煎浣曟紨鍖栤€濄€?
          </span>
        </InfoCard>
        <InfoCard
          title="Why it fits physics 涓轰粈涔堥€傚悎鐗╃悊鑳屾櫙"
          icon={<Sparkles className="h-5 w-5 text-amber-600" />}
        >
          The stock demo can be explained through diffusion, random walks, and stochastic processes.
          <span className="block text-sm text-gray-500">
            瀹冨拰鎵╂暎銆侀殢鏈烘父璧般€佹鐜囧垎甯冩紨鍖栧緢鎺ヨ繎锛岄€傚悎浣滀负閲戣瀺鏉垮潡鐨勭涓€绔欍€?
          </span>
        </InfoCard>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share Live Analysis <span className="text-base font-medium text-gray-500">A鑲″疄鏃跺垎鏋?/span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Load one A-share code, inspect market session status, latest quote fields, and historical volatility based on recent trading history.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氳繖涓€鍧椾紭鍏堥潰鍚?A 鑲℃棩甯稿垎鏋愶紝涓嶇洿鎺ョ粰涔板崠寤鸿锛岃€屾槸寮鸿皟鈥滃綋鍓嶅競鍦虹姸鎬佹槸浠€涔堛€佹渶鏂颁环鏍兼潵鑷摢閲屻€佽繎鏈熸尝鍔ㄧ巼鏈夊楂樷€濄€?
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 鑲＄エ浠ｇ爜</span>
              <input
                type="text"
                value={aShareForm.symbol}
                onChange={(event) => onAShareChange('symbol', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm uppercase outline-none transition focus:border-blue-500"
                placeholder="000001"
              />
              <span className="mt-2 block text-xs text-gray-500">Use 6-digit A-share codes such as `000001`, `600519`, or `300750`.</span>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Lookback Days 鍥炵湅澶╂暟</span>
              <input
                type="number"
                min={60}
                step={1}
                value={aShareForm.lookbackDays}
                onChange={(event) => onAShareChange('lookbackDays', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              />
              <span className="mt-2 block text-xs text-gray-500">Used for annualized drift and historical volatility windows.</span>
            </label>
          </div>

          <label className="mt-4 flex items-start gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={aShareForm.forceHistoryOnly}
              onChange={(event) => onAShareChange('forceHistoryOnly', event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>
              <span className="font-medium text-gray-900">Use history-only mode 鍙敤鍘嗗彶鏃ョ嚎妯″紡</span>
              <span className="mt-1 block text-xs text-gray-500">
                If live quotes are unstable, enable this to skip real-time fetching and use daily-close analysis directly.
              </span>
            </span>
          </label>

          <button
            onClick={onRunAShare}
            disabled={aShareLoading}
            className="mt-5 rounded-lg bg-gray-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-gray-800"
          >
            {aShareLoading ? 'Loading A-share... 姝ｅ湪鍔犺浇A鑲℃暟鎹? : 'Load A-share Analysis 鍔犺浇A鑲″垎鏋?}
          </button>

          {aShareError ? <p className="mt-3 text-sm text-red-600">{aShareError}</p> : null}

          <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Reliability note 鍙潬鎬ц鏄?/p>
            <p className="mt-2">
              During active sessions, the latest price is closer to a live quote; outside active sessions, it should be read as the latest available market quote or latest completed trading session reference.
            </p>
            <p className="mt-2">
              涓枃璇存槑锛欰鑲℃湁鍥哄畾浜ゆ槗鏃舵锛屽崍浼戙€佹敹鐩樺悗銆佸懆鏈拰鑺傚亣鏃ラ兘涓嶄細浜х敓鏂扮殑杩炵画绔炰环鏁版嵁锛屾墍浠ラ〉闈細鎶娾€滃競鍦虹姸鎬佲€濆拰鈥滄椂闂存埑鈥濅竴璧锋樉绀哄嚭鏉ャ€?
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  Live Snapshot 瀹炴椂蹇収
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  {aShareState ? `${aShareState.name} (${aShareState.symbol})` : 'Waiting for A-share data...'}
                </p>
              </div>
              {aShareState ? (
                <div className={`rounded-full px-3 py-1 text-xs font-semibold ${aShareState.marketClock.marketOpen ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                  {aShareState.marketClock.phaseLabel}
                </div>
              ) : null}
            </div>

            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Latest 鏈€鏂颁环" value={aShareState?.latestPrice ?? 0} note="Latest available quote from the current or most recent session." />
              <MetricCard label="Prev Close 鏄ㄦ敹" value={aShareState?.prevClose ?? aShareState?.latestClose ?? 0} note="Reference close from the previous trading day." />
              <MetricCard label="Change % 娑ㄨ穼骞? value={aShareState?.changePercent ?? 0} note="Relative move against the previous close." />
              <MetricCard label="HV252 骞村寲娉㈠姩" value={aShareState?.volatility.hv252 ?? 0} note="Annualized volatility estimated from recent daily closes." />
              <MetricCard label="HV20 鐭獥娉㈠姩" value={aShareState?.volatility.hv20 ?? 0} note="Short-window volatility for the last 20 trading days." />
              <MetricCard label="HV60 涓獥娉㈠姩" value={aShareState?.volatility.hv60 ?? 0} note="Medium-window volatility for the last 60 trading days." />
              <MetricCard label="Drift 骞村寲婕傜Щ" value={aShareState?.annualizedDrift ?? 0} note="Annualized mean log-return estimate from recent history." />
              <MetricCard label="Volume 鎬绘墜" value={aShareState?.volume ?? 0} note="Latest available turnover volume from the quote source." integer />
            </div>

            {aShareState ? (
              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Data source 鏁版嵁婧?</span> {aShareState.dataSource}</p>
                  <p className="mt-2">
                    <span className="font-semibold">Mode 褰撳墠妯″紡:</span>{' '}
                    {aShareState.realtimeAvailable === false ? 'History fallback 鍘嗗彶鏃ョ嚎鍥為€€妯″紡' : 'Live quote 瀹炴椂琛屾儏妯″紡'}
                  </p>
                  <p className="mt-2"><span className="font-semibold">Market clock 甯傚満鏃堕棿:</span> {aShareState.marketClock.localTime}</p>
                  <p className="mt-2"><span className="font-semibold">Latest trade date 鏈€杩戜氦鏄撴棩:</span> {aShareState.latestTradeDate}</p>
                  <p className="mt-2"><span className="font-semibold">Quote timestamp 鎶ヤ环鏃堕棿:</span> {aShareState.quoteTimestamp ?? 'N/A'}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Open / High / Low:</span> {formatMetricValue(aShareState.open)} / {formatMetricValue(aShareState.high)} / {formatMetricValue(aShareState.low)}</p>
                  <p className="mt-2"><span className="font-semibold">Average price 鍧囦环:</span> {formatMetricValue(aShareState.averagePrice)}</p>
                  <p className="mt-2"><span className="font-semibold">Change amount 娑ㄨ穼棰?</span> {formatMetricValue(aShareState.changeAmount)}</p>
                  <p className="mt-2"><span className="font-semibold">Amount 鎴愪氦棰?</span> {formatMetricValue(aShareState.amount, true)}</p>
                </div>
              </div>
            ) : null}

            {aShareState?.realtimeAvailable === false ? (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                <p className="font-semibold">Fallback mode 宸插垏鎹㈠埌鍘嗗彶鏃ョ嚎妯″紡</p>
                <p className="mt-2">
                  Live quote source is temporarily unavailable, so this panel is currently using the latest daily close and recent history.
                </p>
                <p className="mt-2">
                  涓枃璇存槑锛氬疄鏃剁洏鍙ｆ簮鏆傛椂涓嶅彲鐢紝鎵€浠ュ綋鍓嶇湅鍒扮殑鏄€滃巻鍙叉棩绾垮洖閫€妯″紡鈥濄€傛尝鍔ㄧ巼銆佽繎30鏃ヨ蛋鍔裤€佹渶杩戜氦鏄撴棩绛夊垎鏋愪粛鐒舵湁鏁堬紝浣嗏€滄渶鏂颁环鈥濇鏃舵洿鎺ヨ繎鏈€杩戞敹鐩樹环鑰屼笉鏄洏涓疄鏃朵环銆?
                </p>
              </div>
            ) : null}

            {aShareState?.notes?.length ? (
              <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                <p className="font-semibold">Interpretation notes 瑙ｈ鎻愮ず</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {aShareState.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          <ChartCard
            title="Recent Close Trend 杩?0鏃ユ敹鐩樿蛋鍔?
            note="This chart uses the latest daily closes, which makes it suitable for post-close analysis and stable volatility estimation."
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={aShareState?.historyPreview ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: 'Close 鏀剁洏浠?, angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(2)} />
                <Line type="monotone" dataKey="close" stroke="#111827" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share Pair Analysis <span className="text-base font-medium text-gray-500">A鑲″弻鑲＄エ鑱斿姩鍒嗘瀽</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Compare two A-share stocks to see whether they move together, how strong the historical relationship is, and whether the correlation is stable or drifting.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氬弻鑲＄エ涓嶆槸瑕佸悓鏃堕娴嬩袱鍙偂绁紝鑰屾槸鐪嬪畠浠箣闂寸殑鑱斿姩鍏崇郴锛屼緥濡傚悓鏉垮潡鑲＄エ鏄惁甯稿父涓€璧锋定璺岋紝鐩稿叧鎬ф槸绋冲畾杩樻槸鍦ㄥ彉鍖栥€?
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 1 鑲＄エ1</span>
              <input
                type="text"
                value={aSharePairForm.symbol1}
                onChange={(event) => onASharePairChange('symbol1', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm uppercase outline-none transition focus:border-blue-500"
                placeholder="000001"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 2 鑲＄エ2</span>
              <input
                type="text"
                value={aSharePairForm.symbol2}
                onChange={(event) => onASharePairChange('symbol2', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm uppercase outline-none transition focus:border-blue-500"
                placeholder="600519"
              />
            </label>
            <label className="block md:col-span-2">
              <span className="mb-2 block text-sm font-medium text-gray-700">Lookback Days 鍥炵湅澶╂暟</span>
              <input
                type="number"
                min={60}
                step={1}
                value={aSharePairForm.lookbackDays}
                onChange={(event) => onASharePairChange('lookbackDays', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              />
            </label>
          </div>

          <button
            onClick={onRunASharePair}
            disabled={aSharePairLoading}
            className="mt-5 rounded-lg bg-slate-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            {aSharePairLoading ? 'Loading Pair Data... 姝ｅ湪鍔犺浇鍙岃偂绁ㄦ暟鎹? : 'Load Pair Analysis 鍔犺浇鍙岃偂绁ㄥ垎鏋?}
          </button>

          {aSharePairError ? <p className="mt-3 text-sm text-red-600">{aSharePairError}</p> : null}

          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
            <p className="font-semibold">How to read pair correlation 濡備綍鐞嗚В鍙岃偂绁ㄧ浉鍏虫€?/p>
            <p className="mt-2">
              A high positive correlation means the two stocks often move in the same direction, while a lower or unstable rolling correlation suggests the relationship can weaken over time.
            </p>
            <p className="mt-2">
              涓枃璇存槑锛氳繖閲岀殑鐩稿叧鎬т笉鏄洜鏋滃叧绯伙紝鍙槸缁熻涓婄殑鈥滃悓娑ㄥ悓璺岀▼搴︹€濄€傛粴鍔ㄧ浉鍏崇郴鏁扮敤鏉ヨ瀵熻繖绉嶈仈鍔ㄦ槸鍚︿竴鐩寸ǔ瀹氥€?
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-xl font-semibold text-gray-900">Pair Summary 鍙岃偂绁ㄦ憳瑕?/h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Correlation 鐩稿叧绯绘暟" value={aSharePairState?.correlation ?? 0} note="Overall historical co-movement across the selected lookback window." />
              <MetricCard label="HV252 鑲＄エ1娉㈠姩" value={aSharePairState?.hv252_1 ?? 0} note="Annualized volatility of the first stock." />
              <MetricCard label="HV252 鑲＄エ2娉㈠姩" value={aSharePairState?.hv252_2 ?? 0} note="Annualized volatility of the second stock." />
              <MetricCard label="Data Source 鏁版嵁婧? value={aSharePairState ? 1 : 0} note={aSharePairState?.dataSource ?? 'Waiting for pair data.'} integer />
            </div>
            {aSharePairState ? (
              <p className="mt-4 text-sm text-gray-500">
                {aSharePairState.name1} ({aSharePairState.symbol1}) vs {aSharePairState.name2} ({aSharePairState.symbol2})
              </p>
            ) : null}
          </div>

          <ChartCard
            title="Dual Price Trend 鍙屼环鏍艰蛋鍔?
            note="Compare the most recent daily closes of the two selected A-share stocks."
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={aSharePairState?.pairHistory ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" label={{ value: 'Stock 1 鑲＄エ1', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Stock 2 鑲＄エ2', angle: 90, position: 'insideRight' }} />
                <Tooltip formatter={(value: number) => value.toFixed(2)} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="close1" name={aSharePairState?.symbol1 ?? 'Stock 1'} stroke="#2563eb" strokeWidth={2.5} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="close2" name={aSharePairState?.symbol2 ?? 'Stock 2'} stroke="#dc2626" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Rolling Correlation 婊氬姩鐩稿叧绯绘暟"
            note="A 20-day rolling correlation helps show whether the relationship is strengthening, weakening, or drifting over time."
            heightClass="h-[300px]"
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={aSharePairState?.rollingCorrelation ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-1, 1]} label={{ value: 'Correlation 鐩稿叧鎬?, angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(3)} />
                <Line type="monotone" dataKey="correlation" stroke="#0f766e" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>


      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_1.3fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            Stock Inputs <span className="text-base font-medium text-gray-500">鑲＄エ妯℃嫙鍙傛暟</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氫笅闈㈣繖浜涘弬鏁板喅瀹氳偂绁ㄢ€滃钩鍧囧悜涓婃紓绉诲灏戔€濆拰鈥滀笂涓嬫尝鍔ㄥ鍓х儓鈥濓紝绯荤粺浼氭嵁姝よ嚜鍔ㄧ敓鎴愭牱鏈矾寰勪笌缁熻鍒嗗竷銆?
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            {STOCK_INPUTS.map((item) => {
              const key = item.key as keyof StockFormState;
              return (
                <label key={item.key} className="block">
                  <span className="mb-2 block text-sm font-medium text-gray-700">{item.label}</span>
                  <input
                    type="number"
                    step={key === 'steps' || key === 'paths' ? 1 : 0.01}
                    min={key === 'volatility' ? 0 : undefined}
                    value={form[key]}
                    onChange={(event) => onChange(key, event.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                  />
                  <span className="mt-2 block text-xs text-gray-500">{item.note}</span>
                </label>
              );
            })}
          </div>

          <button
            onClick={onRun}
            disabled={loading}
            className="mt-5 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
          >
            {loading ? 'Running... 姝ｅ湪妯℃嫙' : 'Run Stock Simulation 杩愯鑲＄エ妯℃嫙'}
          </button>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
            <p className="font-semibold">How to read it 鎬庝箞鐞嗚В缁撴灉</p>
            <p className="mt-2">
              Sample paths show possible future trajectories, the terminal histogram shows where final prices cluster,
              and the summary cards give quick risk and spread references.
            </p>
            <p className="mt-2">
              涓枃璇存槑锛氭牱鏈矾寰勭敤浜庣洿瑙傜湅鈥滃彲鑳芥€庝箞璧扳€濓紝缁堢偣鍒嗗竷鐢ㄤ簬鐪嬧€滄渶鍚庡ぇ姒傝惤鍦ㄥ摢浜涗环鏍煎尯闂粹€濓紝缁熻鎽樿鐢ㄤ簬蹇€熷垽鏂闄╁拰绂绘暎绋嬪害銆?
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <ChartCard
            title="Sample Paths 鏍锋湰璺緞"
            note="灞曠ず鑻ュ共鏉℃ā鎷熶环鏍艰矾寰勩€傛瘡涓€鏉＄嚎浠ｈ〃涓€绉嶅彲鑳界殑鏈潵婕斿寲杞ㄨ抗銆?
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.samplePathData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" label={{ value: 'Step 鏃堕棿姝?, position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Price 浠锋牸', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(2)} labelFormatter={(label: number) => `Step: ${label}`} />
                <Legend />
                {Object.keys(result.samplePathData[0] || {})
                  .filter((key) => key !== 'step')
                  .map((key, index) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      dot={false}
                      stroke={PATH_COLORS[index % PATH_COLORS.length]}
                      strokeWidth={2}
                    />
                  ))}
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Terminal Distribution 缁堢偣浠锋牸鍒嗗竷"
            note="鏌辩姸鍥捐〃绀烘墍鏈夋ā鎷熻矾寰勫湪缁撴潫鏃跺埢钀藉叆鍚勪釜浠锋牸鍖洪棿鐨勬鏁般€?
            heightClass="h-[300px]"
          >
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={result.terminalHistogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" angle={-18} textAnchor="end" height={60} interval={0} />
                <YAxis label={{ value: 'Count 鏁伴噺', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" name="Terminal count 缁堢偣鏁伴噺" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Simulation Summary <span className="text-base font-medium text-gray-500">妯℃嫙鎽樿</span>
        </h2>
        <p className="text-sm text-gray-500">
          涓枃璇存槑锛氳繖閲岀粺璁＄殑鏄墍鏈夌粓鐐逛环鏍硷紝涓嶆槸涓棿姣忎竴姝ョ殑骞冲潎鍊硷紝鍥犳鏇撮€傚悎鍥炵瓟鈥滄渶鍚庡彲鑳芥敹鍦ㄥ摢閲屸€濄€?
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Mean 鍧囧€? value={result.summary.mean} note="缁堢偣浠锋牸鐨勫钩鍧囨按骞炽€? />
          <MetricCard label="Std 鏍囧噯宸? value={result.summary.std} note="缁堢偣浠锋牸绂绘暎绋嬪害锛岃秺澶ц〃绀洪闄╄秺楂樸€? />
          <MetricCard label="P05 5%鍒嗕綅" value={result.summary.p05} note="杈冩偛瑙傛儏褰笅鐨勫弬鑰冧环鏍笺€? />
          <MetricCard label="P95 95%鍒嗕綅" value={result.summary.p95} note="杈冧箰瑙傛儏褰笅鐨勫弬鑰冧环鏍笺€? />
          <MetricCard label="Median 涓綅鏁? value={result.summary.median} note="涓€鍗婅矾寰勯珮浜庡畠锛屼竴鍗婅矾寰勪綆浜庡畠銆? />
          <MetricCard label="Min 鏈€灏忓€? value={result.summary.min} note="鎵€鏈夌粓鐐逛环鏍间腑鐨勬渶浣庡€笺€? />
          <MetricCard label="Max 鏈€澶у€? value={result.summary.max} note="鎵€鏈夌粓鐐逛环鏍间腑鐨勬渶楂樺€笺€? />
          <MetricCard label="Paths 璺緞鏁? value={form.paths} note="褰撳墠鐢ㄤ簬缁熻鐨勬€绘ā鎷熸牱鏈暟銆? integer />
        </div>
      </section>
    </div>
  );
}

function OptionsPanel({
  form,
  result,
  option2DForm,
  option2DResult,
  marketCompareForm,
  marketStockState,
  marketCompareState,
  aShareEtfOptionForm,
  aShareEtfOptionState,
  aShareIndexOptionForm,
  aShareIndexOptionState,
  loading,
  error,
  option2DLoading,
  option2DError,
  marketLoading,
  marketError,
  aShareEtfOptionLoading,
  aShareEtfOptionError,
  aShareIndexOptionLoading,
  aShareIndexOptionError,
  onChange,
  onRun,
  onChange2D,
  onRun2D,
  onMarketCompareInput,
  onRunMarketComparison,
  onAShareEtfOptionInput,
  onRunAShareEtfOption,
  onAShareIndexOptionInput,
  onRunAShareIndexOption,
}: {
  form: OptionFormState;
  result: OptionPricingResult;
  option2DForm: Option2DFormState;
  option2DResult: Option2DPricingResult;
  marketCompareForm: MarketCompareFormState;
  marketStockState: MarketStockState | null;
  marketCompareState: MarketCompareState | null;
  aShareEtfOptionForm: AShareETFOptionFormState;
  aShareEtfOptionState: AShareETFOptionState | null;
  aShareIndexOptionForm: AShareIndexOptionFormState;
  aShareIndexOptionState: AShareIndexOptionState | null;
  loading: boolean;
  error: string | null;
  option2DLoading: boolean;
  option2DError: string | null;
  marketLoading: boolean;
  marketError: string | null;
  aShareEtfOptionLoading: boolean;
  aShareEtfOptionError: string | null;
  aShareIndexOptionLoading: boolean;
  aShareIndexOptionError: string | null;
  onChange: (key: keyof OptionFormState, value: string) => void;
  onRun: () => Promise<void>;
  onChange2D: (key: keyof Option2DFormState, value: string) => void;
  onRun2D: () => Promise<void>;
  onMarketCompareInput: (key: keyof MarketCompareFormState, value: string | boolean) => void;
  onRunMarketComparison: () => Promise<void>;
  onAShareEtfOptionInput: (key: keyof AShareETFOptionFormState, value: string) => void;
  onRunAShareEtfOption: () => Promise<void>;
  onAShareIndexOptionInput: (key: keyof AShareIndexOptionFormState, value: string) => void;
  onRunAShareIndexOption: () => Promise<void>;
}) {
  return (
    <div className="mt-6 space-y-6">
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <InfoCard
          title="What this module does 杩欎釜鏉垮潡鍋氫粈涔?
          icon={<CircleDollarSign className="h-5 w-5 text-green-600" />}
        >
          It introduces option pricing as a financial PDE application, starting from Black-Scholes 1D.
          <span className="block text-sm text-gray-500">
            浣犲彲浠ュ厛鎶婂畠鐞嗚В鎴愨€滀互鑲＄エ浠锋牸鍜屾椂闂翠负鑷彉閲忥紝姹備竴涓噾铻嶅悎绾︿环鍊尖€濈殑 PDE 渚嬪瓙銆?
          </span>
        </InfoCard>
        <InfoCard
          title="Why it matters 涓轰粈涔堝€煎緱鍋?
          icon={<BarChart3 className="h-5 w-5 text-purple-600" />}
        >
          Option pricing is one of the most classical and explainable PDE applications in finance.
          <span className="block text-sm text-gray-500">
            瀹冭兘浣撶幇鏁板€兼柟娉曘€佽竟鐣屾潯浠跺拰鍙傛暟鏁忔劅鎬х殑浠峰€硷紝涔熸洿閫傚悎鍐欒繘瀛︽湳灞曠ず銆?
          </span>
        </InfoCard>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share ETF Options <span className="text-base font-medium text-gray-500">A鑲TF鏈熸潈蹇収</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Start with the most practical domestic derivative case: 50ETF options. This panel focuses on market snapshots, Greeks, and theory-vs-market reference rather than automated execution.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氳繖閲屼紭鍏堝仛鍥藉唴 ETF 鏈熸潈锛屾槸鍥犱负瀹冩瘮涓偂鏈熸潈鏇寸ǔ銆佹洿閫傚悎浣滀负鏁板€煎垎鏋愬钩鍙伴噷鐨勮鐢熷搧搴旂敤鍏ュ彛銆?
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Underlying 鏍囩殑ETF</span>
              <select
                value={aShareEtfOptionForm.underlying}
                onChange={(event) => onAShareEtfOptionInput('underlying', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="510050">50ETF (510050)</option>
                <option value="510300">300ETF (510300)</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Option Type 鏂瑰悜</span>
              <select
                value={aShareEtfOptionForm.optionType}
                onChange={(event) => onAShareEtfOptionInput('optionType', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="call">Call 璁よ喘</option>
                <option value="put">Put 璁ゆ步</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Expiry 鍒版湡鏃?/span>
              <select
                value={aShareEtfOptionForm.expiry}
                onChange={(event) => onAShareEtfOptionInput('expiry', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="">Auto 鑷姩</option>
                {(aShareEtfOptionState?.availableExpiries ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Strike 琛屾潈浠?/span>
              <select
                value={aShareEtfOptionForm.strike}
                onChange={(event) => onAShareEtfOptionInput('strike', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="">Auto 鑷姩</option>
                {(aShareEtfOptionState?.availableStrikes ?? []).map((item) => (
                  <option key={item} value={String(item)}>
                    {item.toFixed(3)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <button
            onClick={onRunAShareEtfOption}
            disabled={aShareEtfOptionLoading}
            className="mt-5 rounded-lg bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            {aShareEtfOptionLoading ? 'Loading ETF Option... 姝ｅ湪鍔犺浇ETF鏈熸潈' : 'Load ETF Option Snapshot 鍔犺浇ETF鏈熸潈蹇収'}
          </button>

          {aShareEtfOptionError ? <p className="mt-3 text-sm text-red-600">{aShareEtfOptionError}</p> : null}

          <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">How to read this 濡備綍鐞嗚В杩欎竴鍧?/p>
            <p className="mt-2">
              `latest price` is the observed option quote, `theoretical value` is the pricing reference returned with the option data, and `pricing gap` helps you see how far the traded quote is from that theoretical reference.
            </p>
            <p className="mt-2">
              涓枃璇存槑锛氳繖涓€鍧楁洿鍍忊€滃競鍦哄揩鐓?+ 鏁忔劅鎬у垎鏋愨€濓紝涓嶆槸鑷姩涓嬪崟绯荤粺锛屼篃涓嶆槸鎶曡祫寤鸿銆?
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-xl font-semibold text-gray-900">ETF Option Summary ETF鏈熸潈鎽樿</h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Latest Price 鏈€鏂颁环" value={aShareEtfOptionState?.latestPrice ?? 0} note="Observed option latest price." />
              <MetricCard label="Midpoint 涓棿浠? value={aShareEtfOptionState?.midpoint ?? 0} note="Midpoint between bid and ask when both are available." />
              <MetricCard label="IV 闅愬惈娉㈠姩鐜? value={aShareEtfOptionState?.impliedVolatility ?? 0} note="Implied volatility from the option snapshot." />
              <MetricCard label="Gap 鐞嗚鍋忓樊" value={aShareEtfOptionState?.pricingGap ?? 0} note="Latest price minus theoretical value." />
              <MetricCard label="Delta" value={aShareEtfOptionState?.delta ?? 0} note="First-order sensitivity to the ETF price." />
              <MetricCard label="Gamma" value={aShareEtfOptionState?.gamma ?? 0} note="Rate of change of Delta." />
              <MetricCard label="Theta" value={aShareEtfOptionState?.theta ?? 0} note="Time-decay sensitivity." />
              <MetricCard label="Vega" value={aShareEtfOptionState?.vega ?? 0} note="Sensitivity to implied volatility." />
            </div>

            {aShareEtfOptionState ? (
              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Underlying 鏍囩殑:</span> {aShareEtfOptionState.underlyingName} ({aShareEtfOptionState.underlying})</p>
                  <p className="mt-2"><span className="font-semibold">Underlying price 鏍囩殑鏈€鏂颁环:</span> {formatMetricValue(aShareEtfOptionState.underlyingPrice)}</p>
                  <p className="mt-2"><span className="font-semibold">Prev close / Open:</span> {formatMetricValue(aShareEtfOptionState.underlyingPrevClose)} / {formatMetricValue(aShareEtfOptionState.underlyingOpen)}</p>
                  <p className="mt-2"><span className="font-semibold">High / Low:</span> {formatMetricValue(aShareEtfOptionState.underlyingHigh)} / {formatMetricValue(aShareEtfOptionState.underlyingLow)}</p>
                  <p className="mt-2"><span className="font-semibold">Underlying time 鏍囩殑鏃堕棿:</span> {aShareEtfOptionState.underlyingQuoteTime}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Contract 鍚堢害:</span> {aShareEtfOptionState.contractName}</p>
                  <p className="mt-2"><span className="font-semibold">Trading code 浜ゆ槗浠ｇ爜:</span> {aShareEtfOptionState.tradingCode}</p>
                  <p className="mt-2"><span className="font-semibold">Expiry / Strike:</span> {aShareEtfOptionState.expiry} / {formatMetricValue(aShareEtfOptionState.strike)}</p>
                  <p className="mt-2"><span className="font-semibold">Bid / Ask:</span> {formatMetricValue(aShareEtfOptionState.bid)} / {formatMetricValue(aShareEtfOptionState.ask)}</p>
                  <p className="mt-2"><span className="font-semibold">Quote time 鎶ヤ环鏃堕棿:</span> {aShareEtfOptionState.quoteTime}</p>
                </div>
              </div>
            ) : null}

            {aShareEtfOptionState ? (
              <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                <p className="font-semibold">Interpretation notes 瑙ｈ鎻愮ず</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {aShareEtfOptionState.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.1fr_1.3fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            Option Inputs <span className="text-base font-medium text-gray-500">鏈熸潈瀹氫环鍙傛暟</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氳繖涓€缁勫弬鏁版槸 Black-Scholes 1D 鐨勭涓€鐗堝叆鍙ｏ紝鍏堝府鍔╀綘鐞嗚В鍚箟锛屽啀鐪嬩环鏍兼洸绾垮拰鏀剁泭鍑芥暟銆?
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            {OPTION_INPUTS.map((item) => {
              const key = item.key as keyof OptionFormState;
              return (
                <label key={item.key} className="block">
                  <span className="mb-2 block text-sm font-medium text-gray-700">{item.label}</span>
                  <input
                    type="number"
                    step={0.01}
                    min={key === 'volatility' || key === 'maturity' ? 0 : undefined}
                    value={form[key]}
                    onChange={(event) => onChange(key, event.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                  />
                  <span className="mt-2 block text-xs text-gray-500">{item.note}</span>
                </label>
              );
            })}
          </div>

          <button
            onClick={onRun}
            disabled={loading}
            className="mt-5 rounded-lg bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
          >
            {loading ? 'Pricing... 姝ｅ湪瀹氫环' : 'Run Black-Scholes 1D 杩愯 Black-Scholes 1D'}
          </button>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

          <div className="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-900">
            <p className="font-semibold">How to read it 鎬庝箞鐞嗚В鏈熸潈鍥?/p>
            <p className="mt-2">
              The price curve shows how a call or put changes when the spot price moves. The payoff curve shows the
              contract value at expiry, without time value.
            </p>
            <p className="mt-2">
              涓枃璇存槑锛氫环鏍兼洸绾跨湅鐨勬槸鈥滀粖澶╁€煎灏戦挶鈥濓紝鏀剁泭鏇茬嚎鐪嬬殑鏄€滃埌鏈熼偅涓€鍒昏兘璧氬灏戔€濓紝涓よ€呯殑宸埆灏辨槸鏃堕棿浠峰€肩殑涓€閮ㄥ垎銆?
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <ChartCard
            title="Black-Scholes Price Curve 瀹氫环鏇茬嚎"
            note="灞曠ず涓嶅悓鏍囩殑浠锋牸涓嬶紝鐪嬫定鏈熸潈鍜岀湅璺屾湡鏉冪殑鐞嗚浠锋牸銆?
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="spot" label={{ value: 'Spot 鏍囩殑浠锋牸', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Option Price 鏈熸潈浠锋牸', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(4)} />
                <Legend />
                <Line type="monotone" dataKey="callPrice" stroke="#16a34a" strokeWidth={2} dot={false} name="Call 鐪嬫定鏈熸潈" />
                <Line type="monotone" dataKey="putPrice" stroke="#dc2626" strokeWidth={2} dot={false} name="Put 鐪嬭穼鏈熸潈" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Payoff Curve 鏀剁泭鏇茬嚎"
            note="灞曠ず鍒版湡鏃剁殑鍚堢害鏀剁泭锛屼笉鍖呭惈鍒版湡鍓嶅皻鏈疄鐜扮殑鏃堕棿浠峰€笺€?
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="spot" label={{ value: 'Spot 鏍囩殑浠锋牸', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Payoff 鏀剁泭', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(4)} />
                <Legend />
                <Line type="monotone" dataKey="callPayoff" stroke="#0f766e" strokeWidth={2} dot={false} name="Call payoff 鐪嬫定鏀剁泭" />
                <Line type="monotone" dataKey="putPayoff" stroke="#b91c1c" strokeWidth={2} dot={false} name="Put payoff 鐪嬭穼鏀剁泭" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Pricing Summary <span className="text-base font-medium text-gray-500">瀹氫环鎽樿</span>
        </h2>
        <p className="text-sm text-gray-500">
          涓枃璇存槑锛氫笅闈㈢殑鎽樿榛樿鐪嬪綋鍓?`spot` 涓嬬殑浠锋牸锛屽苟鎶婂唴鍦ㄤ环鍊煎拰鏃堕棿浠峰€兼媶寮€锛屽府鍔╀綘鐞嗚В涓轰粈涔堚€滅幇鍦ㄧ殑浠锋牸鈥濅笉绛変簬鈥滃埌鏈熸敹鐩娾€濄€?
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricCard label="Call Price 鐪嬫定浠锋牸" value={result.summary.callAtSpot} note="褰撳墠鏍囩殑浠锋牸涓嬬殑鐪嬫定鏈熸潈鐞嗚浠锋牸銆? />
          <MetricCard label="Put Price 鐪嬭穼浠锋牸" value={result.summary.putAtSpot} note="褰撳墠鏍囩殑浠锋牸涓嬬殑鐪嬭穼鏈熸潈鐞嗚浠锋牸銆? />
          <MetricCard label="Call Intrinsic 鐪嬫定鍐呭湪浠峰€? value={result.summary.intrinsicCall} note="绔嬪嵆鍒版湡鏃剁湅娑ㄥ悎绾﹁兘鍏戠幇鐨勪环鍊笺€? />
          <MetricCard label="Put Intrinsic 鐪嬭穼鍐呭湪浠峰€? value={result.summary.intrinsicPut} note="绔嬪嵆鍒版湡鏃剁湅璺屽悎绾﹁兘鍏戠幇鐨勪环鍊笺€? />
          <MetricCard label="Call Time Value 鐪嬫定鏃堕棿浠峰€? value={result.summary.timeValueCall} note="鐪嬫定鏈熸潈浠锋牸涓秴鍑哄唴鍦ㄤ环鍊肩殑閮ㄥ垎銆? />
          <MetricCard label="Put Time Value 鐪嬭穼鏃堕棿浠峰€? value={result.summary.timeValuePut} note="鐪嬭穼鏈熸潈浠锋牸涓秴鍑哄唴鍦ㄤ环鍊肩殑閮ㄥ垎銆? />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Greeks Summary <span className="text-base font-medium text-gray-500">鏁忔劅鎬ф寚鏍?/span>
        </h2>
        <p className="text-sm text-gray-500">
          涓枃璇存槑锛欸reeks 鐢ㄦ潵琛￠噺鏈熸潈浠锋牸瀵规爣鐨勪环鏍笺€佹尝鍔ㄧ巼銆佹椂闂村拰鍒╃巼鍙樺寲鐨勬晱鎰熺▼搴︼紝鏄噺鍖栧垎鏋愰噷闈炲父甯歌鐨勪竴缁勬寚鏍囥€?
        </p>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <GreekGroupCard
            title="Call Greeks 鐪嬫定鏈熸潈 Greeks"
            values={result.summary.greeks.call}
          />
          <GreekGroupCard
            title="Put Greeks 鐪嬭穼鏈熸潈 Greeks"
            values={result.summary.greeks.put}
          />
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">
            Black-Scholes 2D <span className="text-base font-medium text-gray-500">鍙岃祫浜т簩缁存洸闈?/span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            涓枃璇存槑锛氳繖涓€鍧楀睍绀虹殑鏄弻璧勪骇銆佸甫鐩稿叧鎬х殑 basket-style 杩戜技鏇查潰锛岀敤鏉ュ府鍔╀綘鐞嗚В浜岀淮閲戣瀺 PDE 鍦烘櫙涓嬩环鏍煎浣曢殢涓や釜璧勪骇鍚屾椂鍙樺寲銆?
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
            <h3 className="text-lg font-semibold text-gray-900">2D Inputs 浜岀淮鍙傛暟</h3>
            <p className="mt-2 text-sm text-gray-500">
              杩欓噷鐗瑰埆鍊煎緱鍏虫敞 `correlation`锛屽畠鍐冲畾涓ゅ彧璧勪骇鑱斿姩寮哄急锛屼篃浼氭樉钁楁敼鍙樻洸闈㈠舰鐘躲€?
            </p>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
              {OPTION_2D_INPUTS.map((item) => {
                const key = item.key as keyof Option2DFormState;
                return (
                  <label key={item.key} className="block">
                    <span className="mb-2 block text-sm font-medium text-gray-700">{item.label}</span>
                    <input
                      type="number"
                      step={key === 'gridSize' ? 1 : 0.01}
                      value={option2DForm[key]}
                      onChange={(event) => onChange2D(key, event.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                    />
                    <span className="mt-2 block text-xs text-gray-500">{item.note}</span>
                  </label>
                );
              })}
            </div>

            <button
              onClick={onRun2D}
              disabled={option2DLoading}
              className="mt-5 rounded-lg bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
            >
              {option2DLoading ? 'Pricing 2D... 姝ｅ湪鐢熸垚浜岀淮鏇查潰' : 'Run Black-Scholes 2D 杩愯 Black-Scholes 2D'}
            </button>

            {option2DError ? <p className="mt-3 text-sm text-red-600">{option2DError}</p> : null}

            <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-900">
              <p className="font-semibold">Interpretation 缁撴灉瑙ｈ</p>
              <p className="mt-2">
                Higher areas in the surface mean a more valuable basket-style call when the two assets jointly move into favorable regions.
              </p>
              <p className="mt-2">
                涓枃璇存槑锛氱儹鍔涘浘瓒婁寒锛岃〃绀哄湪瀵瑰簲 `璧勪骇1浠锋牸 + 璧勪骇2浠锋牸` 缁勫悎涓嬶紝杩欎釜浜岀淮鐪嬫定鍚堢害瓒婂€奸挶銆?
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <ChartCard
              title="2D Price Surface 浜岀淮浠锋牸鏇查潰"
              note="妯酱鍜岀旱杞村垎鍒搴斾袱鍙祫浜т环鏍硷紝棰滆壊琛ㄧず浜岀淮鐪嬫定浠锋牸楂樹綆銆?
              heightClass="h-[560px]"
            >
              <Heatmap
                solution={option2DResult.surface}
                nx={option2DResult.xValues.length}
                ny={option2DResult.yValues.length}
                title="2D basket-style call surface"
              />
            </ChartCard>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Effective Vol 鏈夋晥娉㈠姩鐜? value={option2DResult.summary.effectiveVolatility} note="灏嗕袱鍙祫浜у拰鐩稿叧鎬ф姌绠楀悗鐨勭瓑鏁堟尝鍔ㄦ按骞炽€? />
          <MetricCard label="Basket Spot 绡瓙浠锋牸" value={option2DResult.summary.basketSpot} note="鐢ㄤ袱鍙祫浜у綋鍓嶄环鏍兼瀯閫犵殑骞冲潎绡瓙浠锋牸銆? />
          <MetricCard label="2D Call 褰撳墠浜岀淮浠锋牸" value={option2DResult.summary.callAtCurrentPair} note="褰撳墠璧勪骇缁勫悎涓嬬殑浜岀淮鐪嬫定浠锋牸銆? />
          <MetricCard label="Surface Range 鏇查潰璺ㄥ害" value={option2DResult.summary.surfaceMax - option2DResult.summary.surfaceMin} note="鏁村紶浜岀淮鏇查潰浠庢渶浣庡埌鏈€楂樼殑浠锋牸璺ㄥ害銆? />
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">
            Market Comparison <span className="text-base font-medium text-gray-500">妯″瀷涓庡競鍦哄姣?/span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            杩欓噷浼氫粠鐪熷疄甯傚満蹇収鑷姩浼拌 `spot / historical volatility / risk-free rate`锛屽苟骞舵帓灞曠ず `model price / market price / implied volatility / pricing gap`銆?
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
            <h3 className="text-lg font-semibold text-gray-900">Live Market Inputs 瀹炴椂甯傚満杈撳叆</h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Ticker 鑲＄エ浠ｇ爜</span>
                <input
                  type="text"
                  value={marketCompareForm.symbol}
                  onChange={(event) => onMarketCompareInput('symbol', event.target.value.toUpperCase())}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Option Type 鏈熸潈鏂瑰悜</span>
                <select
                  value={marketCompareForm.optionType}
                  onChange={(event) => onMarketCompareInput('optionType', event.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                >
                  <option value="call">call</option>
                  <option value="put">put</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Maturity Years 鍒版湡骞撮檺</span>
                <input
                  type="number"
                  step={0.01}
                  value={marketCompareForm.maturityYears}
                  onChange={(event) => onMarketCompareInput('maturityYears', event.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                />
              </label>
              <label className="flex items-center gap-3 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={marketCompareForm.useMarketIv}
                  onChange={(event) => onMarketCompareInput('useMarketIv', event.target.checked)}
                />
                Use market IV 浣跨敤甯傚満闅愬惈娉㈠姩鐜?
              </label>
            </div>

            <button
              onClick={onRunMarketComparison}
              disabled={marketLoading}
              className="mt-5 rounded-lg bg-slate-800 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-900"
            >
              {marketLoading ? 'Loading Market Data... 姝ｅ湪鑾峰彇甯傚満鏁版嵁' : 'Load Market Comparison 鍔犺浇甯傚満瀵规瘮'}
            </button>

            {marketError ? <p className="mt-3 text-sm text-red-600">{marketError}</p> : null}

            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-semibold">Reliability Notice 鍙潬鎬у０鏄?/p>
              <p className="mt-2">This is model-based analysis, not investment advice.</p>
              <p className="mt-2">涓枃璇存槑锛氳繖閲屽睍绀虹殑鏄ā鍨嬩及鍊煎拰甯傚満蹇収瀵规瘮锛屼粎渚涘涔犮€佺爺绌跺拰鍒嗘瀽鍙傝€冿紝涓嶆瀯鎴愭姇璧勫缓璁€?/p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <MetricCard label="Spot 鐜颁环" value={marketStockState?.spot ?? 0} note="鏈€鏂拌偂绁ㄤ环鏍煎揩鐓с€? />
              <MetricCard label="Hist Vol 鍘嗗彶娉㈠姩鐜? value={marketStockState?.historicalVolatility ?? 0} note="鐢卞巻鍙插鏁版敹鐩婄巼浼拌寰楀埌銆? />
              <MetricCard label="Risk-free 鏃犻闄╁埄鐜? value={marketStockState?.riskFreeRate ?? 0} note="鐢ㄤ簬妯″瀷瀹氫环鐨勫埄鐜囦唬鐞嗗€笺€? />
              <MetricCard label="Drift 婕傜Щ鐜? value={marketStockState?.drift ?? 0} note="鐢卞巻鍙叉敹鐩婄巼骞村寲寰楀埌鐨勭矖鐣ユ紓绉讳及璁°€? />
              <MetricCard label="Model Price 妯″瀷浠锋牸" value={marketCompareState?.modelPrice ?? 0} note="Black-Scholes 绫绘ā鍨嬬粰鍑虹殑浼板€笺€? />
              <MetricCard label="Market Price 甯傚満浠锋牸" value={marketCompareState?.marketPrice ?? 0} note="鏈熸潈閾惧揩鐓т腑鐨勫競鍦轰环鏍艰繎浼笺€? />
              <MetricCard label="Implied Vol 闅愬惈娉㈠姩鐜? value={marketCompareState?.impliedVolatility ?? 0} note="鏉ヨ嚜甯傚満鏈熸潈閾剧殑闅愬惈娉㈠姩鐜囧瓧娈点€? />
              <MetricCard label="Pricing Gap 瀹氫环宸? value={marketCompareState?.pricingGap ?? 0} note="妯″瀷浠锋牸鍑忓幓甯傚満浠锋牸锛屾鍊艰〃绀烘ā鍨嬫洿璐点€? />
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">Market Snapshot 甯傚満蹇収</h3>
              <div className="mt-4 space-y-2 text-sm text-gray-600">
                <p>Symbol: {marketCompareState?.symbol || '-'}</p>
                <p>Contract: {marketCompareState?.contractSymbol || '-'}</p>
                <p>Expiry: {marketCompareState?.expiry || '-'}</p>
                <p>Strike: {marketCompareState?.strike?.toFixed(2) ?? '-'}</p>
                <p>Type: {marketCompareState?.optionType || '-'}</p>
              </div>
              <div className="mt-4 rounded-md bg-gray-50 p-3 text-xs text-gray-500">
                {(marketCompareState?.notes || []).map((note) => (
                  <p key={note} className="mt-1 first:mt-0">{note}</p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function SummaryCard({
  icon,
  title,
  subtitle,
  description,
}: {
  icon: ReactNode;
  title: string;
  subtitle: string;
  description: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 text-gray-700">{icon}</div>
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      <p className="mt-1 text-sm font-medium text-gray-500">{subtitle}</p>
      <p className="mt-3 text-sm text-gray-600">{description}</p>
    </div>
  );
}

function InfoCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">{icon}</div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="mt-4 text-gray-600">{children}</div>
    </div>
  );
}

function ChartCard({
  title,
  note,
  children,
  heightClass,
}: {
  title: string;
  note: string;
  children: ReactNode;
  heightClass: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-sm text-gray-500">{note}</p>
      <div className={`mt-4 ${heightClass}`}>{children}</div>
    </div>
  );
}

function formatMetricValue(value: number | null | undefined, integer = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'N/A';
  }
  return integer ? `${Math.round(value)}` : value.toFixed(2);
}

function MetricCard({
  label,
  value,
  note,
  integer = false,
}: {
  label: string;
  value: number;
  note: string;
  integer?: boolean;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-medium text-gray-500">{label}</div>
      <div className="mt-2 text-2xl font-bold text-gray-900">{integer ? Math.round(value) : value.toFixed(2)}</div>
      <div className="mt-2 text-sm text-gray-600">{note}</div>
    </div>
  );
}

function GreekGroupCard({
  title,
  values,
}: {
  title: string;
  values: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
}) {
  const rows = [
    ['Delta', values.delta, '瀵规爣鐨勪环鏍煎彉鍖栨渶鐩存帴鐨勬晱鎰熷害銆?],
    ['Gamma', values.gamma, '琛￠噺 Delta 鑷韩鍙樺寲閫熷害銆?],
    ['Theta', values.theta, '琛￠噺鏃堕棿娴侀€濆浠锋牸鐨勫奖鍝嶃€?],
    ['Vega', values.vega, '琛￠噺娉㈠姩鐜囧彉鍖栧浠锋牸鐨勫奖鍝嶃€?],
    ['Rho', values.rho, '琛￠噺鍒╃巼鍙樺寲瀵逛环鏍肩殑褰卞搷銆?],
  ] as const;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <div className="mt-4 space-y-3">
        {rows.map(([label, value, note]) => (
          <div key={label} className="rounded-md bg-gray-50 p-3">
            <div className="flex items-center justify-between gap-4">
              <span className="font-medium text-gray-900">{label}</span>
              <span className="text-sm font-semibold text-gray-700">{value.toFixed(4)}</span>
            </div>
            <p className="mt-1 text-xs text-gray-500">{note}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
        active ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {children}
    </button>
  );
}

function simulateStockDynamics(form: StockFormState): StockSimulationResult {
  const steps = clampInteger(form.steps, 10, 600);
  const paths = clampInteger(form.paths, 50, 5000);
  const initialPrice = Math.max(form.initialPrice, 1);
  const drift = form.drift;
  const volatility = Math.max(form.volatility, 0.0001);
  const horizon = Math.max(form.horizon, 0.05);
  const dt = horizon / steps;

  let seed = 20260322;
  const random = () => {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  };

  const normal = () => {
    const u1 = Math.max(random(), 1e-12);
    const u2 = random();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };

  const pathStore: number[][] = Array.from({ length: Math.min(paths, 6) }, () => new Array(steps + 1).fill(initialPrice));
  const terminalPrices: number[] = [];

  for (let pathIndex = 0; pathIndex < paths; pathIndex += 1) {
    let price = initialPrice;
    for (let stepIndex = 1; stepIndex <= steps; stepIndex += 1) {
      const shock = normal();
      price *= Math.exp((drift - 0.5 * volatility * volatility) * dt + volatility * Math.sqrt(dt) * shock);
      if (pathIndex < pathStore.length) {
        pathStore[pathIndex][stepIndex] = price;
      }
    }
    terminalPrices.push(price);
  }

  const samplePathData = Array.from({ length: steps + 1 }, (_, stepIndex) => {
    const row: Record<string, number | string> = { step: stepIndex };
    pathStore.forEach((path, pathIndex) => {
      row[`Path ${pathIndex + 1}`] = path[stepIndex];
    });
    return row;
  });

  return {
    samplePathData,
    terminalHistogram: buildHistogram(terminalPrices, 12),
    summary: buildSummary(terminalPrices),
  };
}

function computeOptionPricing(form: OptionFormState): OptionPricingResult {
  const spot = Math.max(form.spot, 1);
  const strike = Math.max(form.strike, 1);
  const maturity = Math.max(form.maturity, 0.01);
  const volatility = Math.max(form.volatility, 0.0001);
  const rate = form.rate;

  const start = Math.max(spot * 0.4, strike * 0.4, 10);
  const end = Math.max(spot * 1.8, strike * 1.8, start + 10);
  const curve = Array.from({ length: 40 }, (_, index) => {
    const currentSpot = start + ((end - start) * index) / 39;
    const { call, put } = blackScholes(currentSpot, strike, maturity, rate, volatility);
    return {
      spot: Number(currentSpot.toFixed(2)),
      callPrice: call,
      putPrice: put,
      callPayoff: Math.max(currentSpot - strike, 0),
      putPayoff: Math.max(strike - currentSpot, 0),
    };
  });

  const atSpot = blackScholes(spot, strike, maturity, rate, volatility);
  const intrinsicCall = Math.max(spot - strike, 0);
  const intrinsicPut = Math.max(strike - spot, 0);

  return {
    curve,
    summary: {
      callAtSpot: atSpot.call,
      putAtSpot: atSpot.put,
      intrinsicCall,
      intrinsicPut,
      timeValueCall: Math.max(atSpot.call - intrinsicCall, 0),
      timeValuePut: Math.max(atSpot.put - intrinsicPut, 0),
      greeks: computeLocalGreeks(spot, strike, maturity, rate, volatility),
    },
  };
}

function computeOptionPricing2D(form: Option2DFormState): Option2DPricingResult {
  const spot1 = Math.max(form.spot1, 1);
  const spot2 = Math.max(form.spot2, 1);
  const strike = Math.max(form.strike, 1);
  const maturity = Math.max(form.maturity, 0.01);
  const volatility1 = Math.max(form.volatility1, 0.0001);
  const volatility2 = Math.max(form.volatility2, 0.0001);
  const correlation = Math.max(Math.min(form.correlation, 0.999), -0.999);
  const gridSize = clampInteger(form.gridSize, 8, 32);
  const effectiveVolatility = Math.sqrt(
    (volatility1 * volatility1 + volatility2 * volatility2 + 2 * correlation * volatility1 * volatility2) / 4,
  );

  const s1Start = Math.max(Math.min(spot1, strike) * 0.4, 10);
  const s1End = Math.max(Math.max(spot1, strike) * 1.8, s1Start + 10);
  const s2Start = Math.max(Math.min(spot2, strike) * 0.4, 10);
  const s2End = Math.max(Math.max(spot2, strike) * 1.8, s2Start + 10);

  const xValues = Array.from({ length: gridSize }, (_, index) => Number((s1Start + ((s1End - s1Start) * index) / (gridSize - 1)).toFixed(2)));
  const yValues = Array.from({ length: gridSize }, (_, index) => Number((s2Start + ((s2End - s2Start) * index) / (gridSize - 1)).toFixed(2)));

  const surface: number[] = [];
  yValues.forEach((s2Value) => {
    xValues.forEach((s1Value) => {
      const basketSpot = 0.5 * (s1Value + s2Value);
      surface.push(blackScholes(basketSpot, strike, maturity, form.rate, effectiveVolatility).call);
    });
  });

  const basketSpot = 0.5 * (spot1 + spot2);
  const callAtCurrentPair = blackScholes(basketSpot, strike, maturity, form.rate, effectiveVolatility).call;

  return {
    surface,
    xValues,
    yValues,
    summary: {
      effectiveVolatility,
      basketSpot,
      callAtCurrentPair,
      surfaceMin: Math.min(...surface),
      surfaceMax: Math.max(...surface),
    },
  };
}

function blackScholes(spot: number, strike: number, maturity: number, rate: number, volatility: number) {
  const sqrtT = Math.sqrt(maturity);
  const d1 = (Math.log(spot / strike) + (rate + 0.5 * volatility * volatility) * maturity) / (volatility * sqrtT);
  const d2 = d1 - volatility * sqrtT;
  const nd1 = normalCdf(d1);
  const nd2 = normalCdf(d2);
  const discountedStrike = strike * Math.exp(-rate * maturity);

  const call = spot * nd1 - discountedStrike * nd2;
  const put = discountedStrike * normalCdf(-d2) - spot * normalCdf(-d1);

  return {
    call,
    put,
  };
}

function computeLocalGreeks(spot: number, strike: number, maturity: number, rate: number, volatility: number) {
  const sqrtT = Math.sqrt(maturity);
  const d1 = (Math.log(spot / strike) + (rate + 0.5 * volatility * volatility) * maturity) / (volatility * sqrtT);
  const d2 = d1 - volatility * sqrtT;
  const pdfD1 = normalPdf(d1);
  const nd1 = normalCdf(d1);
  const nd2 = normalCdf(d2);
  const gamma = pdfD1 / (spot * volatility * sqrtT);
  const vega = spot * pdfD1 * sqrtT;
  const callTheta = -(spot * pdfD1 * volatility) / (2 * sqrtT) - rate * strike * Math.exp(-rate * maturity) * nd2;
  const putTheta = -(spot * pdfD1 * volatility) / (2 * sqrtT) + rate * strike * Math.exp(-rate * maturity) * normalCdf(-d2);
  const callRho = strike * maturity * Math.exp(-rate * maturity) * nd2;
  const putRho = -strike * maturity * Math.exp(-rate * maturity) * normalCdf(-d2);

  return {
    call: {
      delta: nd1,
      gamma,
      theta: callTheta,
      vega,
      rho: callRho,
    },
    put: {
      delta: nd1 - 1,
      gamma,
      theta: putTheta,
      vega,
      rho: putRho,
    },
  };
}

function normalCdf(x: number) {
  return 0.5 * (1 + erf(x / Math.sqrt(2)));
}

function normalPdf(x: number) {
  return Math.exp((-0.5) * x * x) / Math.sqrt(2 * Math.PI);
}

function erf(x: number) {
  const sign = x < 0 ? -1 : 1;
  const value = Math.abs(x);
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;
  const t = 1 / (1 + p * value);
  const y = 1 - (((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-value * value));
  return sign * y;
}

function buildSummary(values: number[]): SummaryStats {
  const sorted = [...values].sort((a, b) => a - b);
  const mean = sorted.reduce((sum, value) => sum + value, 0) / sorted.length;
  const variance = sorted.reduce((sum, value) => sum + (value - mean) ** 2, 0) / sorted.length;

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    mean,
    std: Math.sqrt(variance),
    p05: percentile(sorted, 0.05),
    median: percentile(sorted, 0.5),
    p95: percentile(sorted, 0.95),
  };
}

function buildHistogram(values: number[], bins: number) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const width = Math.max((max - min) / bins, 1e-6);
  const counts = new Array(bins).fill(0);

  values.forEach((value) => {
    const index = Math.min(Math.floor((value - min) / width), bins - 1);
    counts[index] += 1;
  });

  return counts.map((count, index) => {
    const start = min + index * width;
    const end = start + width;
    return {
      bin: `${start.toFixed(0)}-${end.toFixed(0)}`,
      count,
    };
  });
}

function percentile(sortedValues: number[], ratio: number) {
  const index = ratio * (sortedValues.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) {
    return sortedValues[lower];
  }
  const weight = index - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function clampInteger(value: number, min: number, max: number) {
  return Math.min(Math.max(Math.round(value), min), max);
}

```
