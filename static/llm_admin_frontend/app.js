// 支持的模型列表及默认配置
const MODELS = [
    { id: 'openai', name: 'OpenAI', defaultUrl: 'https://api.openai.com/v1', keyPattern: /^sk-[a-zA-Z0-9]{32,}$/, keyHint: 'OpenAI Key 通常以 sk- 开头' },
    { id: 'qwen', name: '通义千问', defaultUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', keyPattern: /^sk-[a-zA-Z0-9]+$/, keyHint: '通义千问 Key 通常以 sk- 开头' },
    { id: 'deepseek', name: 'DeepSeek', defaultUrl: 'https://api.deepseek.com/v1', keyPattern: /^sk-[a-zA-Z0-9]+$/, keyHint: 'DeepSeek Key 通常以 sk- 开头' },
    { id: 'doubao', name: '豆包', defaultUrl: 'https://ark.cn-beijing.volces.com/api/v3', keyPattern: /^[a-zA-Z0-9-]+$/, keyHint: '请输入有效的豆包 API Key' },
    { id: 'gemini', name: 'Google Gemini', defaultUrl: 'https://generativelanguage.googleapis.com/v1beta', keyPattern: /^AIza[0-9A-Za-z-_]{35}$/, keyHint: 'Gemini Key 通常以 AIza 开头' },
    { id: 'qianfan', name: '百度千帆', defaultUrl: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop', keyPattern: /.*/, keyHint: '请输入有效的百度千帆 Key' }
];

// 后端 API 基础路径
const API_BASE = '/llm';

// DOM 元素引用
const modelGrid = document.getElementById('model-grid');
const quotaGrid = document.getElementById('quota-grid');
const toastContainer = document.getElementById('toast-container');

// 初始化
function init() {
    renderModelCards();
    loadLocalConfigs();
    fetchServerConfigs();
    fetchQuotas();

    document.getElementById('load-configs-btn').addEventListener('click', fetchServerConfigs);
    document.getElementById('refresh-quota-btn').addEventListener('click', fetchQuotas);
}

// 渲染模型配置卡片
function renderModelCards() {
    modelGrid.innerHTML = '';
    MODELS.forEach(model => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-title">${model.name}</div>
            <div class="form-group">
                <label>API Key <span style="color:#999;font-weight:normal;font-size:11px;">(本地缓存)</span></label>
                <div class="input-wrapper">
                    <input type="password" id="key-${model.id}" placeholder="输入 API Key" autocomplete="off">
                    <button type="button" class="toggle-pwd" onclick="togglePwd('key-${model.id}')">显示</button>
                </div>
                <div class="error-msg" id="err-${model.id}">${model.keyHint}</div>
            </div>
            <div class="form-group">
                <label>Base URL <span style="color:#999;font-weight:normal;font-size:11px;">(可选)</span></label>
                <input type="text" id="url-${model.id}" placeholder="${model.defaultUrl}">
            </div>
            ${model.id === 'doubao' ? `
            <div class="form-group">
                <label>模型名称 <span style="color:#999;font-weight:normal;font-size:11px;">(必填)</span></label>
                <input type="text" id="model-id-${model.id}" placeholder="例如：doubao-seed-1-8-251228">
                <div class="error-msg" style="color:#666;font-size:11px;margin-top:2px;">请在火山方舟控制台的「模型推理」页面获取模型名称</div>
            </div>
            ` : ''}
            <div class="card-actions">
                <button class="btn secondary" id="test-btn-${model.id}" onclick="testConfig('${model.id}')">
                    <div class="spinner"></div>测试连接
                </button>
                <button class="btn primary" id="save-btn-${model.id}" onclick="saveConfig('${model.id}')">
                    <div class="spinner"></div>保存配置
                </button>
            </div>
        `;
        modelGrid.appendChild(card);

        // 添加输入校验和本地缓存监听
        const keyInput = document.getElementById(`key-${model.id}`);
        keyInput.addEventListener('input', (e) => validateKey(model.id, e.target.value));
        keyInput.addEventListener('change', (e) => {
            localStorage.setItem(`llm_key_${model.id}`, e.target.value);
        });

        const urlInput = document.getElementById(`url-${model.id}`);
        urlInput.addEventListener('change', (e) => {
            localStorage.setItem(`llm_url_${model.id}`, e.target.value);
        });

        // 为豆包添加模型名称的本地缓存
        if (model.id === 'doubao') {
            const modelIdInput = document.getElementById(`model-id-${model.id}`);
            modelIdInput.addEventListener('change', (e) => {
                localStorage.setItem(`llm_model_id_${model.id}`, e.target.value);
            });
        }
    });
}

// 切换密码显示/隐藏
window.togglePwd = function(inputId) {
    const input = document.getElementById(inputId);
    const btn = input.nextElementSibling;
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '隐藏';
    } else {
        input.type = 'password';
        btn.textContent = '显示';
    }
}

// 校验 API Key 格式
function validateKey(modelId, value) {
    const model = MODELS.find(m => m.id === modelId);
    const input = document.getElementById(`key-${modelId}`);
    const errMsg = document.getElementById(`err-${modelId}`);
    
    if (value && model.keyPattern && !model.keyPattern.test(value)) {
        input.classList.add('error');
        errMsg.style.display = 'block';
        return false;
    } else {
        input.classList.remove('error');
        errMsg.style.display = 'none';
        return true;
    }
}

// 从 LocalStorage 加载本地缓存
function loadLocalConfigs() {
    MODELS.forEach(model => {
        const localKey = localStorage.getItem(`llm_key_${model.id}`);
        const localUrl = localStorage.getItem(`llm_url_${model.id}`);
        
        if (localKey) {
            document.getElementById(`key-${model.id}`).value = localKey;
            validateKey(model.id, localKey);
        }
        if (localUrl) {
            document.getElementById(`url-${model.id}`).value = localUrl;
        }
        
        // 为豆包加载模型名称
        if (model.id === 'doubao') {
            const localModelId = localStorage.getItem(`llm_model_id_${model.id}`);
            if (localModelId) {
                document.getElementById(`model-id-${model.id}`).value = localModelId;
            }
        }
    });
}

// 从服务器获取已配置的信息
async function fetchServerConfigs() {
    const btn = document.getElementById('load-configs-btn');
    setLoading(btn, true);
    try {
        const res = await fetch(`${API_BASE}/config/get`);
        const result = await res.json();
        if (result.code === 200 && result.data) {
            for (const [modelId, config] of Object.entries(result.data)) {
                const urlInput = document.getElementById(`url-${modelId}`);
                if (urlInput && config.base_url && !urlInput.value) {
                    urlInput.value = config.base_url;
                }
                const keyInput = document.getElementById(`key-${modelId}`);
                if (keyInput && config.api_key && !keyInput.value) {
                    keyInput.placeholder = "已在服务器配置 (脱敏隐藏)";
                }
            }
            showToast('已加载服务器配置', 'success');
        }
    } catch (err) {
        showToast('获取服务器配置失败', 'error');
    } finally {
        setLoading(btn, false);
    }
}

// 测试连接
window.testConfig = async function(modelId) {
    const keyInput = document.getElementById(`key-${modelId}`);
    const urlInput = document.getElementById(`url-${modelId}`);
    const modelIdInput = modelId === 'doubao' ? document.getElementById(`model-id-${modelId}`) : null;
    
    if (!keyInput.value && !keyInput.placeholder.includes('已在服务器配置')) {
        showToast('请先输入 API Key', 'error');
        return;
    }

    if (modelId === 'doubao' && !modelIdInput) {
        showToast('请先输入模型名称', 'error');
        return;
    }

    const btn = document.getElementById(`test-btn-${modelId}`);
    setLoading(btn, true);

    const requestData = {
        model_name: modelId,
        api_key: keyInput.value || "", 
        base_url: urlInput.value || null,
        model_id: modelIdInput ? modelIdInput.value : null
    };
    
    console.log('发送测试请求:', requestData);

    try {
        const res = await fetch(`${API_BASE}/config/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        const result = await res.json();
        
        if (result.code === 200) {
            showToast(`${MODELS.find(m=>m.id===modelId).name} 测试成功`, 'success');
        } else {
            showToast(`测试失败: ${result.message}`, 'error');
        }
    } catch (err) {
        showToast(`请求失败: ${err.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

// 保存配置
window.saveConfig = async function(modelId) {
    const keyInput = document.getElementById(`key-${modelId}`);
    const urlInput = document.getElementById(`url-${modelId}`);
    const modelIdInput = modelId === 'doubao' ? document.getElementById(`model-id-${modelId}`) : null;
    
    if (!keyInput.value) {
        showToast('请先输入 API Key', 'error');
        return;
    }

    if (!validateKey(modelId, keyInput)) {
        showToast('API Key 格式可能不正确，请检查', 'error');
    }

    if (modelId === 'doubao' && !modelIdInput) {
        showToast('请先输入模型名称', 'error');
        return;
    }

    const btn = document.getElementById(`save-btn-${modelId}`);
    setLoading(btn, true);

    try {
        const res = await fetch(`${API_BASE}/config/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model_name: modelId,
                api_key: keyInput.value,
                base_url: urlInput.value || null,
                model_id: modelIdInput ? modelIdInput.value : null
            })
        });
        const result = await res.json();
        
        if (result.code === 200) {
            showToast('配置保存成功', 'success');
            fetchQuotas(); // 保存成功后刷新额度
        } else {
            showToast(`保存失败: ${result.message}`, 'error');
        }
    } catch (err) {
        showToast(`请求失败: ${err.message}`, 'error');
    } finally {
        setLoading(btn, false);
    }
}

