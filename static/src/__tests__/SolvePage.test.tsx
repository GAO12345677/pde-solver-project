import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SolvePage from '../pages/SolvePage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    solve: vi.fn(),
  },
}));

vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    progress: 0,
    status: 'idle',
    result: null,
    error: null,
    connected: false,
    sendMessage: vi.fn(),
    disconnect: vi.fn(),
    reset: vi.fn(),
  }),
}));

vi.mock('../components/StatsChart', () => ({
  default: () => <div>StatsChart</div>,
}));

vi.mock('../components/SolutionChart', () => ({
  default: () => <div>SolutionChart</div>,
}));

vi.mock('../components/Heatmap', () => ({
  default: () => <div>Heatmap</div>,
}));

describe('SolvePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders solve page', () => {
    render(<SolvePage />);

    expect(screen.getByText('PDE 求解器')).toBeInTheDocument();
    expect(screen.getByText('求解参数')).toBeInTheDocument();
  });

  it('renders equation type selector', () => {
    render(<SolvePage />);

    const select = screen.getByLabelText('方程类型');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('heat1d');
  });

  it('renders algorithm selector', () => {
    render(<SolvePage />);

    const select = screen.getByLabelText('算法');
    expect(select).toBeInTheDocument();
    expect(select).toHaveValue('fdm');
  });

  it('updates params when inputs change', async () => {
    render(<SolvePage />);

    const nxInput = screen.getByLabelText('网格点数 (nx)');
    fireEvent.change(nxInput, { target: { value: '201' } });

    await waitFor(() => {
      expect(nxInput).toHaveValue(201);
    });
  });

  it('calls solve API when button clicked', async () => {
    vi.mocked(api.solve).mockResolvedValue({
      status: 'ok',
      success: true,
      error: null,
      data: {
        solve_info: {
          algorithm: 'fdm',
          elapsed_s: 0.0234,
          nfev: 100,
          status: 'success',
        },
        solution_preview: {
          count: 4,
          head: [0.0, 0.0012],
          tail: [0.0089, 0.0067],
          stats: {
            min: 0.0,
            max: 0.1234,
            mean: 0.0567,
            std: 0.0345,
          },
        },
        solution: [0.0, 0.0012, 0.0089, 0.0067],
      },
    });

    render(<SolvePage />);
    fireEvent.click(screen.getByText('开始求解'));

    await waitFor(() => {
      expect(api.solve).toHaveBeenCalled();
    });
  });
});
