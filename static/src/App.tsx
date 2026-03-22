import type { ReactNode } from 'react';
import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  BarChart3,
  Calculator,
  FileText,
  Home,
  Landmark,
  Settings,
} from 'lucide-react';
import AnimeAssistant from './components/AnimeAssistant';
import GlobalSceneBackdrop from './components/GlobalSceneBackdrop';

const FinancePage = lazy(() => import('./pages/FinancePage'));
const LLMConfigPage = lazy(() => import('./pages/LLMConfigPage'));
const QuestionPage = lazy(() => import('./pages/QuestionPage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const SolvePage = lazy(() => import('./pages/SolvePage'));

type Page = 'home' | 'question' | 'solve' | 'results' | 'finance' | 'llm-config';

const HASH_TO_PAGE: Record<string, Page> = {
  '#home': 'home',
  '#question': 'question',
  '#solve': 'solve',
  '#results': 'results',
  '#finance': 'finance',
  '#llm-config': 'llm-config',
};

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>(() => HASH_TO_PAGE[window.location.hash] || 'home');

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPage(HASH_TO_PAGE[window.location.hash] || 'home');
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (page: Page) => {
    const nextHash = Object.entries(HASH_TO_PAGE).find(([, value]) => value === page)?.[0] || '#home';
    window.location.hash = nextHash;
    setCurrentPage(page);
  };

  const assistantPreset = useMemo(() => {
    switch (currentPage) {
      case 'finance':
        return {
          mood: 'happy' as const,
          message: '金融分析模块已就绪。\n可以去看股票演化和期权定价面板。',
        };
      case 'results':
        return {
          mood: 'thinking' as const,
          message: '这里是实验结果总览页。\n可以快速比较算法误差、耗时和支持范围。',
        };
      case 'question':
        return {
          mood: 'idle' as const,
          message: '可以先从自然语言题目解析开始。\n我会陪你一步步看参数。',
        };
      case 'llm-config':
        return {
          mood: 'shy' as const,
          message: '这里是模型配置页。\n改完参数后记得回到求解页试一试。',
        };
      case 'home':
      default:
        return {
          mood: 'idle' as const,
          message: '欢迎回来。\n要不要先去 Solve 页跑一个 PDE 例子？',
        };
    }
  }, [currentPage]);

  const renderPage = () => {
    switch (currentPage) {
      case 'question':
        return <QuestionPage />;
      case 'solve':
        return <SolvePage />;
      case 'results':
        return <ResultsPage />;
      case 'finance':
        return <FinancePage />;
      case 'llm-config':
        return <LLMConfigPage />;
      case 'home':
      default:
        return (
          <HomePage
            onStart={() => navigate('solve')}
            onViewResults={() => navigate('results')}
            onOpenFinance={() => navigate('finance')}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b border-gray-200 bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex min-h-16 flex-col justify-center gap-3 py-3 lg:flex-row lg:items-center lg:justify-between lg:py-0">
            <div className="flex items-center gap-2">
              <Calculator className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">
                PDE Solver <span className="text-sm font-medium text-gray-500">偏微分方程求解平台</span>
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1">
              <NavButton active={currentPage === 'home'} onClick={() => navigate('home')} icon={<Home className="h-4 w-4" />}>
                Home 首页
              </NavButton>
              <NavButton active={currentPage === 'question'} onClick={() => navigate('question')} icon={<FileText className="h-4 w-4" />}>
                Parse 解析
              </NavButton>
              <NavButton active={currentPage === 'solve'} onClick={() => navigate('solve')} icon={<Activity className="h-4 w-4" />}>
                Solve 求解
              </NavButton>
              <NavButton active={currentPage === 'results'} onClick={() => navigate('results')} icon={<BarChart3 className="h-4 w-4" />}>
                Results 结果
              </NavButton>
              <NavButton active={currentPage === 'finance'} onClick={() => navigate('finance')} icon={<Landmark className="h-4 w-4" />}>
                Finance 金融实践
              </NavButton>
              <NavButton
                active={currentPage === 'llm-config'}
                onClick={() => navigate('llm-config')}
                icon={<Settings className="h-4 w-4" />}
              >
                LLM Config 配置
              </NavButton>
            </div>
          </div>
        </div>
      </nav>
      <main className="relative overflow-hidden py-6">
        <GlobalSceneBackdrop page={currentPage} />
        <div className="relative z-10">
          <Suspense fallback={<PageFallback />}>{renderPage()}</Suspense>
        </div>
      </main>
      {currentPage !== 'solve' ? <AnimeAssistant mood={assistantPreset.mood} message={assistantPreset.message} /> : null}
    </div>
  );
}

function PageFallback() {
  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-gray-600">
        Loading page... 页面加载中
      </div>
    </div>
  );
}

function NavButton({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean;
  onClick: () => void;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-md px-4 py-2 transition-colors ${
        active ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

function HomePage({
  onStart,
  onViewResults,
  onOpenFinance,
}: {
  onStart: () => void;
  onViewResults: () => void;
  onOpenFinance: () => void;
}) {
  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-12 text-center">
        <h1 className="mb-4 text-4xl font-bold text-gray-900">
          ML-Driven PDE Solver Framework
          <span className="block text-lg font-medium text-gray-500">
            机器学习驱动的 PDE 求解与算法选择框架
          </span>
        </h1>
        <p className="text-xl text-gray-600">
          Connect question parsing, feature extraction, algorithm recommendation, numerical solving, and result evaluation.
          <span className="block text-base text-gray-500">
            打通题目解析、特征提取、算法推荐、数值求解与结果评估。
          </span>
        </p>
      </div>

      <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-3">
        <FeatureCard
          title="Feature Extraction 特征提取"
          icon={<Activity className="h-6 w-6 text-blue-600" />}
          iconBg="bg-blue-100"
        >
          Extract physics, hardware, and requirement features to build a unified selector input.
          <span className="block text-sm text-gray-500">自动整理物理特征、硬件特征和需求特征，作为算法选择的统一输入。</span>
        </FeatureCard>
        <FeatureCard
          title="Algorithm Selection 算法选择"
          icon={<Calculator className="h-6 w-6 text-green-600" />}
          iconBg="bg-green-100"
        >
          Support RF, XGB, RL, MLP, GNN, and other recommendation strategies.
          <span className="block text-sm text-gray-500">支持随机森林、XGBoost、强化学习、MLP、GNN 等策略。</span>
        </FeatureCard>
        <FeatureCard
          title="Finance Practice 金融实践"
          icon={<Landmark className="h-6 w-6 text-amber-600" />}
          iconBg="bg-amber-100"
        >
          Extend the PDE platform into stock dynamics and option-pricing case studies without changing the thesis mainline.
          <span className="block text-sm text-gray-500">在不改变论文主线的前提下，扩展股票演化和期权定价两个金融应用场景。</span>
        </FeatureCard>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-2xl font-bold">
          Representative Equations <span className="text-base font-medium text-gray-500">当前支持的代表性方程</span>
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 xl:grid-cols-4">
          <AlgoCard title="heat1d">1D heat equation with `fdm / fvm / fem / spectral / pinn`. 一维热传导方程。</AlgoCard>
          <AlgoCard title="heat2d">2D heat equation with `fdm / fvm / fem`. 二维热传导方程。</AlgoCard>
          <AlgoCard title="heat3d">3D heat equation with `fdm / fvm / fem`. 三维热传导方程。</AlgoCard>
          <AlgoCard title="wave1d">1D wave equation with `fdm / fem / spectral`. 一维波动方程。</AlgoCard>
          <AlgoCard title="wave2d">2D wave equation with `fdm / fem / spectral`. 二维波动方程。</AlgoCard>
          <AlgoCard title="wave3d">3D wave equation with `fdm / fem / spectral`. 三维波动方程。</AlgoCard>
          <AlgoCard title="poisson1d">1D Poisson equation with `fdm / fem / spectral / bem`. 一维 Poisson 方程。</AlgoCard>
          <AlgoCard title="poisson3d">3D Poisson equation with `fdm / fem / bem`. 三维 Poisson 方程。</AlgoCard>
          <AlgoCard title="poisson2d_nonlinear">2D nonlinear Poisson demo case. 二维非线性 Poisson 演示场景。</AlgoCard>
        </div>
      </div>

      <div className="mt-8 rounded-lg border border-blue-100 bg-blue-50 p-5 text-sm text-blue-900">
        <p className="font-semibold">Finance 模块说明</p>
        <p className="mt-2">
          新增的金融实践板块不会替代现有的 heat / wave / poisson 主线，而是作为平台通用性的应用案例。
        </p>
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
        <button
          onClick={onStart}
          className="rounded-lg bg-blue-600 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700"
        >
          Start Solving 开始求解
        </button>
        <button
          onClick={onViewResults}
          className="rounded-lg border border-blue-200 bg-white px-8 py-3 text-lg font-semibold text-blue-700 transition-colors hover:bg-blue-50"
        >
          View Results 查看结果
        </button>
        <button
          onClick={onOpenFinance}
          className="rounded-lg border border-amber-200 bg-amber-50 px-8 py-3 text-lg font-semibold text-amber-800 transition-colors hover:bg-amber-100"
        >
          Open Finance 打开金融模块
        </button>
      </div>
    </div>
  );
}

function FeatureCard({
  title,
  icon,
  iconBg,
  children,
}: {
  title: string;
  icon: ReactNode;
  iconBg: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-lg ${iconBg}`}>{icon}</div>
      <h3 className="mb-2 text-lg font-semibold">{title}</h3>
      <div className="text-gray-600">{children}</div>
    </div>
  );
}

function AlgoCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md bg-gray-50 p-4">
      <h3 className="mb-2 font-semibold">{title}</h3>
      <p className="text-sm text-gray-600">{children}</p>
    </div>
  );
}
