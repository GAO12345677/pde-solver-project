export interface SolveRequest {
  equation_type: 'heat1d' | 'poisson2d_nonlinear';
  accuracy: 'high' | 'medium' | 'low';
  realtime: 'high' | 'medium' | 'low';
  resource_budget: number;
  boundary_condition: 'dirichlet' | 'neumann' | 'mixed';
  nx?: number;
  ny?: number;
  k?: number;
  L?: number;
  t0?: number;
  t1?: number;
  left_bc?: number;
  right_bc?: number;
  algorithm_key?: 'fdm' | 'fem' | 'spectral';
  return_full_solution?: boolean;
}

export interface SolveResponse {
  status: string;
  success: boolean;
  error: any;
  data: {
    solve_info: {
      algorithm: string;
      elapsed_s: number;
      nfev: number;
      status: string;
      estimated_error?: number;
      resource_proxy?: number;
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
  equation_type: 'heat1d' | 'poisson2d_nonlinear';
  accuracy: 'high' | 'medium' | 'low';
  realtime: 'high' | 'medium' | 'low';
  resource_budget: number;
  boundary_condition: 'dirichlet' | 'neumann' | 'mixed';
  nx?: number;
  ny?: number;
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
  strategy: 'static_rf' | 'static_xgb' | 'dynamic_rl';
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
