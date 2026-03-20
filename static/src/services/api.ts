import type {
  SolveRequest,
  SolveResponse,
  FeatureExtractionRequest,
  FeatureExtractionResponse,
  AlgorithmSelectionRequest,
  AlgorithmSelectionResponse,
  LLMConfig,
  LLMQuota,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function buildApiUrl(endpoint: string): string {
  if (!API_BASE_URL) {
    return endpoint;
  }
  return `${API_BASE_URL}${endpoint}`;
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
    const error = await response.json().catch(() => ({ message: '请求失败' }));
    throw new Error(error.message || `HTTP ${response.status}`);
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
      console.log('testConfig - 发送的 config 对象:', JSON.stringify(config, null, 2));
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
};
