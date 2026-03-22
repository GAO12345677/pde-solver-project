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
