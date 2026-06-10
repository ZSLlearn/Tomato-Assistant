document.addEventListener('DOMContentLoaded', function() {
    const now = new Date();
    const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
    document.getElementById('start_time').value = local;
    document.getElementById('schedule-form').addEventListener('submit', addEvent);
    document.getElementById('start_time').addEventListener('change', function() {
        const end = document.getElementById('end_time');
        if (!end.value) setDuration(60);
    });
    document.getElementById('title').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); addEvent(e); }
    });
    loadEvents();
});

function setDuration(minutes) {
    const startVal = document.getElementById('start_time').value;
    if (!startVal) return;
    const start = new Date(startVal);
    start.setMinutes(start.getMinutes() + minutes);
    document.getElementById('end_time').value = new Date(start.getTime() - start.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

async function loadEvents() {
    const resp = await api('/schedule/api/events');
    const tbody = document.getElementById('events-body');
    tbody.innerHTML = '';
    if (!resp.data || resp.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">📭 暂无日程<br><small>用上方表单安排你的事项吧</small></td></tr>';
        return;
    }
    const catMap = { '工作': '💼', '个人': '👤', '紧急': '🔴' };
    resp.data.forEach(ev => {
        const tr = document.createElement('tr');
        if (ev.is_completed) tr.style.opacity = '0.5';
        tr.innerHTML = `<td>${ev.title}</td>
            <td>${ev.start_time?.replace('T',' ') || '-'}</td>
            <td>${ev.end_time?.replace('T',' ') || '-'}</td>
            <td>${catMap[ev.category] || ''} ${ev.category}</td>
            <td class="prio-${ev.priority}">${'🔴🟡🟢'[ev.priority-1] || ''}</td>
            <td>${ev.is_completed ? '✅' : '⏳'}</td>
            <td>
                <button onclick="toggleComplete(${ev.id})" style="font-size:12px;padding:4px 8px;">${ev.is_completed ? '↩' : '✓'}</button>
                <button onclick="delEvent(${ev.id})" class="danger" style="font-size:12px;padding:4px 8px;">✕</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

async function addEvent(e) {
    e.preventDefault();
    const title = document.getElementById('title').value.trim();
    if (!title) { showToast('请输入日程标题', true); return; }
    const start = document.getElementById('start_time').value;
    if (!start) { showToast('请选择开始时间', true); return; }
    const body = {
        title, start_time: start,
        end_time: document.getElementById('end_time').value,
        category: document.getElementById('category').value,
        priority: parseInt(document.getElementById('priority').value)
    };
    const resp = await api('/schedule/api/events', 'POST', body);
    if (resp.code === 201) {
        showToast('📅 日程已添加');
        document.getElementById('title').value = '';
        document.getElementById('title').focus();
        loadEvents();
    } else { showToast(resp.message, true); }
}

async function toggleComplete(id) {
    await api(`/schedule/api/events/${id}/complete`, 'PUT');
    loadEvents();
}

async function delEvent(id) {
    if (!confirm('确认删除？')) return;
    await api(`/schedule/api/events/${id}`, 'DELETE');
    showToast('已删除');
    loadEvents();
}
