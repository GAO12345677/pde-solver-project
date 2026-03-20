import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { Activity, Calculator, FileText, Home, Settings } from 'lucide-react';
import LLMConfigPage from './pages/LLMConfigPage';
import QuestionPage from './pages/QuestionPage';
import SolvePage from './pages/SolvePage';

type Page = 'home' | 'solve' | 'llm-config' | 'question';

const HASH_TO_PAGE: Record<string, Page> = {
  '#home': 'home',
  '#solve': 'solve',
  '#llm-config': 'llm-config',
  '#question': 'question',
};

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>(() => HASH_TO_PAGE[window.location.hash] || 'home');

  useEffect(() => {
    const onHashChange = () => {
      setCurrentPage(HASH_TO_PAGE[window.location.hash] || 'home');
    };

    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const navigate = (page: Page) => {
    const nextHash = Object.entries(HASH_TO_PAGE).find(([, value]) => value === page)?.[0] || '#home';
    window.location.hash = nextHash;
    setCurrentPage(page);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'solve':
        return <SolvePage />;
      case 'llm-config':
        return <LLMConfigPage />;
      case 'question':
        return <QuestionPage />;
      case 'home':
      default:
        return <HomePage onStart={() => navigate('solve')} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <Calculator className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">PDE 求解器</span>
            </div>
            <div className="flex items-center gap-1">
              <NavButton active={currentPage === 'home'} onClick={() => navigate('home')} icon={<Home className="w-4 h-4" />}>
                首页
              </NavButton>
              <NavButton active={currentPage === 'question'} onClick={() => navigate('question')} icon={<FileText className="w-4 h-4" />}>
                题目解析
              </NavButton>
              <NavButton active={currentPage === 'solve'} onClick={() => navigate('solve')} icon={<Activity className="w-4 h-4" />}>
                求解
              </NavButton>
              <NavButton active={currentPage === 'llm-config'} onClick={() => navigate('llm-config')} icon={<Settings className="w-4 h-4" />}>
                LLM 配置
              </NavButton>
            </div>
          </div>
        </div>
      </nav>

      <main className="py-6">{renderPage()}</main>
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
      className={`px-4 py-2 rounded-md flex items-center gap-2 transition-colors ${
        active ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      {icon}
      {children}
    </button>
  );
}

function HomePage({ onStart }: { onStart: () => void }) {
  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">机器学习驱动的 PDE 求解器选择框架</h1>
        <p className="text-xl text-gray-600">智能选择最优算法，高效求解偏微分方程</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <FeatureCard title="特征提取" icon={<Activity className="w-6 h-6 text-blue-600" />} iconBg="bg-blue-100">
          自动提取物理特征、硬件特征和领域需求，为算法选择提供完整上下文。
        </FeatureCard>
        <FeatureCard title="算法选择" icon={<Calculator className="w-6 h-6 text-green-600" />} iconBg="bg-green-100">
          基于机器学习模型推荐更合适的数值方法，支持静态与动态策略。
        </FeatureCard>
        <FeatureCard title="结果评估" icon={<Settings className="w-6 h-6 text-purple-600" />} iconBg="bg-purple-100">
          从精度、效率和资源角度评估结果，并为后续优化提供反馈。
        </FeatureCard>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold mb-4">支持的算法</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AlgoCard title="有限差分法 (FDM)">适用于规则网格，实现简单，计算效率高。</AlgoCard>
          <AlgoCard title="有限元法 (FEM)">适用于复杂几何问题，精度高，通用性强。</AlgoCard>
          <AlgoCard title="谱方法 (Spectral)">适用于光滑解场景，收敛快，精度高。</AlgoCard>
        </div>
      </div>

      <div className="mt-8 text-center">
        <button
          onClick={onStart}
          className="bg-blue-600 text-white py-3 px-8 rounded-lg hover:bg-blue-700 transition-colors text-lg font-semibold"
        >
          开始求解
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${iconBg}`}>{icon}</div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{children}</p>
    </div>
  );
}

function AlgoCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-gray-50 p-4 rounded-md">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-gray-600">{children}</p>
    </div>
  );
}
