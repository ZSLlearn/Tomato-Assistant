var currentConvId = null;
var _suppressSwitch = false;
var _defaultCity = '北京';

document.addEventListener('DOMContentLoaded', async function() {
    // Load default city
    try {
        var cfg = await api('/settings/api/config');
        if (cfg.data && cfg.data.default_city) _defaultCity = cfg.data.default_city;
    } catch(e) {}

    await loadConversationList(true);
    document.getElementById('ai-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    document.getElementById('ai-input').addEventListener('input', autoResizeInput);
});

// === Conversation Management ===

async function loadConversationList(autoLoad) {
    var resp = await api('/ai/conversations');
    var select = document.getElementById('conv-selector');
    _suppressSwitch = true;
    select.innerHTML = '<option value="">+ 新建对话</option>';
    if (resp.code === 200 && resp.data.length > 0) {
        resp.data.forEach(function(c) {
            var opt = document.createElement('option');
            opt.value = c.id;
            var t = c.title || '新对话';
            opt.textContent = (t.length > 18 ? t.slice(0, 18) + '…' : t);
            opt.title = c.title || '新对话';
            select.appendChild(opt);
        });
        if (autoLoad) {
            var lastId = resp.data[0].id;
            select.value = lastId;
            _suppressSwitch = false;
            await switchConversation(lastId);
        } else if (currentConvId) {
            select.value = currentConvId;
        }
    }
    _suppressSwitch = false;
}

async function newConversation() {
    var resp = await api('/ai/conversations', 'POST');
    if (resp.code === 201) {
        currentConvId = resp.data.id;
        document.getElementById('ai-messages').innerHTML =
            '<div class="ai-empty"><div class="ai-empty-icon">💬</div><p>新建对话，开始交流吧</p>' +
            '<div class="ai-hints">' +
            '<span onclick="fillInput(\'今天收入 元\')">💰 记账</span>' +
            '<span onclick="fillInput(\'今天运动 分钟\')">🏃 运动</span>' +
            '<span onclick="fillInput(\'添加日程\')">📅 日程</span>' +
            '<span onclick="fillInput(\'查天气 ' + _defaultCity + '\')">🌤 天气</span>' +
            '</div></div>';
        await loadConversationList(false);
        _suppressSwitch = true;
        document.getElementById('conv-selector').value = currentConvId;
        _suppressSwitch = false;
        document.getElementById('ai-input').focus();
    }
}

async function switchConversation(cid) {
    if (_suppressSwitch) return;
    if (!cid) { await newConversation(); return; }
    currentConvId = parseInt(cid);
    var container = document.getElementById('ai-messages');
    container.innerHTML = '<div class="ai-loading"><span></span><span></span><span></span></div>';

    var resp = await api('/ai/conversations/' + cid);
    if (resp.code !== 200) {
        container.innerHTML = '<div class="ai-empty"><p>对话不存在</p></div>';
        return;
    }
    container.innerHTML = '';
    var msgs = resp.data.messages || [];
    if (msgs.length === 0) {
        container.innerHTML =
            '<div class="ai-empty"><div class="ai-empty-icon">💬</div><p>开始一段新对话吧</p>' +
            '<div class="ai-hints">' +
            '<span onclick="fillInput(\'记账\')">💰</span>' +
            '<span onclick="fillInput(\'健康\')">🏃</span>' +
            '<span onclick="fillInput(\'日程\')">📅</span>' +
            '<span onclick="fillInput(\'天气 ' + _defaultCity + '\')">🌤</span>' +
            '</div></div>';
    }
    msgs.forEach(function(m) {
        var tc = null;
        if (m.tool_called) {
            var parsed = JSON.parse(m.tool_called);
            // Extract tool name from array format [{...}] or use string directly
            if (Array.isArray(parsed)) {
                tc = parsed[0] && parsed[0].function ? parsed[0].function.name : null;
            } else if (typeof parsed === 'string') {
                tc = parsed;
            }
        }
        addMessage(m.content, m.role, tc);
    });
}

async function renameConversation() {
    if (!currentConvId) return;
    var select = document.getElementById('conv-selector');
    var currentName = select.options[select.selectedIndex].text;
    var newName = prompt('重命名对话：', currentName);
    if (!newName || !newName.trim()) return;
    await api('/ai/conversations/' + currentConvId, 'PUT', { title: newName.trim() });
    await loadConversationList(false);
    _suppressSwitch = true;
    document.getElementById('conv-selector').value = currentConvId;
    _suppressSwitch = false;
    showToast('已重命名');
}

async function deleteConversation() {
    if (!currentConvId) return;
    if (!confirm('确认删除当前对话？所有消息将被永久删除。')) return;
    await api('/ai/conversations/' + currentConvId, 'DELETE');
    currentConvId = null;
    await loadConversationList(true);
    showToast('对话已删除');
}

// === Message Rendering ===

function addMessage(text, role, toolCalled) {
    var container = document.getElementById('ai-messages');
    // Remove empty state if present
    var empty = container.querySelector('.ai-empty');
    if (empty) empty.remove();

    var div = document.createElement('div');
    div.className = 'msg ' + role;

    if (toolCalled) {
        var badge = document.createElement('span');
        badge.className = 'tool-badge';
        // Normalize: extract name if array
        var toolName = toolCalled;
        if (Array.isArray(toolCalled)) {
            toolName = toolCalled[0] && toolCalled[0].function ? toolCalled[0].function.name : '';
        }
        var labelMap = {
            'add_finance_record': '💰 记账', 'query_finance': '📊 查账',
            'record_health': '❤️ 健康', 'query_health': '📋 健康',
            'manage_schedule': '📅 日程', 'manage_memo': '📝 笔记',
            'query_weather': '🌤 天气'
        };
        badge.textContent = labelMap[toolName] || toolName;
        div.appendChild(badge);
    }

    // Format text: line breaks, simple markdown
    var formatted = formatMessage(text);
    div.innerHTML += formatted;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatMessage(text) {
    if (!text) return '';
    // Escape HTML
    var escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    // Bold: **text**
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Line breaks
    escaped = escaped.replace(/\n/g, '<br>');
    // Highlight amounts
    escaped = escaped.replace(/¥([\d,.]+)/g, '<span class="hl-amount">¥$1</span>');
    // Highlight temperatures
    escaped = escaped.replace(/(\d+\.?\d*°C)/g, '<span class="hl-temp">$1</span>');
    return escaped;
}

function showTyping() {
    var container = document.getElementById('ai-messages');
    var div = document.createElement('div');
    div.className = 'msg ai typing';
    div.id = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    var el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

// === Input Helpers ===

function fillInput(text) {
    var input = document.getElementById('ai-input');
    input.value = text;
    input.focus();
    // Place cursor at end
    var len = input.value.length;
    input.setSelectionRange(len, len);
}

function autoResizeInput() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 80) + 'px';
}

// === Send Message ===

async function sendMessage() {
    var input = document.getElementById('ai-input');
    var message = input.value.trim();
    if (!message) return;

    // Handle /commands
    if (message.startsWith('/')) {
        handleCommand(message);
        input.value = '';
        return;
    }

    addMessage(message, 'user');
    input.value = '';
    input.style.height = 'auto';
    input.disabled = true;
    showTyping();

    try {
        var resp = await api('/ai/chat', 'POST', {
            message: message,
            conversation_id: currentConvId
        });

        hideTyping();

        if (resp.code === 400) {
            addMessage(resp.message, 'ai');
            input.disabled = false;
            input.focus();
            return;
        }

        var data = resp.data;
        currentConvId = data.conversation_id;
        addMessage(data.reply, 'ai', data.tool_called);

        if (data.refresh) {
            window.dispatchEvent(new CustomEvent('ai-refresh', {
                detail: { module: data.refresh, tool: data.tool_called, result: data.tool_result }
            }));
        }

        await loadConversationList(false);

    } catch (e) {
        hideTyping();
        addMessage('网络连接失败，请重试', 'ai');
    }
    input.disabled = false;
    input.focus();
}

function handleCommand(cmd) {
    var map = {
        '/help': '可用指令：\n/income 金额 备注 — 记录收入\n/expense 金额 备注 — 记录支出\n/weight 数值 — 记录体重\n/water 毫升 — 记录饮水\n/schedule 标题 — 添加日程\n/weather 城市 — 查天气\n/rename — 重命名对话\n/delete — 删除当前对话\n/clear — 新建对话',
        '/rename': function() { renameConversation(); return null; },
        '/delete': function() { deleteConversation(); return null; },
        '/clear': function() { newConversation(); return null; }
    };
    if (typeof map[cmd] === 'function') { map[cmd](); return; }
    if (map[cmd]) { addMessage(map[cmd], 'ai'); return; }

    // Parse /income, /expense, etc.
    var parts = cmd.slice(1).split(/\s+/);
    var action = parts[0];
    if (action === 'income') {
        sendMessage(); return;  // fall through to normal chat
    }
    // Default: send as normal message
    document.getElementById('ai-input').value = cmd;
    sendMessage();
}
