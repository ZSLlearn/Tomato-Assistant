async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: {} };
    if (body) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const resp = await fetch(url, opts);
    return resp.json();
}

function showToast(message, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'toast' + (isError ? ' error' : '');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('zh-CN');
}

function formatAmount(amount, type) {
    const prefix = type === 'income' ? '+' : '-';
    return `${prefix}${amount.toFixed(2)}`;
}

// Global AI refresh handler — fires on every page when AI modifies data
window.addEventListener('ai-refresh', function(e) {
    var m = e.detail.module;
    if (!m) return;

    // Call the appropriate refresh function if it exists on current page
    if (m === 'finance') {
        if (typeof loadRecords === 'function') loadRecords();
        if (typeof loadSummary === 'function') loadSummary();
        if (typeof loadCategories === 'function') loadCategories();
    }
    if (m === 'health') {
        if (typeof loadDashboard === 'function') loadDashboard();
        if (typeof loadTabData === 'function' && typeof currentTab !== 'undefined') loadTabData(currentTab);
    }
    if (m === 'schedule') {
        if (typeof loadEvents === 'function') loadEvents();
    }
    if (m === 'memo') {
        if (typeof loadNoteList === 'function') loadNoteList();
    }
    // For dashboard pages that have dashboard cards
    if (typeof refreshDashboard === 'function') refreshDashboard();
});
