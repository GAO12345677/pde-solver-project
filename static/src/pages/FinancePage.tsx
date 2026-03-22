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
import { ChartCard, ErrorPanel, MetricCard, StatusBadge } from '../components/FinanceWidgets';
import Heatmap from '../components/Heatmap';
import '../styles/finance.css';

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
    label: 'Initial Price 初始价格',
    note: '股票或指数在起点时刻的价格，也是整段模拟的起始值。',
  },
  {
    key: 'drift',
    label: 'Drift 漂移率',
    note: '表示价格长期平均增长趋势，可粗略理解为平均向上增长的倾向。',
  },
  {
    key: 'volatility',
    label: 'Volatility 波动率',
    note: '表示价格上下起伏的强度，是风险和不确定性的核心来源。',
  },
  {
    key: 'horizon',
    label: 'Horizon 时间范围',
    note: '表示向未来模拟多久，默认 1 代表 1 年。',
  },
  {
    key: 'steps',
    label: 'Steps 时间步数',
    note: '把整个时间区间切成多少个离散步，步数越多，路径越平滑。',
  },
  {
    key: 'paths',
    label: 'Paths 路径数',
    note: '蒙特卡洛样本数，越大统计越稳定，但计算量也会上升。',
  },
] as const;

const OPTION_INPUTS = [
  {
    key: 'spot',
    label: 'Spot Price 标的价格',
    note: '当前股票价格，是期权定价的起点。',
  },
  {
    key: 'strike',
    label: 'Strike 行权价',
    note: '约定的买卖价格，决定期权收益的关键阈值。',
  },
  {
    key: 'maturity',
    label: 'Maturity 到期时间',
    note: '从现在到合约到期还剩多久，单位这里按年处理。',
  },
  {
    key: 'volatility',
    label: 'Volatility 波动率',
    note: '控制未来价格不确定性的强度，是 Black-Scholes 的关键输入。',
  },
  {
    key: 'rate',
    label: 'Risk-free Rate 无风险利率',
    note: '常用的贴现率参数，用来把未来收益折算回现在。',
  },
] as const;

