import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, Cpu, GitBranch, Sigma, Timer } from 'lucide-react';
import { api } from '../services/api';
import type { BenchmarkReport, SupportedEquationsResponse } from '../types';

const STRATEGY_NAMES: Record<string, string> = {
  static_rf: 'Random Forest',
  static_xgb: 'XGBoost',
  dynamic_rl: 'Reinforcement Learning',
  mlp_nn: 'MLP Neural Network',
  gnn_selector: 'GNN Selector',
};

const EQUATION_NAMES: Record<string, string> = {
  heat1d: '1D Heat Equation',
  heat2d: '2D Heat Equation',
  heat3d: '3D Heat Equation',
  wave1d: '1D Wave Equation',
  wave2d: '2D Wave Equation',
  wave3d: '3D Wave Equation',
  poisson1d: '1D Poisson Equation',
  poisson3d: '3D Poisson Equation',
  poisson2d_nonlinear: '2D Nonlinear Poisson Equation',
};

const UNSUPPORTED_CASES = [
  'General mechanics problems that are not PDE-based. 非 PDE 的一般力学问题暂不在本平台范围内。',
  'Large multi-physics engineering problems with high-dimensional coupling. 高维强耦合多物理场工程问题暂不作为当前演示重点。',
  'Prompts that omit clear boundary or initial conditions. 如果题目没有明确边界条件或初始条件，系统通常无法稳定自动求解。',
];

const PIPELINE_STEPS = [
  'User prompt or structured PDE parameters. 用户输入自然语言题目，或直接填写结构化 PDE 参数。',
  'Feature extraction (physics + hardware + domain). 系统提取物理特征、硬件特征和问题域特征。',
  'AI selector (RF / XGB / RL / MLP / GNN). 算法选择器根据特征推荐更合适的求解方法。',
  'Recommended algorithm. 页面展示推荐算法，用户也可以手动覆盖和调整。',
  'Numerical solver execution. 后端数值求解器开始计算，并返回解、误差和耗时信息。',
  'Error and resource evaluation. 最终汇总误差、运行时间、训练摘要和支持范围，形成结果页面。',
];

