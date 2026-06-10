let currentNoteId = null;
let autoSaveTimer = null;

document.addEventListener('DOMContentLoaded', function() {
    loadNoteList();
    document.getElementById('memo-form').addEventListener('submit', saveNote);
    document.getElementById('search-input').addEventListener('input', function() {
        loadNoteList(this.value);
    });
    // Auto-save on input (debounced)
    ['memo-title', 'memo-content', 'memo-tags'].forEach(id => {
        document.getElementById(id)?.addEventListener('input', debounceAutoSave);
    });
});

function debounceAutoSave() {
    if (!currentNoteId) return;
    clearTimeout(autoSaveTimer);
    document.getElementById('auto-save-indicator').classList.add('visible');
    document.getElementById('auto-save-indicator').textContent = '⏳ 正在保存...';
    autoSaveTimer = setTimeout(() => autoSave(), 1500);
}

async function autoSave() {
    if (!currentNoteId) return;
    const body = {
        title: document.getElementById('memo-title').value.trim() || '未命名笔记',
        content: document.getElementById('memo-content').value,
        tags: document.getElementById('memo-tags').value
    };
    await api(`/memo/api/notes/${currentNoteId}`, 'PUT', body);
    document.getElementById('auto-save-indicator').textContent = '✅ 已自动保存';
    setTimeout(() => {
        document.getElementById('auto-save-indicator').classList.remove('visible');
    }, 2000);
    loadNoteList();
}

function newNote() {
    currentNoteId = null;
    document.getElementById('memo-title-display').textContent = '新建笔记';
    document.getElementById('memo-content-display').innerHTML = '<p style="color:var(--text-muted);">输入内容后点击保存...</p>';
    document.getElementById('memo-title').value = '';
    document.getElementById('memo-content').value = '';
    document.getElementById('memo-tags').value = '';
    document.getElementById('btn-pin').style.display = 'none';
    document.getElementById('auto-save-indicator').classList.remove('visible');
    document.querySelectorAll('#memo-list .item').forEach(el => el.classList.remove('active'));
    document.getElementById('memo-title').focus();
}

async function loadNoteList(keyword = '') {
    const url = keyword ? `/memo/api/notes?keyword=${encodeURIComponent(keyword)}` : '/memo/api/notes';
    const resp = await api(url);
    const list = document.getElementById('memo-list');
    list.innerHTML = '';
    if (!resp.data || resp.data.length === 0) {
        list.innerHTML = '<div class="item" style="color:var(--text-muted);cursor:default;">📭 暂无笔记</div>';
        return;
    }
    resp.data.forEach(note => {
        const div = document.createElement('div');
        div.className = 'item' + (note.id === currentNoteId ? ' active' : '');
        const dateStr = note.updated_at ? note.updated_at.slice(0, 10) : '';
        div.innerHTML = `${note.is_pinned ? '<span style="color:var(--warning);">📌</span> ' : ''}<strong>${escapeHtml(note.title)}</strong><br><small style="color:var(--text-muted);">${dateStr}</small>`;
        div.addEventListener('click', () => selectNote(note.id));
        list.appendChild(div);
    });
}

async function selectNote(id) {
    // Auto-save current note before switching
    if (currentNoteId && currentNoteId !== id) {
        clearTimeout(autoSaveTimer);
        await autoSave();
    }
    currentNoteId = id;
    const resp = await api(`/memo/api/notes/${id}`);
    const note = resp.data;
    document.getElementById('memo-title-display').textContent = note.title;
    document.getElementById('memo-content-display').innerHTML = (note.content || '<p style="color:var(--text-muted);">无内容</p>').replace(/\n/g, '<br>');
    document.getElementById('memo-title').value = note.title;
    document.getElementById('memo-content').value = note.content;
    document.getElementById('memo-tags').value = note.tags || '';
    const pinBtn = document.getElementById('btn-pin');
    pinBtn.style.display = '';
    pinBtn.textContent = note.is_pinned ? '📌 已置顶' : '📌 置顶';
    pinBtn.className = 'btn-pin' + (note.is_pinned ? ' pinned' : '');
    document.getElementById('auto-save-indicator').classList.remove('visible');
    loadNoteList(document.getElementById('search-input').value);
}

async function togglePin() {
    if (!currentNoteId) return;
    const resp = await api(`/memo/api/notes/${currentNoteId}/pin`, 'PUT');
    const note = resp.data;
    document.getElementById('btn-pin').textContent = note.is_pinned ? '📌 已置顶' : '📌 置顶';
    document.getElementById('btn-pin').className = 'btn-pin' + (note.is_pinned ? ' pinned' : '');
    showToast(note.is_pinned ? '已置顶' : '已取消置顶');
    loadNoteList(document.getElementById('search-input').value);
}

async function saveNote(e) {
    e.preventDefault();
    const title = document.getElementById('memo-title').value.trim();
    if (!title) { showToast('标题不能为空', true); return; }
    const body = {
        title, content: document.getElementById('memo-content').value,
        tags: document.getElementById('memo-tags').value
    };
    if (currentNoteId) {
        await api(`/memo/api/notes/${currentNoteId}`, 'PUT', body);
        showToast('笔记已更新');
    } else {
        const resp = await api('/memo/api/notes', 'POST', body);
        currentNoteId = resp.data.id;
        document.getElementById('btn-pin').style.display = '';
        showToast('笔记已创建');
    }
    document.getElementById('auto-save-indicator').classList.remove('visible');
    loadNoteList(document.getElementById('search-input').value);
}

// Double-click to delete
document.addEventListener('dblclick', async function(e) {
    if (e.target.closest('#memo-list .item') && currentNoteId) {
        if (confirm('确认删除此笔记？此操作不可撤销。')) {
            await api(`/memo/api/notes/${currentNoteId}`, 'DELETE');
            showToast('已删除');
            newNote();
        }
    }
});

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
