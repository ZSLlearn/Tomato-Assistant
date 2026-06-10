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
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">暂无日程<p style="font-size:var(--text-xs);margin-top:4px;">用上方表单添加日程</p></td></tr>';
        return;
    }
    const catMap = { '工作': '工作', '个人': '个人', '紧急': '紧急' };
    resp.data.forEach(function(ev) {
        const tr = document.createElement('tr');
        if (ev.is_completed) tr.style.opacity = '0.45';
        tr.innerHTML = '<td>' + ev.title + '</td>' +
            '<td>' + (ev.start_time ? ev.start_time.replace('T',' ') : '-') + '</td>' +
            '<td>' + (ev.end_time ? ev.end_time.replace('T',' ') : '-') + '</td>' +
            '<td><span class="cat-badge" style="background:var(--bg);">' + ev.category + '</span></td>' +
            '<td class="prio-' + ev.priority + '">' + (ev.priority === 1 ? '高' : ev.priority === 2 ? '中' : '低') + '</td>' +
            '<td>' + (ev.is_completed ? '已完成' : '待办') + '</td>' +
            '<td style="white-space:nowrap;">' +
                '<button onclick="toggleComplete(' + ev.id + ')" class="btn btn-sm btn-secondary" style="margin-right:4px;">' + (ev.is_completed ? '撤销' : '完成') + '</button>' +
                '<button onclick="delEvent(' + ev.id + ')" class="btn btn-sm btn-danger">删除</button>' +
            '</td>';
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
        title: title,
        start_time: start,
        end_time: document.getElementById('end_time').value,
        category: document.getElementById('category').value,
        priority: parseInt(document.getElementById('priority').value)
    };
    const resp = await api('/schedule/api/events', 'POST', body);
    if (resp.code === 201) {
        showToast('日程已添加');
        document.getElementById('title').value = '';
        document.getElementById('title').focus();
        loadEvents();
    } else { showToast(resp.message, true); }
}

async function toggleComplete(id) {
    await api('/schedule/api/events/' + id + '/complete', 'PUT');
    loadEvents();
}

async function delEvent(id) {
    if (!confirm('确认删除？')) return;
    await api('/schedule/api/events/' + id, 'DELETE');
    showToast('已删除');
    loadEvents();
}

window.addEventListener("ai-refresh", function(e) {
    if (e.detail.module === "schedule") { loadEvents(); }
});