const ZH = {
  benchmark: '\u5b9e\u9a8c\u7ed3\u679c',
  benchmarkIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u672c\u9875\u5c55\u793a\u7684\u662f\u6574\u4f53 benchmark \u6c47\u603b\uff0c\u7528\u6765\u8bf4\u660e\u7cfb\u7edf\u80fd\u529b\u3001\u7b97\u6cd5\u63a8\u8350\u8868\u73b0\u548c\u6c42\u89e3\u5668\u6548\u679c\uff0c\u800c\u4e0d\u662f\u67d0\u4e00\u6b21\u5355\u72ec\u6c42\u89e3\u7684\u8f93\u51fa\u3002',
  selector: '\u7b97\u6cd5\u9009\u62e9\u7cbe\u5ea6',
  selectorIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u8fd9\u91cc\u8861\u91cf\u7684\u662f\u201c\u63a8\u8350\u7b97\u6cd5\u6a21\u5757\u201d\u662f\u5426\u9009\u5bf9\u6c42\u89e3\u5668\uff0c\u4e0d\u662f\u6570\u503c\u89e3\u672c\u8eab\u7684\u8bef\u5dee\u3002',
  strategy: '\u7b56\u7565',
  accuracy: '\u7cbe\u5ea6',
  testSamples: '\u6837\u672c\u6570',
  trainingSummary: '\u8bad\u7ec3\u6458\u8981',
  solver: '\u6c42\u89e3\u5668\u8bef\u5dee\u4e0e\u8017\u65f6',
  solverIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u8fd9\u91cc\u76f4\u63a5\u6bd4\u8f83\u4e0d\u540c\u6570\u503c\u65b9\u6cd5\u7684\u8bef\u5dee\u548c\u8fd0\u884c\u65f6\u95f4\uff0c\u7528\u4e8e\u56de\u7b54\u201c\u54ea\u4e2a\u65b9\u6cd5\u66f4\u51c6\u3001\u66f4\u5feb\u201d\u3002',
  equation: '\u65b9\u7a0b',
  algorithm: '\u7b97\u6cd5',
  l2: '\u4e8c\u8303\u6570\u8bef\u5dee',
  linf: '\u6700\u5927\u8bef\u5dee',
  elapsed: '\u8017\u65f6',
  status: '\u72b6\u6001',
  notes: '\u5907\u6ce8',
  sweep: '\u5206\u8fa8\u7387\u626b\u63cf',
  sweepIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u8fd9\u91cc\u5c55\u793a\u7f51\u683c\u89c4\u6a21\u53d8\u5316\u540e\uff0c\u5404\u7b97\u6cd5\u8bef\u5dee\u548c\u8017\u65f6\u7684\u53d8\u5316\u8d8b\u52bf\u3002',
  coverage: '\u5f53\u524d\u652f\u6301\u8303\u56f4',
  coverageIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u8fd9\u91cc\u5217\u51fa\u7684\u90fd\u662f\u5f53\u524d\u5df2\u7ecf\u63a5\u901a\u524d\u540e\u7aef\u3001\u53ef\u4ee5\u5b9e\u9645\u8fd0\u884c\u7684\u65b9\u7a0b\u548c\u7b97\u6cd5\uff0c\u4e0d\u662f\u8ba1\u5212\u529f\u80fd\u3002',
  outOfScope: '\u6682\u4e0d\u652f\u6301',
  equationCardHint:
    '\u4e2d\u6587\u63d0\u793a\uff1a\u6bcf\u5f20\u5361\u7247\u5bf9\u5e94\u4e00\u7c7b PDE\uff0cAlgorithms \u662f\u5f53\u524d\u53ef\u9009\u6570\u503c\u65b9\u6cd5\uff0cStrategies \u662f\u53ef\u7528\u7684\u7b97\u6cd5\u63a8\u8350\u7b56\u7565\u3002',
  algorithmsLabel:
    '\u4e2d\u6587\u8bf4\u660e\uff1aAlgorithms \u8868\u793a\u4f60\u771f\u6b63\u53ef\u4ee5\u5728\u6c42\u89e3\u9875\u4e2d\u9009\u62e9\u7684\u6570\u503c\u65b9\u6cd5\u3002',
  strategiesLabel:
    '\u4e2d\u6587\u8bf4\u660e\uff1aStrategies \u8868\u793a\u7cfb\u7edf\u53ef\u4ee5\u7528\u54ea\u4e9b AI \u6216 ML \u7b56\u7565\u6765\u63a8\u8350\u7b97\u6cd5\u3002',
  pipeline: '\u7b97\u6cd5\u9009\u62e9\u6d41\u7a0b',
  pipelineIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u5c55\u793a\u4ece\u9898\u76ee\u8f93\u5165\u5230\u7b97\u6cd5\u63a8\u8350\u3001\u6570\u503c\u6c42\u89e3\u3001\u7ed3\u679c\u8bc4\u4f30\u7684\u5b8c\u6574\u7cfb\u7edf\u94fe\u8def\u3002',
  pipelineHint:
    '\u4e2d\u6587\u63d0\u793a\uff1aGNN \u66f4\u504f\u5411\u7b97\u6cd5\u63a8\u8350\uff0cPINN \u66f4\u504f\u5411 AI \u6c42\u89e3\u539f\u578b\uff0c\u5b83\u4eec\u548c\u4f20\u7edf\u6570\u503c\u6cd5\u662f\u4e92\u8865\u5173\u7cfb\u3002',
  benchmarkNotes: '\u5b9e\u9a8c\u8bf4\u660e',
  benchmarkNotesIntro:
    '\u4e2d\u6587\u8bf4\u660e\uff1a\u8fd9\u91cc\u8bb0\u5f55\u57fa\u51c6\u6d4b\u8bd5\u7684\u9644\u52a0\u8bf4\u660e\u3001\u5047\u8bbe\u6761\u4ef6\u548c\u5b9e\u9a8c\u5907\u6ce8\u3002',
};

