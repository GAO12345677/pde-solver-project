import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SolvePage from '../pages/SolvePage';
import { api } from '../services/api';

vi.mock('../services/api', () => ({
  api: {
    solve: vi.fn(),
    extractFeature: vi.fn(),
    selectAlgorithm: vi.fn(),
    getSupportedEquations: vi.fn().mockResolvedValue({
      status: 'ok',
      success: true,
      error: null,
      data: {
        equations: {
          heat1d: { name: 'heat1d', algorithms: ['fdm', 'fvm', 'fem', 'spectral', 'pinn'], strategies: [], note: '' },
          heat2d: { name: 'heat2d', algorithms: ['fdm', 'fvm', 'fem'], strategies: [], note: '' },
          heat3d: { name: 'heat3d', algorithms: ['fdm', 'fvm', 'fem'], strategies: [], note: '' },
          wave1d: { name: 'wave1d', algorithms: ['fdm', 'fem', 'spectral'], strategies: [], note: '' },
          wave2d: { name: 'wave2d', algorithms: ['fdm', 'fem', 'spectral'], strategies: [], note: '' },
          wave3d: { name: 'wave3d', algorithms: ['fdm', 'fem', 'spectral'], strategies: [], note: '' },
          poisson1d: { name: 'poisson1d', algorithms: ['fdm', 'fem', 'spectral', 'bem'], strategies: [], note: '' },
          poisson3d: { name: 'poisson3d', algorithms: ['fdm', 'fem', 'bem'], strategies: [], note: '' },
          poisson2d_nonlinear: { name: 'poisson2d_nonlinear', algorithms: ['fdm'], strategies: [], note: '' },
        },
      },
    }),
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

  const renderSolvePage = async () => {
    render(<SolvePage />);
    await waitFor(() => {
      expect(api.getSupportedEquations).toHaveBeenCalled();
    });
  };

  it('renders the page shell', async () => {
    await renderSolvePage();

    expect(screen.getByRole('heading', { name: /PDE Solver/ })).toBeInTheDocument();
    expect(screen.getByText('Solve Parameters')).toBeInTheDocument();
  });

  it('renders equation and algorithm selectors', async () => {
    await renderSolvePage();

    expect(screen.getByLabelText('Equation Type')).toHaveValue('heat1d');
    expect(screen.getByLabelText('Algorithm')).toHaveValue('fdm');
  });

  it('updates numeric inputs', async () => {
    await renderSolvePage();

    const nxInput = screen.getByLabelText('Grid Points (nx)');
    fireEvent.change(nxInput, { target: { value: '201' } });

    await waitFor(() => {
      expect(nxInput).toHaveValue(201);
    });
  });

  it('calls solve when the solve button is clicked', async () => {
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

    await renderSolvePage();
    fireEvent.click(screen.getByRole('button', { name: /Start Solve/i }));

    await waitFor(() => {
      expect(api.solve).toHaveBeenCalled();
    });
  });

  it('requests the full solution for 3d equations', async () => {
    vi.mocked(api.solve).mockResolvedValue({
      status: 'ok',
      success: true,
      error: null,
      data: {
        solve_info: {
          algorithm: 'fdm',
          elapsed_s: 0.01,
          nfev: 12,
          status: 'ok',
        },
        solution_preview: {
          count: 27,
          head: [0, 0, 0],
          tail: [0, 0, 0],
          stats: { min: 0, max: 1, mean: 0.2, std: 0.1 },
        },
        solution: Array.from({ length: 27 }, (_, index) => index / 10),
      },
    });

    await renderSolvePage();
    fireEvent.change(screen.getByLabelText('Equation Type'), { target: { value: 'heat3d' } });
    fireEvent.change(screen.getByLabelText('Grid Points (nx)'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Grid Points (ny)'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Grid Points (nz)'), { target: { value: '3' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Solve/i }));

    await waitFor(() => {
      expect(api.solve).toHaveBeenCalledWith(
        expect.objectContaining({ equation_type: 'heat3d', return_full_solution: true }),
      );
    });
  });

  it('shows the 3d slice controls after solving a 3d case', async () => {
    vi.mocked(api.solve).mockResolvedValue({
      status: 'ok',
      success: true,
      error: null,
      data: {
        solve_info: {
          algorithm: 'fdm',
          elapsed_s: 0.01,
          nfev: 12,
          status: 'ok',
        },
        solution_preview: {
          count: 27,
          head: [0, 0, 0],
          tail: [0, 0, 0],
          stats: { min: 0, max: 1, mean: 0.2, std: 0.1 },
        },
        solution: Array.from({ length: 27 }, (_, index) => index / 10),
      },
    });

    await renderSolvePage();
    fireEvent.change(screen.getByLabelText('Equation Type'), { target: { value: 'heat3d' } });
    fireEvent.change(screen.getByLabelText('Grid Points (nx)'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Grid Points (ny)'), { target: { value: '3' } });
    fireEvent.change(screen.getByLabelText('Grid Points (nz)'), { target: { value: '3' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Solve/i }));

    await waitFor(() => {
      expect(screen.getByLabelText('Slice Axis')).toBeInTheDocument();
      expect(screen.getByLabelText('Slice Index')).toBeInTheDocument();
    });
  });
});