const OPTION_2D_INPUTS = [
  { key: 'spot1', label: 'Asset 1 Spot 资产1价格', note: '第一只资产当前价格。' },
  { key: 'spot2', label: 'Asset 2 Spot 资产2价格', note: '第二只资产当前价格。' },
  { key: 'strike', label: 'Strike 行权价', note: '二维篮子期权近似中的共同阈值。' },
  { key: 'maturity', label: 'Maturity 到期时间', note: '从现在到合约到期还剩多久。' },
  { key: 'volatility1', label: 'Vol 1 资产1波动率', note: '第一只资产的波动率。' },
  { key: 'volatility2', label: 'Vol 2 资产2波动率', note: '第二只资产的波动率。' },
  { key: 'correlation', label: 'Correlation 相关系数', note: '两只资产同涨同跌的联动强弱。' },
  { key: 'gridSize', label: 'Grid Size 网格大小', note: '二维价格曲面离散精度。' },
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
        title: 'Stocks 股票演化',
        subtitle: '先从股票价格路径和终点分布入手，更贴近随机过程和扩散的直觉。',
      };
    }

    return {
      title: 'Options 期权定价',
      subtitle: '把金融 PDE 应用扩展到 Black-Scholes 1D，并用图表解释价格和收益。',
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
    <div className="finance-dashboard-bg min-h-screen pb-12">
      <div className="mx-auto max-w-7xl space-y-6 p-6">
      <section className="dash-card rounded-lg border border-gray-200 bg-white/95 p-6 shadow-sm backdrop-blur-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-4xl">
            <h1 className="text-3xl font-bold text-gray-900">
              Finance Module <span className="text-lg font-medium text-gray-500">金融实践板块</span>
            </h1>
            <p className="mt-3 text-gray-600">
              Use finance as an application extension of the PDE platform without replacing the thesis core.
              <span className="block text-sm text-gray-500">
                这里把金融作为应用案例扩展，而不是替代原有的 `heat / wave / poisson` 主线。
              </span>
            </p>
            <p className="mt-3 text-sm text-gray-500">
              中文说明：建议先做 `Stocks`，因为它更接近随机过程和扩散的物理直觉；再做 `Options`，因为它更贴近标准金融 PDE。
            </p>
          </div>
          <div className="rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <div className="flex items-center gap-2 font-semibold">
              <Landmark className="h-4 w-4" />
              Module status 模块状态
            </div>
            <p className="mt-2">Stocks and Options first versions are both interactive now.</p>
            <p className="mt-1">股票和期权两个子板块现在都已经进入“可运行、可展示”的第一版状态。</p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SummaryCard
          icon={<CandlestickChart className="h-5 w-5" />}
          title="Stocks First"
          subtitle="先做股票演化"
          description="Build intuition with price paths, terminal distribution, and Monte Carlo statistics."
        />
        <SummaryCard
          icon={<CircleDollarSign className="h-5 w-5" />}
          title="Options Next"
          subtitle="再做期权定价"
          description="Move into Black-Scholes 1D and use price/payoff charts to explain the contract value."
        />
        <SummaryCard
          icon={<BarChart3 className="h-5 w-5" />}
          title="Thesis Safe"
          subtitle="不偏离论文主线"
          description="Finance remains a separate application area under the same numerical-analysis framework."
        />
      </section>

      <section className="dash-card rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap gap-3">
          <TabButton active={tab === 'stocks'} onClick={() => setTab('stocks')}>
            Stocks 股票演化
          </TabButton>
          <TabButton active={tab === 'options'} onClick={() => setTab('options')}>
            Options 期权定价
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
  let marketStatus: 'loading' | 'live' | 'fallback' | 'error' | 'offline' = 'offline';
  let marketText = 'Standby';

  if (aShareLoading) {
    marketStatus = 'loading';
    marketText = 'Fetching Data';
  } else if (aShareError) {
    marketStatus = 'error';
    marketText = 'Source Error';
  } else if (aShareState) {
    if (aShareState.realtimeAvailable === false) {
      marketStatus = 'fallback';
      marketText = 'History Fallback';
    } else {
      marketStatus = 'live';
      marketText = aShareState.marketClock.phaseLabel || 'Live';
    }
  }

  return (
    <div className="mt-6 space-y-6">
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <InfoCard
          title="What this module does 这个板块做什么"
          icon={<CandlestickChart className="h-5 w-5 text-blue-600" />}
        >
          It simulates stock-price evolution, sample paths, and terminal-price distributions using a geometric-Brownian-motion baseline.
          <span className="block text-sm text-gray-500">
            这一块主要做股票价格路径、终点分布和基础风险统计，不强调荐股，而是强调“价格如何演化”。
          </span>
        </InfoCard>
        <InfoCard
          title="Why it fits physics 为什么适合物理背景"
          icon={<Sparkles className="h-5 w-5 text-amber-600" />}
        >
          The stock demo can be explained through diffusion, random walks, and stochastic processes.
          <span className="block text-sm text-gray-500">
            它和扩散、随机游走、概率分布演化很接近，适合作为金融板块的第一站。
          </span>
        </InfoCard>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="dash-card rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share Live Analysis <span className="text-base font-medium text-gray-500">A股实时分析</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Load one A-share code, inspect market session status, latest quote fields, and historical volatility based on recent trading history.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：这一块优先面向 A 股日常分析，不直接给买卖建议，而是强调“当前市场状态是什么、最新价格来自哪里、近期波动率有多高”。
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 股票代码</span>
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
              <span className="mb-2 block text-sm font-medium text-gray-700">Lookback Days 回看天数</span>
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
              <span className="font-medium text-gray-900">Use history-only mode 只用历史日线模式</span>
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
            {aShareLoading ? 'Loading A-share... 正在加载A股数据' : 'Load A-share Analysis 加载A股分析'}
          </button>

          <ErrorPanel error={aShareError} />

          <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Reliability note 可靠性说明</p>
            <p className="mt-2">
              During active sessions, the latest price is closer to a live quote; outside active sessions, it should be read as the latest available market quote or latest completed trading session reference.
            </p>
            <p className="mt-2">
              中文说明：A股有固定交易时段，午休、收盘后、周末和节假日都不会产生新的连续竞价数据，所以页面会把“市场状态”和“时间戳”一起显示出来。
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="dash-card rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  Live Snapshot 实时快照
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  {aShareState ? `${aShareState.name} (${aShareState.symbol})` : 'Waiting for A-share data...'}
                </p>
              </div>
              <StatusBadge status={marketStatus} text={marketText} />
            </div>

            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Latest 最新价" value={aShareState?.latestPrice} note="Latest available quote from the current or most recent session." loading={aShareLoading} />
              <MetricCard label="Prev Close 昨收" value={aShareState?.prevClose ?? aShareState?.latestClose} note="Reference close from the previous trading day." loading={aShareLoading} />
              <MetricCard label="Change % 涨跌幅" value={aShareState?.changePercent} note="Relative move against the previous close." loading={aShareLoading} />
              <MetricCard label="HV252 年化波动" value={aShareState?.volatility.hv252} note="Annualized volatility estimated from recent daily closes." loading={aShareLoading} />
              <MetricCard label="HV20 短窗波动" value={aShareState?.volatility.hv20} note="Short-window volatility for the last 20 trading days." loading={aShareLoading} />
              <MetricCard label="HV60 中窗波动" value={aShareState?.volatility.hv60} note="Medium-window volatility for the last 60 trading days." loading={aShareLoading} />
              <MetricCard label="Drift 年化漂移" value={aShareState?.annualizedDrift} note="Annualized mean log-return estimate from recent history." loading={aShareLoading} />
              <MetricCard label="Volume 总手" value={aShareState?.volume} note="Latest available turnover volume from the quote source." integer loading={aShareLoading} />
            </div>

            {aShareState ? (
              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Data source 数据源:</span> {aShareState.dataSource}</p>
                  <p className="mt-2">
                    <span className="font-semibold">Mode 当前模式:</span>{' '}
                    {aShareState.realtimeAvailable === false ? 'History fallback 历史日线回退模式' : 'Live quote 实时行情模式'}
                  </p>
                  <p className="mt-2"><span className="font-semibold">Market clock 市场时间:</span> {aShareState.marketClock.localTime}</p>
                  <p className="mt-2"><span className="font-semibold">Latest trade date 最近交易日:</span> {aShareState.latestTradeDate}</p>
                  <p className="mt-2"><span className="font-semibold">Quote timestamp 报价时间:</span> {aShareState.quoteTimestamp ?? 'N/A'}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Open / High / Low:</span> {formatMetricValue(aShareState.open)} / {formatMetricValue(aShareState.high)} / {formatMetricValue(aShareState.low)}</p>
                  <p className="mt-2"><span className="font-semibold">Average price 均价:</span> {formatMetricValue(aShareState.averagePrice)}</p>
                  <p className="mt-2"><span className="font-semibold">Change amount 涨跌额:</span> {formatMetricValue(aShareState.changeAmount)}</p>
                  <p className="mt-2"><span className="font-semibold">Amount 成交额:</span> {formatMetricValue(aShareState.amount, true)}</p>
                </div>
              </div>
            ) : null}

            {aShareState?.realtimeAvailable === false ? (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                <p className="font-semibold">Fallback mode 已切换到历史日线模式</p>
                <p className="mt-2">
                  Live quote source is temporarily unavailable, so this panel is currently using the latest daily close and recent history.
                </p>
                <p className="mt-2">
                  中文说明：实时盘口源暂时不可用，所以当前看到的是“历史日线回退模式”。波动率、近30日走势、最近交易日等分析仍然有效，但“最新价”此时更接近最近收盘价而不是盘中实时价。
                </p>
              </div>
            ) : null}

            {aShareError ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                实时行情源暂时不可用。你可以勾选 `Use history-only mode`，直接查看历史日线分析。
              </div>
            ) : null}

            {aShareState?.notes?.length ? (
              <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                <p className="font-semibold">Interpretation notes 解读提示</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {aShareState.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          <ChartCard
            title="Recent Close Trend 近30日收盘走势"
            note="This chart uses the latest daily closes, which makes it suitable for post-close analysis and stable volatility estimation."
            heightClass="h-[320px]"
            loading={aShareLoading}
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={aShareState?.historyPreview ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis label={{ value: 'Close 收盘价', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(2)} />
                <Line type="monotone" dataKey="close" stroke="#111827" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="dash-card rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share Pair Analysis <span className="text-base font-medium text-gray-500">A股双股票联动分析</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Compare two A-share stocks to see whether they move together, how strong the historical relationship is, and whether the correlation is stable or drifting.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：双股票不是要同时预测两只股票，而是看它们之间的联动关系，例如同板块股票是否常常一起涨跌，相关性是稳定还是在变化。
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 1 股票1</span>
              <input
                type="text"
                value={aSharePairForm.symbol1}
                onChange={(event) => onASharePairChange('symbol1', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm uppercase outline-none transition focus:border-blue-500"
                placeholder="000001"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Symbol 2 股票2</span>
              <input
                type="text"
                value={aSharePairForm.symbol2}
                onChange={(event) => onASharePairChange('symbol2', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm uppercase outline-none transition focus:border-blue-500"
                placeholder="600519"
              />
            </label>
            <label className="block md:col-span-2">
              <span className="mb-2 block text-sm font-medium text-gray-700">Lookback Days 回看天数</span>
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
            {aSharePairLoading ? 'Loading Pair Data... 正在加载双股票数据' : 'Load Pair Analysis 加载双股票分析'}
          </button>

          <ErrorPanel error={aSharePairError} />

          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
            <p className="font-semibold">How to read pair correlation 如何理解双股票相关性</p>
            <p className="mt-2">
              A high positive correlation means the two stocks often move in the same direction, while a lower or unstable rolling correlation suggests the relationship can weaken over time.
            </p>
            <p className="mt-2">
              中文说明：这里的相关性不是因果关系，只是统计上的“同涨同跌程度”。滚动相关系数用来观察这种联动是否一直稳定。
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-xl font-semibold text-gray-900">Pair Summary 双股票摘要</h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Correlation 相关系数" value={aSharePairState?.correlation} note="Overall historical co-movement across the selected lookback window." loading={aSharePairLoading} />
              <MetricCard label="HV252 股票1波动" value={aSharePairState?.hv252_1} note="Annualized volatility of the first stock." loading={aSharePairLoading} />
              <MetricCard label="HV252 股票2波动" value={aSharePairState?.hv252_2} note="Annualized volatility of the second stock." loading={aSharePairLoading} />
              <MetricCard label="Data Source 数据源" value={aSharePairState ? 1 : null} note={aSharePairState?.dataSource ?? 'Waiting for pair data.'} integer loading={aSharePairLoading} />
            </div>
            {aSharePairState ? (
              <p className="mt-4 text-sm text-gray-500">
                {aSharePairState.name1} ({aSharePairState.symbol1}) vs {aSharePairState.name2} ({aSharePairState.symbol2})
              </p>
            ) : null}
          </div>

          <ChartCard
            title="Dual Price Trend 双价格走势"
            note="Compare the most recent daily closes of the two selected A-share stocks."
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={aSharePairState?.pairHistory ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis yAxisId="left" label={{ value: 'Stock 1 股票1', angle: -90, position: 'insideLeft' }} />
                <YAxis yAxisId="right" orientation="right" label={{ value: 'Stock 2 股票2', angle: 90, position: 'insideRight' }} />
                <Tooltip formatter={(value: number) => value.toFixed(2)} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="close1" name={aSharePairState?.symbol1 ?? 'Stock 1'} stroke="#2563eb" strokeWidth={2.5} dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="close2" name={aSharePairState?.symbol2 ?? 'Stock 2'} stroke="#dc2626" strokeWidth={2.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Rolling Correlation 滚动相关系数"
            note="A 20-day rolling correlation helps show whether the relationship is strengthening, weakening, or drifting over time."
            heightClass="h-[300px]"
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={aSharePairState?.rollingCorrelation ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-1, 1]} label={{ value: 'Correlation 相关性', angle: -90, position: 'insideLeft' }} />
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
            Stock Inputs <span className="text-base font-medium text-gray-500">股票模拟参数</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：下面这些参数决定股票“平均向上漂移多少”和“上下波动多剧烈”，系统会据此自动生成样本路径与统计分布。
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
            {loading ? 'Running... 正在模拟' : 'Run Stock Simulation 运行股票模拟'}
          </button>

          {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}

          <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
            <p className="font-semibold">How to read it 怎么理解结果</p>
            <p className="mt-2">
              Sample paths show possible future trajectories, the terminal histogram shows where final prices cluster,
              and the summary cards give quick risk and spread references.
            </p>
            <p className="mt-2">
              中文说明：样本路径用于直观看“可能怎么走”，终点分布用于看“最后大概落在哪些价格区间”，统计摘要用于快速判断风险和离散程度。
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <ChartCard
            title="Sample Paths 样本路径"
            note="展示若干条模拟价格路径。每一条线代表一种可能的未来演化轨迹。"
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.samplePathData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" label={{ value: 'Step 时间步', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Price 价格', angle: -90, position: 'insideLeft' }} />
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
            title="Terminal Distribution 终点价格分布"
            note="柱状图表示所有模拟路径在结束时刻落入各个价格区间的次数。"
            heightClass="h-[300px]"
          >
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={result.terminalHistogram}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="bin" angle={-18} textAnchor="end" height={60} interval={0} />
                <YAxis label={{ value: 'Count 数量', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" name="Terminal count 终点数量" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Simulation Summary <span className="text-base font-medium text-gray-500">模拟摘要</span>
        </h2>
        <p className="text-sm text-gray-500">
          中文说明：这里统计的是所有终点价格，不是中间每一步的平均值，因此更适合回答“最后可能收在哪里”。
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Mean 均值" value={result.summary.mean} note="终点价格的平均水平。" />
          <MetricCard label="Std 标准差" value={result.summary.std} note="终点价格离散程度，越大表示风险越高。" />
          <MetricCard label="P05 5%分位" value={result.summary.p05} note="较悲观情形下的参考价格。" />
          <MetricCard label="P95 95%分位" value={result.summary.p95} note="较乐观情形下的参考价格。" />
          <MetricCard label="Median 中位数" value={result.summary.median} note="一半路径高于它，一半路径低于它。" />
          <MetricCard label="Min 最小值" value={result.summary.min} note="所有终点价格中的最低值。" />
          <MetricCard label="Max 最大值" value={result.summary.max} note="所有终点价格中的最高值。" />
          <MetricCard label="Paths 路径数" value={form.paths} note="当前用于统计的总模拟样本数。" integer />
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
          title="What this module does 这个板块做什么"
          icon={<CircleDollarSign className="h-5 w-5 text-green-600" />}
        >
          It introduces option pricing as a financial PDE application, starting from Black-Scholes 1D.
          <span className="block text-sm text-gray-500">
            你可以先把它理解成“以股票价格和时间为自变量，求一个金融合约价值”的 PDE 例子。
          </span>
        </InfoCard>
        <InfoCard
          title="Why it matters 为什么值得做"
          icon={<BarChart3 className="h-5 w-5 text-purple-600" />}
        >
          Option pricing is one of the most classical and explainable PDE applications in finance.
          <span className="block text-sm text-gray-500">
            它能体现数值方法、边界条件和参数敏感性的价值，也更适合写进学术展示。
          </span>
        </InfoCard>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
          <h2 className="text-2xl font-semibold text-gray-900">
            A-Share ETF Options <span className="text-base font-medium text-gray-500">A股ETF期权快照</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            Start with the most practical domestic derivative case: 50ETF options. This panel focuses on market snapshots, Greeks, and theory-vs-market reference rather than automated execution.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：这里优先做国内 ETF 期权，是因为它比个股期权更稳、更适合作为数值分析平台里的衍生品应用入口。
          </p>

          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Underlying 标的ETF</span>
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
              <span className="mb-2 block text-sm font-medium text-gray-700">Option Type 方向</span>
              <select
                value={aShareEtfOptionForm.optionType}
                onChange={(event) => onAShareEtfOptionInput('optionType', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="call">Call 认购</option>
                <option value="put">Put 认沽</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Expiry 到期日</span>
              <select
                value={aShareEtfOptionForm.expiry}
                onChange={(event) => onAShareEtfOptionInput('expiry', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="">Auto 自动</option>
                {(aShareEtfOptionState?.availableExpiries ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-gray-700">Strike 行权价</span>
              <select
                value={aShareEtfOptionForm.strike}
                onChange={(event) => onAShareEtfOptionInput('strike', event.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
              >
                <option value="">Auto 自动</option>
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
            {aShareEtfOptionLoading ? 'Loading ETF Option... 正在加载ETF期权' : 'Load ETF Option Snapshot 加载ETF期权快照'}
          </button>

          <ErrorPanel error={aShareEtfOptionError} />

          <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">How to read this 如何理解这一块</p>
            <p className="mt-2">
              `latest price` is the observed option quote, `theoretical value` is the pricing reference returned with the option data, and `pricing gap` helps you see how far the traded quote is from that theoretical reference.
            </p>
            <p className="mt-2">
              中文说明：这一块更像“市场快照 + 敏感性分析”，不是自动下单系统，也不是投资建议。
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="text-xl font-semibold text-gray-900">ETF Option Summary ETF期权摘要</h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Latest Price 最新价" value={aShareEtfOptionState?.latestPrice ?? 0} note="Observed option latest price." />
              <MetricCard label="Midpoint 中间价" value={aShareEtfOptionState?.midpoint ?? 0} note="Midpoint between bid and ask when both are available." />
              <MetricCard label="IV 隐含波动率" value={aShareEtfOptionState?.impliedVolatility ?? 0} note="Implied volatility from the option snapshot." />
              <MetricCard label="Gap 理论偏差" value={aShareEtfOptionState?.pricingGap ?? 0} note="Latest price minus theoretical value." />
              <MetricCard label="Delta" value={aShareEtfOptionState?.delta ?? 0} note="First-order sensitivity to the ETF price." />
              <MetricCard label="Gamma" value={aShareEtfOptionState?.gamma ?? 0} note="Rate of change of Delta." />
              <MetricCard label="Theta" value={aShareEtfOptionState?.theta ?? 0} note="Time-decay sensitivity." />
              <MetricCard label="Vega" value={aShareEtfOptionState?.vega ?? 0} note="Sensitivity to implied volatility." />
            </div>

            {aShareEtfOptionState ? (
              <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Underlying 标的:</span> {aShareEtfOptionState.underlyingName} ({aShareEtfOptionState.underlying})</p>
                  <p className="mt-2"><span className="font-semibold">Underlying price 标的最新价:</span> {formatMetricValue(aShareEtfOptionState.underlyingPrice)}</p>
                  <p className="mt-2"><span className="font-semibold">Prev close / Open:</span> {formatMetricValue(aShareEtfOptionState.underlyingPrevClose)} / {formatMetricValue(aShareEtfOptionState.underlyingOpen)}</p>
                  <p className="mt-2"><span className="font-semibold">High / Low:</span> {formatMetricValue(aShareEtfOptionState.underlyingHigh)} / {formatMetricValue(aShareEtfOptionState.underlyingLow)}</p>
                  <p className="mt-2"><span className="font-semibold">Underlying time 标的时间:</span> {aShareEtfOptionState.underlyingQuoteTime}</p>
                </div>
                <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
                  <p><span className="font-semibold">Contract 合约:</span> {aShareEtfOptionState.contractName}</p>
                  <p className="mt-2"><span className="font-semibold">Trading code 交易代码:</span> {aShareEtfOptionState.tradingCode}</p>
                  <p className="mt-2"><span className="font-semibold">Expiry / Strike:</span> {aShareEtfOptionState.expiry} / {formatMetricValue(aShareEtfOptionState.strike)}</p>
                  <p className="mt-2"><span className="font-semibold">Bid / Ask:</span> {formatMetricValue(aShareEtfOptionState.bid)} / {formatMetricValue(aShareEtfOptionState.ask)}</p>
                  <p className="mt-2"><span className="font-semibold">Quote time 报价时间:</span> {aShareEtfOptionState.quoteTime}</p>
                </div>
              </div>
            ) : null}

            {aShareEtfOptionState ? (
              <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                <p className="font-semibold">Interpretation notes 解读提示</p>
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
            Option Inputs <span className="text-base font-medium text-gray-500">期权定价参数</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：这一组参数是 Black-Scholes 1D 的第一版入口，先帮助你理解含义，再看价格曲线和收益函数。
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
            {loading ? 'Pricing... 正在定价' : 'Run Black-Scholes 1D 运行 Black-Scholes 1D'}
          </button>

          <ErrorPanel error={error} />

          <div className="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-900">
            <p className="font-semibold">How to read it 怎么理解期权图</p>
            <p className="mt-2">
              The price curve shows how a call or put changes when the spot price moves. The payoff curve shows the
              contract value at expiry, without time value.
            </p>
            <p className="mt-2">
              中文说明：价格曲线看的是“今天值多少钱”，收益曲线看的是“到期那一刻能赚多少”，两者的差别就是时间价值的一部分。
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <ChartCard
            title="Black-Scholes Price Curve 定价曲线"
            note="展示不同标的价格下，看涨期权和看跌期权的理论价格。"
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="spot" label={{ value: 'Spot 标的价格', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Option Price 期权价格', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(4)} />
                <Legend />
                <Line type="monotone" dataKey="callPrice" stroke="#16a34a" strokeWidth={2} dot={false} name="Call 看涨期权" />
                <Line type="monotone" dataKey="putPrice" stroke="#dc2626" strokeWidth={2} dot={false} name="Put 看跌期权" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Payoff Curve 收益曲线"
            note="展示到期时的合约收益，不包含到期前尚未实现的时间价值。"
            heightClass="h-[320px]"
          >
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={result.curve}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="spot" label={{ value: 'Spot 标的价格', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Payoff 收益', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value: number) => value.toFixed(4)} />
                <Legend />
                <Line type="monotone" dataKey="callPayoff" stroke="#0f766e" strokeWidth={2} dot={false} name="Call payoff 看涨收益" />
                <Line type="monotone" dataKey="putPayoff" stroke="#b91c1c" strokeWidth={2} dot={false} name="Put payoff 看跌收益" />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Pricing Summary <span className="text-base font-medium text-gray-500">定价摘要</span>
        </h2>
        <p className="text-sm text-gray-500">
          中文说明：下面的摘要默认看当前 `spot` 下的价格，并把内在价值和时间价值拆开，帮助你理解为什么“现在的价格”不等于“到期收益”。
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <MetricCard label="Call Price 看涨价格" value={result.summary.callAtSpot} note="当前标的价格下的看涨期权理论价格。" />
          <MetricCard label="Put Price 看跌价格" value={result.summary.putAtSpot} note="当前标的价格下的看跌期权理论价格。" />
          <MetricCard label="Call Intrinsic 看涨内在价值" value={result.summary.intrinsicCall} note="立即到期时看涨合约能兑现的价值。" />
          <MetricCard label="Put Intrinsic 看跌内在价值" value={result.summary.intrinsicPut} note="立即到期时看跌合约能兑现的价值。" />
          <MetricCard label="Call Time Value 看涨时间价值" value={result.summary.timeValueCall} note="看涨期权价格中超出内在价值的部分。" />
          <MetricCard label="Put Time Value 看跌时间价值" value={result.summary.timeValuePut} note="看跌期权价格中超出内在价值的部分。" />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold text-gray-900">
          Greeks Summary <span className="text-base font-medium text-gray-500">敏感性指标</span>
        </h2>
        <p className="text-sm text-gray-500">
          中文说明：Greeks 用来衡量期权价格对标的价格、波动率、时间和利率变化的敏感程度，是量化分析里非常常见的一组指标。
        </p>
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <GreekGroupCard
            title="Call Greeks 看涨期权 Greeks"
            values={result.summary.greeks.call}
          />
          <GreekGroupCard
            title="Put Greeks 看跌期权 Greeks"
            values={result.summary.greeks.put}
          />
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">
            Black-Scholes 2D <span className="text-base font-medium text-gray-500">双资产二维曲面</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            中文说明：这一块展示的是双资产、带相关性的 basket-style 近似曲面，用来帮助你理解二维金融 PDE 场景下价格如何随两个资产同时变化。
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
            <h3 className="text-lg font-semibold text-gray-900">2D Inputs 二维参数</h3>
            <p className="mt-2 text-sm text-gray-500">
              这里特别值得关注 `correlation`，它决定两只资产联动强弱，也会显著改变曲面形状。
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
              {option2DLoading ? 'Pricing 2D... 正在生成二维曲面' : 'Run Black-Scholes 2D 运行 Black-Scholes 2D'}
            </button>

            <ErrorPanel error={option2DError} />

            <div className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-900">
              <p className="font-semibold">Interpretation 结果解读</p>
              <p className="mt-2">
                Higher areas in the surface mean a more valuable basket-style call when the two assets jointly move into favorable regions.
              </p>
              <p className="mt-2">
                中文说明：热力图越亮，表示在对应 `资产1价格 + 资产2价格` 组合下，这个二维看涨合约越值钱。
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <ChartCard
              title="2D Price Surface 二维价格曲面"
              note="横轴和纵轴分别对应两只资产价格，颜色表示二维看涨价格高低。"
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
          <MetricCard label="Effective Vol 有效波动率" value={option2DResult.summary.effectiveVolatility} note="将两只资产和相关性折算后的等效波动水平。" />
          <MetricCard label="Basket Spot 篮子价格" value={option2DResult.summary.basketSpot} note="用两只资产当前价格构造的平均篮子价格。" />
          <MetricCard label="2D Call 当前二维价格" value={option2DResult.summary.callAtCurrentPair} note="当前资产组合下的二维看涨价格。" />
          <MetricCard label="Surface Range 曲面跨度" value={option2DResult.summary.surfaceMax - option2DResult.summary.surfaceMin} note="整张二维曲面从最低到最高的价格跨度。" />
        </div>
      </section>

      <section className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">
            Market Comparison <span className="text-base font-medium text-gray-500">模型与市场对比</span>
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            这里会从真实市场快照自动估计 `spot / historical volatility / risk-free rate`，并并排展示 `model price / market price / implied volatility / pricing gap`。
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.05fr_1.35fr]">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
            <h3 className="text-lg font-semibold text-gray-900">Live Market Inputs 实时市场输入</h3>
            <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Ticker 股票代码</span>
                <input
                  type="text"
                  value={marketCompareForm.symbol}
                  onChange={(event) => onMarketCompareInput('symbol', event.target.value.toUpperCase())}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition focus:border-blue-500"
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-gray-700">Option Type 期权方向</span>
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
                <span className="mb-2 block text-sm font-medium text-gray-700">Maturity Years 到期年限</span>
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
                Use market IV 使用市场隐含波动率
              </label>
            </div>

            <button
              onClick={onRunMarketComparison}
              disabled={marketLoading}
              className="mt-5 rounded-lg bg-slate-800 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-900"
            >
              {marketLoading ? 'Loading Market Data... 正在获取市场数据' : 'Load Market Comparison 加载市场对比'}
            </button>

            <ErrorPanel error={marketError} />

            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="font-semibold">Reliability Notice 可靠性声明</p>
              <p className="mt-2">This is model-based analysis, not investment advice.</p>
              <p className="mt-2">中文说明：这里展示的是模型估值和市场快照对比，仅供学习、研究和分析参考，不构成投资建议。</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <MetricCard label="Spot 现价" value={marketStockState?.spot ?? 0} note="最新股票价格快照。" />
              <MetricCard label="Hist Vol 历史波动率" value={marketStockState?.historicalVolatility ?? 0} note="由历史对数收益率估计得到。" />
              <MetricCard label="Risk-free 无风险利率" value={marketStockState?.riskFreeRate ?? 0} note="用于模型定价的利率代理值。" />
              <MetricCard label="Drift 漂移率" value={marketStockState?.drift ?? 0} note="由历史收益率年化得到的粗略漂移估计。" />
              <MetricCard label="Model Price 模型价格" value={marketCompareState?.modelPrice ?? 0} note="Black-Scholes 类模型给出的估值。" />
              <MetricCard label="Market Price 市场价格" value={marketCompareState?.marketPrice ?? 0} note="期权链快照中的市场价格近似。" />
              <MetricCard label="Implied Vol 隐含波动率" value={marketCompareState?.impliedVolatility ?? 0} note="来自市场期权链的隐含波动率字段。" />
              <MetricCard label="Pricing Gap 定价差" value={marketCompareState?.pricingGap ?? 0} note="模型价格减去市场价格，正值表示模型更贵。" />
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900">Market Snapshot 市场快照</h3>
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

function formatMetricValue(value: number | null | undefined, integer = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return 'N/A';
  }
  return integer ? `${Math.round(value)}` : value.toFixed(2);
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
    ['Delta', values.delta, '对标的价格变化最直接的敏感度。'],
    ['Gamma', values.gamma, '衡量 Delta 自身变化速度。'],
    ['Theta', values.theta, '衡量时间流逝对价格的影响。'],
    ['Vega', values.vega, '衡量波动率变化对价格的影响。'],
    ['Rho', values.rho, '衡量利率变化对价格的影响。'],
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