interface BenchmarkState {
  report: BenchmarkReport | null;
  path: string | null;
}

export default function ResultsPage() {
  const [benchmark, setBenchmark] = useState<BenchmarkState>({ report: null, path: null });
  const [supported, setSupported] = useState<SupportedEquationsResponse['data']['equations'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [benchmarkResponse, supportedResponse] = await Promise.all([
          api.getLatestBenchmark(),
          api.getSupportedEquations(),
        ]);

        setBenchmark({
          report: benchmarkResponse.data.report,
          path: benchmarkResponse.data.path,
        });
        setSupported(supportedResponse.data.equations);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load benchmark results.');
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const gnnSummary = useMemo(() => {
    const row = benchmark.report?.selector_accuracy.find((item) => item.strategy === 'gnn_selector');
    return row?.details?.training_summary || row?.details?.train_info?.training_summary || null;
  }, [benchmark.report]);

  const pinnRow = useMemo(() => {
    return benchmark.report?.solver_accuracy.find((item) => item.equation_type === 'heat1d' && item.algorithm === 'pinn') || null;
  }, [benchmark.report]);

  const pinnSummary = useMemo(() => pinnRow?.details?.training_summary || null, [pinnRow]);

  if (loading) {
    return <PageState title="Results" description="Loading benchmark summaries and supported-equation metadata..." />;
  }

  if (error) {
    return <PageState title="Results" description={error} danger />;
  }

  const selectorRows = benchmark.report?.selector_accuracy ?? [];
  const solverRows = benchmark.report?.solver_accuracy ?? [];
  const sweepRows = benchmark.report?.solver_sweeps ?? {};

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between gap-6">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-gray-900">
              Benchmark Results <span className="text-lg font-medium text-gray-500">{ZH.benchmark}</span>
            </h1>
            <p className="text-gray-600">
              Review selector accuracy, solver error metrics, resolution sweeps, supported PDE coverage, and training summaries for the
              current GNN and PINN baselines.
            </p>
            <p className="mt-2 text-sm text-gray-500">{ZH.benchmarkIntro}</p>
          </div>
          <div className="text-right text-sm text-gray-500">
            <div>Source: latest benchmark report</div>
            <div className="mt-1 break-all">{benchmark.path || 'N/A'}</div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <SummaryCard icon={<Cpu className="h-5 w-5" />} label="Supported equations" value={String(Object.keys(supported || {}).length)} />
        <SummaryCard icon={<Sigma className="h-5 w-5" />} label="Selection strategies" value="RF / XGB / RL / MLP / GNN" />
        <SummaryCard icon={<Timer className="h-5 w-5" />} label="GNN epochs" value={gnnSummary ? String(gnnSummary.epochs_run) : 'N/A'} />
        <SummaryCard
          icon={<GitBranch className="h-5 w-5" />}
          label="Best GNN val loss"
          value={gnnSummary ? Number(gnnSummary.best_val_loss).toExponential(2) : 'N/A'}
        />
        <SummaryCard
          icon={<Timer className="h-5 w-5" />}
          label="PINN heat1d L2"
          value={pinnRow ? Number(pinnRow.l2_error).toExponential(2) : 'N/A'}
        />
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">
          Selector Accuracy <span className="text-sm font-medium text-gray-500">{ZH.selector}</span>
        </h2>
        <p className="mb-4 text-sm text-gray-500">{ZH.selectorIntro}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-600">
                <th className="py-3 pr-4">Strategy {ZH.strategy}</th>
                <th className="py-3 pr-4">Accuracy {ZH.accuracy}</th>
                <th className="py-3 pr-4">Test samples {ZH.testSamples}</th>
                <th className="py-3 pr-4">Training summary {ZH.trainingSummary}</th>
              </tr>
            </thead>
            <tbody>
              {selectorRows.map((row) => {
                const summary = row.details?.training_summary || row.details?.train_info?.training_summary;
                return (
                  <tr key={row.strategy} className="align-top border-b border-gray-100">
                    <td className="py-3 pr-4 font-medium text-gray-900">{STRATEGY_NAMES[row.strategy] || row.strategy}</td>
                    <td className="py-3 pr-4">{(row.accuracy * 100).toFixed(1)}%</td>
                    <td className="py-3 pr-4">{row.num_test_samples}</td>
                    <td className="py-3 pr-4 text-gray-600">
                      {summary ? (
                        <div className="space-y-1">
                          <div>epochs_run: {summary.epochs_run}</div>
                          <div>best_epoch: {summary.best_epoch}</div>
                          <div>best_val_loss: {Number(summary.best_val_loss).toExponential(2)}</div>
                          <div>early_stopped: {summary.early_stopped ? 'true' : 'false'}</div>
                        </div>
                      ) : (
                        <span>-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">
          Solver Error And Runtime <span className="text-sm font-medium text-gray-500">{ZH.solver}</span>
        </h2>
        <p className="mb-4 text-sm text-gray-500">{ZH.solverIntro}</p>
        {pinnSummary && (
          <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <div className="mb-1 font-semibold">PINN training summary</div>
            <div>Adam epochs: {pinnSummary.adam_epochs_run} / {pinnSummary.adam_epochs_configured}</div>
            <div>LBFGS steps: {pinnSummary.lbfgs_steps_run} / {pinnSummary.lbfgs_steps_configured}</div>
            <div>best_loss: {Number(pinnSummary.best_loss).toExponential(2)}</div>
            <div>early_stopped: {pinnSummary.early_stopped ? 'true' : 'false'}</div>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-gray-600">
                <th className="py-3 pr-4">Equation {ZH.equation}</th>
                <th className="py-3 pr-4">Algorithm {ZH.algorithm}</th>
                <th className="py-3 pr-4">L2 error {ZH.l2}</th>
                <th className="py-3 pr-4">L-infinity error {ZH.linf}</th>
                <th className="py-3 pr-4">Elapsed (s) {ZH.elapsed}</th>
                <th className="py-3 pr-4">Status {ZH.status}</th>
                <th className="py-3 pr-4">Notes {ZH.notes}</th>
              </tr>
            </thead>
            <tbody>
              {solverRows.map((row) => (
                <tr key={`${row.equation_type}-${row.algorithm}`} className="border-b border-gray-100">
                  <td className="py-3 pr-4 font-medium text-gray-900">{EQUATION_NAMES[row.equation_type] || row.equation_type}</td>
                  <td className="py-3 pr-4">{row.algorithm}</td>
                  <td className="py-3 pr-4">{Number(row.l2_error).toExponential(2)}</td>
                  <td className="py-3 pr-4">{Number(row.linf_error).toExponential(2)}</td>
                  <td className="py-3 pr-4">{row.elapsed_s.toFixed(6)}</td>
                  <td className="py-3 pr-4">{row.solver_status}</td>
                  <td className="py-3 pr-4 text-gray-600">
                    {row.algorithm === 'pinn' && row.details?.training_summary
                      ? `Adam ${row.details.training_summary.adam_epochs_run} / LBFGS ${row.details.training_summary.lbfgs_steps_run}`
                      : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">
          Resolution Sweep <span className="text-sm font-medium text-gray-500">{ZH.sweep}</span>
        </h2>
        <p className="mb-4 text-sm text-gray-500">{ZH.sweepIntro}</p>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          {Object.entries(sweepRows).map(([equationType, algorithms]) => (
            <div key={equationType} className="rounded-lg border border-gray-200 p-4">
              <h3 className="mb-3 font-semibold text-gray-900">{EQUATION_NAMES[equationType] || equationType}</h3>
              <div className="space-y-3">
                {Object.entries(algorithms as Record<string, any>).map(([algorithm, detail]) => (
                  <div key={algorithm} className="rounded-md bg-gray-50 p-3 text-sm">
                    <div className="mb-1 font-medium text-gray-900">{algorithm}</div>
                    <div className="text-gray-600">mean_L2: {Number(detail.mean_l2_error).toExponential(2)}</div>
                    <div className="text-gray-600">max_L2: {Number(detail.max_l2_error).toExponential(2)}</div>
                    <div className="text-gray-600">mean_elapsed: {Number(detail.mean_elapsed_s).toFixed(6)}s</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">
            Current Coverage <span className="text-sm font-medium text-gray-500">{ZH.coverage}</span>
          </h2>
          <p className="mb-4 text-sm text-gray-500">{ZH.coverageIntro}</p>
          <p className="mb-4 text-sm text-gray-500">{ZH.equationCardHint}</p>
          <div className="space-y-3">
            {supported &&
              Object.entries(supported).map(([key, value]) => (
                <div key={key} className="rounded-md border border-gray-200 p-4">
                  <div className="flex items-center gap-2 font-medium text-gray-900">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    {EQUATION_NAMES[key] || key}
                  </div>
                  <div className="mt-2 text-sm text-gray-600">Algorithms: {value.algorithms.join(' / ')}</div>
                  <div className="mt-1 text-xs text-gray-500">{ZH.algorithmsLabel}</div>
                  <div className="mt-1 text-sm text-gray-600">Strategies: {value.strategies.join(' / ')}</div>
                  <div className="mt-1 text-xs text-gray-500">{ZH.strategiesLabel}</div>
                  <div className="mt-1 text-sm text-gray-500">{value.note}</div>
                </div>
              ))}
          </div>
          <div className="mt-6">
            <h3 className="mb-3 font-medium text-gray-900">
              Still Out Of Scope <span className="text-sm font-medium text-gray-500">{ZH.outOfScope}</span>
            </h3>
            <div className="space-y-2">
              {UNSUPPORTED_CASES.map((item) => (
                <div key={item} className="flex items-center gap-2 text-sm text-gray-600">
                  <AlertCircle className="h-4 w-4 text-amber-500" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">
            Selection Pipeline <span className="text-sm font-medium text-gray-500">{ZH.pipeline}</span>
          </h2>
          <p className="mb-4 text-sm text-gray-500">{ZH.pipelineIntro}</p>
          <div className="grid grid-cols-1 gap-3 text-sm">
            {PIPELINE_STEPS.map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 font-semibold text-blue-700">
                  {index + 1}
                </div>
                <div className="flex-1 rounded-md border border-gray-200 bg-gray-50 px-4 py-3">{step}</div>
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-md border border-blue-100 bg-blue-50 p-4 text-sm text-blue-800">
            The current GNN selector uses a refined relation graph with early stopping. The PINN branch is still a dedicated `heat1d`
            demo baseline and should be presented as a complementary AI solver, not a replacement for the full numerical stack.
            <span className="mt-2 block text-blue-700">{ZH.pipelineHint}</span>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-xl font-semibold text-gray-900">
          Benchmark Notes <span className="text-sm font-medium text-gray-500">{ZH.benchmarkNotes}</span>
        </h2>
        <p className="mb-4 text-sm text-gray-500">{ZH.benchmarkNotesIntro}</p>
        <ul className="space-y-2 text-sm text-gray-600">
          {(benchmark.report?.notes || []).map((note) => (
            <li key={note}>- {note}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function PageState({ title, description, danger = false }: { title: string; description: string; danger?: boolean }) {
  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className={`rounded-lg border p-6 ${danger ? 'border-red-200 bg-red-50 text-red-800' : 'border-gray-200 bg-white text-gray-700'}`}>
        <h1 className="mb-2 text-2xl font-bold">{title}</h1>
        <p>{description}</p>
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2 text-gray-600">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  );
}
