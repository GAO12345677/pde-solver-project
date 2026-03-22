import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import FinancePage from '../pages/FinancePage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    finance: {
      simulateStocks: vi.fn().mockResolvedValue({
        data: {
          inputs: { initial_price: 100, drift: 0.08, volatility: 0.2, horizon: 1, steps: 252, paths: 2000 },
          sample_path_data: [
            { step: 0, 'Path 1': 100, 'Path 2': 100 },
            { step: 1, 'Path 1': 101, 'Path 2': 99 },
          ],
          terminal_histogram: [{ bin: '90-100', count: 12 }],
          summary: { min: 90, max: 120, mean: 103, std: 8, p05: 91, median: 102, p95: 118 },
        },
      }),
      priceBlackScholes1D: vi.fn().mockResolvedValue({
        data: {
          inputs: { spot: 100, strike: 105, maturity: 0.5, volatility: 0.25, rate: 0.02 },
          curve: [
            { spot: 80, callPrice: 1.2, putPrice: 24.1, callPayoff: 0, putPayoff: 25 },
            { spot: 100, callPrice: 5.8, putPrice: 9.7, callPayoff: 0, putPayoff: 5 },
          ],
          summary: {
            callAtSpot: 5.8,
            putAtSpot: 9.7,
            intrinsicCall: 0,
            intrinsicPut: 5,
            timeValueCall: 5.8,
            timeValuePut: 4.7,
            greeks: {
              call: { delta: 0.48, gamma: 0.02, theta: -8.1, vega: 24.5, rho: 21.0 },
              put: { delta: -0.52, gamma: 0.02, theta: -6.7, vega: 24.5, rho: -30.2 },
            },
          },
        },
      }),
      priceBlackScholes2D: vi.fn().mockResolvedValue({
        data: {
          inputs: {
            spot1: 100,
            spot2: 95,
            strike: 100,
            maturity: 0.5,
            volatility1: 0.25,
            volatility2: 0.22,
            rate: 0.02,
            correlation: 0.3,
            grid_size: 12,
          },
          surface: Array.from({ length: 144 }, (_, index) => index / 10),
          x_values: Array.from({ length: 12 }, (_, index) => 60 + index * 10),
          y_values: Array.from({ length: 12 }, (_, index) => 55 + index * 10),
          summary: { effectiveVolatility: 0.21, basketSpot: 97.5, callAtCurrentPair: 8.4, surfaceMin: 0.2, surfaceMax: 26.5 },
        },
      }),
      getStockMarketData: vi.fn().mockResolvedValue({
        data: {
          symbol: 'MSFT',
          spot: 123.45,
          historical_volatility: 0.28,
          drift: 0.11,
          risk_free_rate: 0.021,
          history_preview: [{ date: '2026-03-20', close: 123.45 }],
          data_source: 'yfinance',
        },
      }),
      getAshareStockData: vi.fn().mockResolvedValue({
        data: {
          symbol: '000001.SZ',
          raw_symbol: '000001',
          name: '平安银行',
          latest_price: 10.77,
          latest_close: 10.88,
          open: 10.87,
          high: 10.94,
          low: 10.76,
          prev_close: 10.88,
          average_price: 10.84,
          change_percent: -1.01,
          change_amount: -0.11,
          volume: 834083,
          amount: 903819000,
          quote_timestamp: '15:30:01',
          latest_trade_date: '2026-03-20',
          market_clock: {
            timezone: 'Asia/Shanghai',
            local_time: '2026-03-22 10:00:00',
            is_trading_day: false,
            market_open: false,
            phase: 'closed_non_trading_day',
            phase_label: 'Closed 非交易日',
          },
          volatility: { hv20: 0.18, hv60: 0.22, hv252: 0.25 },
          annualized_drift: 0.06,
          history_preview: [{ date: '2026-03-20', close: 10.88 }],
          data_source: 'akshare',
          notes: ['This module is for research and analysis, not investment advice.'],
        },
      }),
      getAsharePairData: vi.fn().mockResolvedValue({
        data: {
          symbol1: '000001.SZ',
          symbol2: '600519.SH',
          name1: '平安银行',
          name2: '贵州茅台',
          latest_price1: 10.77,
          latest_price2: 1520,
          correlation: 0.36,
          hv252_1: 0.25,
          hv252_2: 0.31,
          pair_history: [
            { date: '2026-03-19', close1: 10.9, close2: 1518 },
            { date: '2026-03-20', close1: 10.88, close2: 1520 },
          ],
          rolling_correlation: [{ date: '2026-03-20', correlation: 0.41 }],
          data_source: 'akshare',
        },
      }),
      getAshareEtfOptionData: vi.fn().mockResolvedValue({
        data: {
          underlying: '510050',
          available_expiries: ['20260325', '20260422'],
          available_strikes: [2.63, 2.68, 2.73],
          underlying_name: '上证50ETF',
          underlying_price: 2.957,
          underlying_prev_close: 2.993,
          underlying_open: 2.99,
          underlying_high: 3.001,
          underlying_low: 2.955,
          underlying_quote_time: '15:00:03',
          option_type: 'call',
          contract_code: '10009633',
          trading_code: '510050C2603A02700',
          contract_name: '50ETF购3月2630A',
          expiry: '20260325',
          strike: 2.63,
          latest_price: 0.33,
          bid: 0.327,
          ask: 0.33,
          midpoint: 0.3285,
          change_percent: -9.76,
          open_interest: 1007,
          volume: 141,
          quote_time: '2026-03-20 14:53:37',
          delta: 1,
          gamma: 0,
          theta: -0.1051,
          vega: 0,
          implied_volatility: 0.5124,
          theoretical_value: 0.3284,
          pricing_gap: 0.0016,
          moneyness: 0.327,
          data_source: 'akshare_sse_option',
          notes: ['This module is for learning and analysis, not investment advice.'],
        },
      }),
      getAshareIndexOptionData: vi.fn().mockResolvedValue({
        data: {
          market: 'hs300',
          market_name: 'HS300 Index Option',
          available_months: ['io2604', 'io2605'],
          available_strikes: [3800, 3850, 3900],
          contract_month: 'io2604',
          option_type: 'call',
          contract_code: 'IO2604-C-3900',
          strike: 3900,
          latest_price: 112.5,
          bid: 111.8,
          ask: 113.2,
          midpoint: 112.5,
          open_interest: 1245,
          change_amount: 8.2,
          data_source: 'akshare_hs300_index_option',
          notes: ['This module is for learning and analysis, not investment advice.'],
        },
      }),
      getPairMarketData: vi.fn().mockResolvedValue({
        data: {
          symbol1: 'MSFT',
          symbol2: 'AAPL',
          spot1: 123.45,
          spot2: 188.2,
          historical_volatility1: 0.28,
          historical_volatility2: 0.25,
          correlation: 0.42,
          data_source: 'yfinance',
        },
      }),
      compareOptionWithMarket: vi.fn().mockResolvedValue({
        data: {
          symbol: 'MSFT',
          spot: 123.45,
          expiry: '2026-06-19',
          strike: 125,
          option_type: 'call',
          market_price: 6.2,
          model_price: 5.8,
          implied_volatility: 0.31,
          risk_free_rate: 0.021,
          pricing_gap: -0.4,
          contract_symbol: 'MSFT260619C00125000',
          notes: ['This is model-based analysis, not investment advice.'],
        },
      }),
    },
  },
}));

