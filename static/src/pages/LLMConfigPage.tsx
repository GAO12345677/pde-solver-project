import { useEffect, useState } from 'react';
import { Activity, CheckCircle, Key, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { LLMConfig, LLMQuota } from '../types';

const MODELS = [
  { id: 'gemini', name: 'Google Gemini', provider: 'Google' },
  { id: 'openai', name: 'OpenAI GPT', provider: 'OpenAI' },
  { id: 'qwen', name: '阿里云 Qwen', provider: '阿里云' },
  { id: 'deepseek', name: 'DeepSeek', provider: 'DeepSeek' },
  { id: 'doubao', name: '字节跳动 Doubao', provider: '字节跳动' },
  { id: 'qianfan', name: '百度千帆', provider: '百度' },
];

export default function LLMConfigPage() {
  const [configs, setConfigs] = useState<Record<string, LLMConfig>>({});
  const [quotas, setQuotas] = useState<LLMQuota[]>([]);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [configRes, quotaRes] = await Promise.all([api.llm.getConfig(), api.llm.getQuota()]);
      setConfigs(configRes.data);
      setQuotas(quotaRes.data);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (modelId: string, config: LLMConfig) => {
    if (!config.api_key) {
      alert('请先配置 API Key');
      return;
    }

    setTesting(modelId);
    try {
      await api.llm.testConfig(config);
      setTestResults((prev) => ({ ...prev, [modelId]: true }));
      alert('连接测试成功');
    } catch (err) {
      setTestResults((prev) => ({ ...prev, [modelId]: false }));
      alert(`连接测试失败: ${err instanceof Error ? err.message : '未知错误'}`);
    } finally {
      setTesting(null);
    }
  };

  const handleSave = async (modelId: string, config: LLMConfig) => {
    try {
      await api.llm.saveConfig(config);
      setConfigs((prev) => ({ ...prev, [modelId]: config }));
      alert('配置保存成功');
    } catch (err) {
      alert(`配置保存失败: ${err instanceof Error ? err.message : '未知错误'}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">LLM 配置管理</h1>
        <p className="text-gray-600">配置和管理各类大语言模型的 API 密钥。</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MODELS.map((model) => {
          const config = configs[model.id] || { model_name: model.id, api_key: '', base_url: '', model_id: '' };
          const quota = quotas.find((item) => item.model_name === model.id);
          const testResult = testResults[model.id];

          return (
            <div key={model.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">{model.name}</h2>
                  <p className="text-sm text-gray-500">{model.provider}</p>
                </div>
                {testResult === true && <CheckCircle className="w-5 h-5 text-green-600" />}
                {testResult === false && <XCircle className="w-5 h-5 text-red-600" />}
              </div>

              <div className="space-y-4">
                <InputField
                  label="API Key"
                  type="password"
                  value={config.api_key || ''}
                  placeholder="输入 API Key"
                  onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, api_key: value } }))}
                />

                <InputField
                  label="Base URL（可选）"
                  value={config.base_url || ''}
                  placeholder="输入自定义 Base URL"
                  onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, base_url: value } }))}
                />

                {model.id === 'doubao' && (
                  <div>
                    <InputField
                      label="模型名称（必填）"
                      value={config.model_id || ''}
                      placeholder="例如：doubao-seed-1-8-251228"
                      onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, model_id: value } }))}
                    />
                    <p className="text-xs text-gray-500 mt-1">请在火山方舟控制台的“模型推理”页面获取模型名称。</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleTest(model.id, config)}
                    disabled={testing === model.id || !config.api_key}
                    className="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Activity className="w-4 h-4" />
                    {testing === model.id ? '测试中...' : '测试连接'}
                  </button>
                  <button
                    onClick={() => handleSave(model.id, config)}
                    disabled={!config.api_key}
                    className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    <Key className="w-4 h-4" />
                    保存配置
                  </button>
                </div>

                {quota && (
                  <div className="bg-gray-50 p-3 rounded-md space-y-2">
                    <QuotaRow label="提供商" value={quota.provider} />
                    <QuotaRow label="状态" value={quota.status === 'normal' ? '正常' : '未配置'} />
                    <QuotaRow label="剩余额度" value={`${quota.remaining_quota} / ${quota.total_quota}`} />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

function QuotaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}
