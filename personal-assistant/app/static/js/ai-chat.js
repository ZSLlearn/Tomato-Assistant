let chatHistory = [];

function addMessage(text, role, toolCalled = null) {
    const container = document.getElementById('ai-messages');
    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (toolCalled) {
        const badge = document.createElement('span');
        badge.className = 'tool-badge';
        badge.textContent = '🔧 ' + toolCalled;
        div.appendChild(badge);
    }
    const p = document.createElement('p');
    p.textContent = text;
    div.appendChild(p);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('ai-input');
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, 'user');
    chatHistory.push({ role: 'user', content: message });
    input.value = '';

    try {
        const resp = await api('/ai/chat', 'POST', { message, history: chatHistory });
        if (resp.code === 400) {
            const text = resp.message;
            addMessage(text, 'ai');
            chatHistory.push({ role: 'assistant', content: text });
            return;
        }
        const data = resp.data;
        let reply = data.reply;
        if (data.tool_result) {
            reply += '\n' + JSON.stringify(data.tool_result, null, 2);
        }
        addMessage(reply, 'ai', data.tool_called);
        chatHistory.push({ role: 'assistant', content: reply });
    } catch (e) {
        addMessage('抱歉，AI 服务连接失败: ' + e.message, 'ai');
    }
}

document.getElementById('ai-input').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') sendMessage();
});
