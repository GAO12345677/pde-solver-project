import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ResultsPage from '../pages/ResultsPage';

vi.mock('../services/api', () => ({
  api: {
    getLatestBenchmark: vi.fn().mockResolvedValue({
      data: {
        path: 'benchmark/latest.json',
        report: {
          selector_accuracy: [
            {
              strategy: 'gnn_selector',
              accuracy: 0.92,
              num_test_samples: 50,
              details: {
                training_summary: {
                  epochs_run: 12,
                  best_epoch: 10,
                  best_val_loss: 0.0012,
                  early_stopped: true,
                },
              },
            },
          ],
          solver_accuracy: [
            {
              equation_type: 'wave3d',
              algorithm: 'spectral',
              l2_error: 0.001,
              linf_error: 0.002,
              elapsed_s: 0.01,
              solver_status: 'ok',
              details: {},
            },
          ],
          solver_sweeps: {
            wave3d: {
              spectral: {
                mean_l2_error: 0.001,
                max_l2_error: 0.002,
                mean_elapsed_s: 0.01,
              },
            },
          },
          notes: ['wave3d spectral baseline enabled'],
        },
      },
    }),
    getSupportedEquations: vi.fn().mockResolvedValue({
      data: {
        equations: {
          wave3d: {
            name: '3D wave equation',
            algorithms: ['fdm', 'fem', 'spectral'],
            strategies: ['static_rf', 'gnn_selector'],
            note: '3D wave methods are available.',
          },
        },
      },
    }),
  },
}));

describe('ResultsPage', () => {
  it('renders the bilingual benchmark shell', async () => {
    render(<ResultsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Benchmark Results/)).toBeInTheDocument();
    });

    expect(screen.getByText(/实验结果/)).toBeInTheDocument();
    expect(screen.getByText(/Current Coverage/)).toBeInTheDocument();
    expect(screen.getByText(/Selection Pipeline/)).toBeInTheDocument();
    expect(screen.getByText(/用户输入自然语言题目/)).toBeInTheDocument();
    expect(screen.getByText(/wave3d spectral baseline enabled/)).toBeInTheDocument();
  });
});
