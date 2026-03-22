import { useEffect, useState } from 'react';
import { Activity, CheckCircle, Key, RefreshCw, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { LLMConfig, LLMQuota } from '../types';

const MODELS = [
  { id: 'gemini', name: 'Google Gemini', provider: 'Google' },
  { id: 'openai', name: 'OpenAI GPT', provider: 'OpenAI' },
  { id: 'qwen', name: 'Qwen', provider: 'Alibaba / 阿里云' },
  { id: 'deepseek', name: 'DeepSeek', provider: 'DeepSeek' },
  { id: 'doubao', name: 'Doubao', provider: 'ByteDance / 字节跳动' },
  { id: 'qianfan', name: 'Qianfan', provider: 'Baidu / 百度' },
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
      alert('Please configure an API key first. 先填写 API Key。');
      return;
    }

    setTesting(modelId);
    try {
      await api.llm.testConfig(config);
      setTestResults((prev) => ({ ...prev, [modelId]: true }));
      alert('Connection test passed. 连接测试成功。');
    } catch (err) {
      setTestResults((prev) => ({ ...prev, [modelId]: false }));
      alert(`Connection test failed. 连接测试失败：${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setTesting(null);
    }
  };

  const handleSave = async (modelId: string, config: LLMConfig) => {
    try {
      await api.llm.saveConfig(config);
      setConfigs((prev) => ({ ...prev, [modelId]: config }));
      alert('Configuration saved. 配置已保存。');
    } catch (err) {
      alert(`Save failed. 保存失败：${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl p-6">
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold text-gray-900">LLM Configuration</h1>
        <p className="text-gray-600">Manage model credentials and endpoint settings. 管理大模型密钥与接口配置。</p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {MODELS.map((model) => {
          const config = configs[model.id] || { model_name: model.id, api_key: '', base_url: '', model_id: '' };
          const quota = quotas.find((item) => item.model_name === model.id);
          const testResult = testResults[model.id];

          return (
            <div key={model.id} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">{model.name}</h2>
                  <p className="text-sm text-gray-500">{model.provider}</p>
                </div>
                {testResult === true && <CheckCircle className="h-5 w-5 text-green-600" />}
                {testResult === false && <XCircle className="h-5 w-5 text-red-600" />}
              </div>

              <div className="space-y-4">
                <InputField
                  label="API Key"
                  type="password"
                  value={config.api_key || ''}
                  placeholder="Enter API key / 输入 API Key"
                  onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, api_key: value } }))}
                />

                <InputField
                  label="Base URL (Optional) / 自定义地址"
                  value={config.base_url || ''}
                  placeholder="Custom base URL / 可选"
                  onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, base_url: value } }))}
                />

                {model.id === 'doubao' && (
                  <div>
                    <InputField
                      label="Model ID (Required) / 模型标识"
                      value={config.model_id || ''}
                      placeholder="Example: doubao-seed-1-8-250715"
                      onChange={(value) => setConfigs((prev) => ({ ...prev, [model.id]: { ...config, model_id: value } }))}
                    />
                    <p className="mt-1 text-xs text-gray-500">Find this in the Volcano Engine model inference console. 在火山方舟控制台获取模型名。</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleTest(model.id, config)}
                    disabled={testing === model.id || !config.api_key}
                    className="flex flex-1 items-center justify-center gap-2 rounded-md bg-gray-100 px-4 py-2 text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:bg-gray-50"
                  >
                    <Activity className="h-4 w-4" />
                    {testing === model.id ? 'Testing... 测试中' : 'Test Connection 测试连接'}
                  </button>
                  <button
                    onClick={() => handleSave(model.id, config)}
                    disabled={!config.api_key}
                    className="flex flex-1 items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
                  >
                    <Key className="h-4 w-4" />
                    Save 保存
                  </button>
                </div>

                {quota && (
                  <div className="space-y-2 rounded-md bg-gray-50 p-3">
                    <QuotaRow label="Provider / 提供方" value={quota.provider} />
                    <QuotaRow label="Status / 状态" value={quota.status === 'normal' ? 'Normal 正常' : 'Not configured 未配置'} />
                    <QuotaRow label="Quota / 配额" value={`${quota.remaining_quota} / ${quota.total_quota}`} />
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
      <label className="mb-1 block text-sm font-medium text-gray-700">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