vi.mock('../components/Heatmap', () => ({
  default: () => <div>Heatmap</div>,
}));

describe('FinancePage', () => {
  it('loads finance data from backend APIs and reruns both demos', async () => {
    render(<FinancePage />);

    expect(screen.getByText(/Finance Module/)).toBeInTheDocument();
    expect(screen.getByText(/金融实践板块/)).toBeInTheDocument();

    await waitFor(() => {
      expect(api.finance.getAshareStockData).toHaveBeenCalled();
      expect(api.finance.getAsharePairData).toHaveBeenCalled();
      expect(api.finance.getAshareEtfOptionData).toHaveBeenCalled();
      expect(api.finance.getAshareIndexOptionData).toHaveBeenCalled();
      expect(api.finance.simulateStocks).toHaveBeenCalled();
      expect(api.finance.priceBlackScholes1D).toHaveBeenCalled();
      expect(api.finance.priceBlackScholes2D).toHaveBeenCalled();
      expect(api.finance.getStockMarketData).toHaveBeenCalled();
      expect(api.finance.compareOptionWithMarket).toHaveBeenCalled();
    });

    expect(screen.getByText(/A-Share Live Analysis/)).toBeInTheDocument();
    expect(screen.getAllByText(/平安银行/).length).toBeGreaterThan(0);
    fireEvent.change(screen.getAllByDisplayValue('000001')[0], { target: { value: '600519' } });
    fireEvent.click(screen.getByRole('button', { name: /Load A-share Analysis/ }));

    await waitFor(() => {
      expect(api.finance.getAshareStockData).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByText(/A-Share Pair Analysis/)).toBeInTheDocument();
    expect(screen.getByText(/Rolling Correlation/)).toBeInTheDocument();
    fireEvent.change(screen.getAllByDisplayValue('600519')[1], { target: { value: '300750' } });
    fireEvent.click(screen.getByRole('button', { name: /Load Pair Analysis/ }));

    await waitFor(() => {
      expect(api.finance.getAsharePairData).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByText(/Stock Inputs/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Paths/), { target: { value: '800' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Stock Simulation/ }));

    await waitFor(() => {
      expect(api.finance.simulateStocks).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByText(/Simulation Summary/)).toBeInTheDocument();
    expect(screen.getByText(/Mean/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Options/ }));
    expect(screen.getByText(/A-Share ETF Options/)).toBeInTheDocument();
    expect(screen.getByText(/ETF Option Summary/)).toBeInTheDocument();

    const comboBoxes = screen.getAllByRole('combobox');
    fireEvent.change(comboBoxes[0], { target: { value: '510300' } });
    fireEvent.change(comboBoxes[1], { target: { value: 'put' } });
    fireEvent.change(comboBoxes[2], { target: { value: '20260422' } });
    fireEvent.change(comboBoxes[3], { target: { value: '2.68' } });
    fireEvent.click(screen.getByRole('button', { name: /Load ETF Option Snapshot/ }));

    await waitFor(() => {
      expect(api.finance.getAshareEtfOptionData).toHaveBeenCalledTimes(2);
    });

    expect(api.finance.getAshareIndexOptionData).toHaveBeenCalledTimes(1);

    expect(screen.getByText(/Option Inputs/)).toBeInTheDocument();
    fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '110' } });
    fireEvent.click(screen.getByRole('button', { name: /Run Black-Scholes 1D/ }));

    await waitFor(() => {
      expect(api.finance.priceBlackScholes1D).toHaveBeenCalledTimes(2);
    });

    expect(screen.getByText(/Pricing Summary/)).toBeInTheDocument();
    expect(screen.getByText(/Greeks Summary/)).toBeInTheDocument();
    expect(screen.getByText(/2D Price Surface/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Run Black-Scholes 2D/ }));

    await waitFor(() => {
      expect(api.finance.priceBlackScholes2D).toHaveBeenCalledTimes(2);
    });

    expect(screen.getAllByText(/Market Comparison/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Model Price/)).toBeInTheDocument();
    expect(screen.getByText(/Market Price/)).toBeInTheDocument();
    fireEvent.change(screen.getByDisplayValue('MSFT'), { target: { value: 'AAPL' } });
    fireEvent.click(screen.getByRole('button', { name: /Load Market Comparison/ }));

    await waitFor(() => {
      expect(api.finance.compareOptionWithMarket).toHaveBeenCalledTimes(2);
    });
  });
});