// 获取所有模型额度
async function fetchQuotas() {
    const btn = document.getElementById('refresh-quota-btn');
    setLoading(btn, true);
    quotaGrid.innerHTML = '<div style="color:#666;font-size:14px;grid-column:1/-1;">加载中...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/quota/get`);
        const result = await res.json();
        
        if (result.code === 200 && result.data) {
            renderQuotaCards(result.data);
            showToast('额度信息已刷新', 'success');
        } else {
            quotaGrid.innerHTML = `<div style="color:var(--error-color);font-size:14px;grid-column:1/-1;">获取失败: ${result.message}</div>`;
        }
    } catch (err) {
        quotaGrid.innerHTML = `<div style="color:var(--error-color);font-size:14px;grid-column:1/-1;">请求失败: ${err.message}</div>`;
    } finally {
        setLoading(btn, false);
    }
}

// 渲染额度卡片
function renderQuotaCards(quotaData) {
    quotaGrid.innerHTML = '';
    
    if (quotaData.length === 0) {
        quotaGrid.innerHTML = '<div style="color:#666;font-size:14px;grid-column:1/-1;">暂无模型额度信息</div>';
        return;
    }

    quotaData.forEach(item => {
        const modelDef = MODELS.find(m => m.id === item.model_name) || { name: item.model_name };
        
        let percent = 0;
        if (item.total_quota > 0) {
            percent = (item.remaining_quota / item.total_quota) * 100;
        }
        percent = Math.max(0, Math.min(100, percent));
        
        let colorClass = '';
        if (percent > 80) colorClass = ''; // 默认绿色
        else if (percent >= 50) colorClass = 'yellow';
        else if (percent > 0) colorClass = 'orange';
        else colorClass = 'red';

        let badgeClass = 'success';
        let statusText = '额度充足';
        
        if (item.status === 'unconfigured') {
            badgeClass = '';
            statusText = '未配置';
            percent = 0;
            colorClass = 'red';
        } else if (item.status === 'error') {
            badgeClass = 'danger';
            statusText = '获取失败';
            percent = 0;
            colorClass = 'red';
        } else if (item.status === 'exhausted' || percent === 0) {
            badgeClass = 'danger';
            statusText = '额度耗尽';
        } else if (item.status === 'insufficient' || percent < 50) {
            badgeClass = 'warning';
            statusText = '额度不足';
        }

        const card = document.createElement('div');
        card.className = 'card quota-card';
        card.innerHTML = `
            <div class="quota-header">
                <div style="font-weight:600;font-size:15px;">${modelDef.name}</div>
                <div class="status-badge ${badgeClass}">${statusText}</div>
            </div>
            <div class="quota-provider">服务商: ${item.provider || '-'}</div>
            
            ${item.status !== 'unconfigured' && item.status !== 'error' ? `
            <div class="quota-stats">
                <span>剩余: ${formatNumber(item.remaining_quota)}</span>
                <span style="color:var(--text-muted)">总计: ${formatNumber(item.total_quota)}</span>
            </div>
            <div class="progress-bg">
                <div class="progress-bar ${colorClass}" style="width: ${percent}%"></div>
            </div>
            ` : ''}
            
            <div class="quota-msg">${item.message ? item.message : `更新于: ${formatDate(item.update_time)}`}</div>
        `;
        quotaGrid.appendChild(card);
    });
}

// 辅助函数：设置按钮加载状态
function setLoading(btn, isLoading) {
    if (!btn) return;
    if (isLoading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// 辅助函数：显示 Toast 提示
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span>${message}</span>
        <button style="background:none;border:none;cursor:pointer;font-size:16px;color:#999;" onclick="this.parentElement.remove()">&times;</button>
    `;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// 辅助函数：格式化数字 (如 1.5K, 2.3M)
function formatNumber(num) {
    if (num === undefined || num === null) return '-';
    if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(2) + 'K';
    return num.toString();
}

// 辅助函数：格式化日期
function formatDate(isoString) {
    if (!isoString) return '-';
    try {
        const d = new Date(isoString);
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    } catch(e) {
        return isoString;
    }
}

// 启动
document.addEventListener('DOMContentLoaded', init);
