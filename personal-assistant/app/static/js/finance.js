let currentType = 'expense';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('date').value = new Date().toISOString().slice(0, 10);
    document.getElementById('record-form').addEventListener('submit', addRecord);
    document.getElementById('amount').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); addRecord(e); }
    });
    document.getElementById('note').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); addRecord(e); }
    });
    loadCategories();
    loadRecords();
    loadSummary();
    setType('expense');
});

function setType(type) {
    currentType = type;
    document.getElementById('type').value = type;
    const btnE = document.getElementById('btn-expense');
    const btnI = document.getElementById('btn-income');
    btnE.className = 'type-toggle' + (type === 'expense' ? ' active-expense' : '');
    btnI.className = 'type-toggle' + (type === 'income' ? ' active-income' : '');
    document.getElementById('amount').focus();
    loadCategories();
}

function quickAmount(amount) {
    document.getElementById('amount').value = amount;
    document.getElementById('amount').focus();
    document.getElementById('amount').select();
}

async function loadCategories() {
    const resp = await api('/finance/api/categories');
    const select = document.getElementById('category_id');
    select.innerHTML = '';
    const filtered = resp.data.filter(function(c) { return c.type === currentType; });
    if (filtered.length === 0) {
        const opt = document.createElement('option');
        opt.value = ''; opt.textContent = '请先添加分类…'; opt.disabled = true;
        select.appendChild(opt);
    }
    filtered.forEach(function(cat) {
        const opt = document.createElement('option');
        opt.value = cat.id;
        opt.textContent = cat.name;
        select.appendChild(opt);
    });
}

async function loadRecords() {
    const resp = await api('/finance/api/records');
    const tbody = document.querySelector('#records-table tbody');
    tbody.innerHTML = '';
    if (!resp.data || resp.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:30px;">暂无记录<p style="font-size:var(--text-xs);margin-top:4px;">用上方表单添加第一笔</p></td></tr>';
        return;
    }
    resp.data.forEach(function(rec) {
        const tr = document.createElement('tr');
        const color = rec.type === 'income' ? 'var(--success)' : 'var(--danger)';
        tr.innerHTML =
            '<td>' + rec.date + '</td>' +
            '<td><span class="cat-badge" style="background:' + (rec.type === 'income' ? 'var(--accent-soft)' : 'var(--danger-soft)') + ';color:' + color + ';">' + (rec.category_name || '-') + '</span></td>' +
            '<td style="color:' + color + ';font-weight:600;">' + formatAmount(rec.amount, rec.type) + '</td>' +
            '<td>' + (rec.note || '-') + '</td>' +
            '<td><button onclick="deleteRecord(' + rec.id + ')" class="btn btn-sm btn-danger">删除</button></td>';
        tbody.appendChild(tr);
    });
}

async function loadSummary() {
    var now = new Date();
    const resp = await api('/finance/api/summary?year=' + now.getFullYear() + '&month=' + (now.getMonth() + 1));
    const d = resp.data;
    document.getElementById('summary').innerHTML =
        '<div class="card"><div class="value" style="color:var(--success);">+' + d.total_income.toFixed(2) + '</div><div class="label">收入</div></div>' +
        '<div class="card"><div class="value" style="color:var(--danger);">-' + d.total_expense.toFixed(2) + '</div><div class="label">支出</div></div>' +
        '<div class="card"><div class="value" style="color:' + (d.balance >= 0 ? 'var(--success)' : 'var(--danger)') + ';">' + (d.balance >= 0 ? '+' : '') + d.balance.toFixed(2) + '</div><div class="label">结余</div></div>';
}

async function addRecord(e) {
    if (e) e.preventDefault();
    const amount = parseFloat(document.getElementById('amount').value);
    const catId = document.getElementById('category_id').value;
    if (!catId) { showToast('请先添加分类', true); return; }
    if (!amount || amount <= 0) { showToast('请输入有效金额', true); document.getElementById('amount').focus(); return; }
    const data = {
        category_id: parseInt(catId),
        type: currentType,
        amount: amount,
        date: document.getElementById('date').value,
        note: document.getElementById('note').value
    };
    const resp = await api('/finance/api/records', 'POST', data);
    if (resp.code === 201) {
        showToast('已记录 ' + amount.toFixed(2) + ' 元');
        document.getElementById('amount').value = '';
        document.getElementById('note').value = '';
        document.getElementById('amount').focus();
        loadRecords();
        loadSummary();
    } else {
        showToast(resp.message, true);
    }
}

async function deleteRecord(id) {
    if (!confirm('确认删除这条记录？')) return;
    const resp = await api('/finance/api/records/' + id, 'DELETE');
    if (resp.code === 200) { showToast('已删除'); loadRecords(); loadSummary(); }
    else { showToast(resp.message, true); }
}

window.addEventListener("ai-refresh", function(e) {
    if (e.detail.module === "finance") { loadRecords(); loadSummary(); }
});
