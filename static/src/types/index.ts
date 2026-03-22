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
  model_id?: string;  // 火山方舟模型名称，例如：doubao-seed-1-8-251228
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
