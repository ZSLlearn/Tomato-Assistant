let currentTab = 'weight';

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('fdate').value = new Date().toISOString().slice(0, 10);
    document.getElementById('health-form').addEventListener('submit', handleSubmit);
    document.getElementById('val').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); handleSubmit(e); }
    });
    document.querySelectorAll('.tabs button').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    loadDashboard();
    switchTab('weight');
});

async function loadDashboard() {
    const resp = await api('/health/api/dashboard');
    const d = resp.data;
    document.getElementById('dashboard').innerHTML =
        `<div class="card"><div class="value">${d.weight || '--'} <small style="font-size:14px;">kg</small></div><div class="label">最近体重</div></div>
         <div class="card"><div class="value">${d.water_total} <small style="font-size:14px;">ml</small></div><div class="label">今日饮水</div></div>
         <div class="card"><div class="value">${d.exercise_today} <small style="font-size:14px;">min</small></div><div class="label">今日运动</div></div>
         <div class="card"><div class="value">${d.sleep_last ? d.sleep_last.quality + '/5' : '--'}</div><div class="label">最近睡眠质量</div></div>`;
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
    const extra = document.getElementById('extra-field');
    const val = document.getElementById('val');
    const note = document.getElementById('fnote');
    const qa = document.getElementById('quick-actions');
    extra.innerHTML = ''; qa.innerHTML = '';
    val.type = 'text'; val.placeholder = '数值'; val.value = '';
    note.style.display = ''; note.placeholder = '备注'; note.value = '';

    if (tab === 'weight') {
        val.type = 'number'; val.placeholder = '体重 (kg)'; val.step = '0.1';
        qa.innerHTML = '<span style="font-size:12px;color:var(--text-muted);">快速记录：</span>' +
            ['50','55','60','65','70','75','80','85','90'].map(w => `<button type="button" onclick="document.getElementById('val').value=${w}" class="chip">${w}kg</button>`).join('');
    } else if (tab === 'exercise') {
        val.placeholder = '运动类型';
        extra.innerHTML = '<input type="number" id="val2" placeholder="时长(分钟)" min="1" style="padding:12px;flex:1;min-width:100px;">' +
            '<input type="number" id="val3" placeholder="消耗(千卡)" min="0" style="padding:12px;flex:0;min-width:100px;">';
        qa.innerHTML = '<span style="font-size:12px;color:var(--text-muted);">常见运动：</span>' +
            ['跑步','散步','游泳','骑行','健身','瑜伽','篮球','跳绳'].map(t => `<button type="button" onclick="document.getElementById('val').value='${t}'" class="chip">${t}</button>`);
    } else if (tab === 'water') {
        val.type = 'number'; val.placeholder = '饮水量 (ml)'; val.step = '50';
        note.style.display = 'none';
        qa.innerHTML = '<span style="font-size:12px;color:var(--text-muted);">快速记录一杯：</span>' +
            [{l:'🧊 小杯 200ml',v:200},{l:'🥛 中杯 300ml',v:300},{l:'🫗 大杯 500ml',v:500},{l:'🍶 水壶 1000ml',v:1000}]
                .map(c => `<button type="button" onclick="quickWater(${c.v})" class="chip">${c.l}</button>`).join('');
    } else if (tab === 'sleep') {
        val.placeholder = '入睡 (如 23:00)';
        extra.innerHTML = '<input type="text" id="val2" placeholder="起床 (如 07:00)" style="padding:12px;flex:1;">';
        note.placeholder = '质量 (1-5)';
        qa.innerHTML = '<span style="font-size:12px;color:var(--text-muted);">快速设置：</span>' +
            [{l:'🌙 22:00→06:00 (8h)',s:'22:00',e:'06:00'},
             {l:'🌙 23:00→07:00 (8h)',s:'23:00',e:'07:00'},
             {l:'🌙 00:00→08:00 (8h)',s:'00:00',e:'08:00'}]
                .map(c => `<button type="button" onclick="quickSleep('${c.s}','${c.e}')" class="chip">${c.l}</button>`).join('');
    }
    val.focus();
    loadTabData(tab);
}

function quickWater(ml) {
    document.getElementById('val').value = ml;
    document.getElementById('health-form').requestSubmit();
}

function quickSleep(start, end) {
    document.getElementById('val').value = start;
    document.getElementById('val2').value = end;
    document.getElementById('fnote').value = '3';
}

async function loadTabData(tab) {
    let resp;
    if (tab === 'weight') resp = await api('/health/api/weight');
    else if (tab === 'exercise') resp = await api('/health/api/exercise');
    else if (tab === 'water') resp = await api('/health/api/water');
    else if (tab === 'sleep') resp = await api('/health/api/sleep');

    const rows = resp.data;
    const tbody = document.getElementById('health-table-body');
    const thead = document.querySelector('#health-table-wrap thead');
    const headers = {
        weight: ['日期','体重','备注'], exercise: ['日期','类型','时长','卡路里','备注'],
        water: ['日期','饮水量'], sleep: ['日期','入睡','起床','质量','备注']
    };
    thead.innerHTML = '<tr>' + headers[tab].map(h => `<th>${h}</th>`).join('') + '<th>操作</th></tr>';
    tbody.innerHTML = '';
    if (!rows || rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-state">📭 暂无数据<br><small>用上方表单添加记录吧</small></td></tr>';
        return;
    }
    rows.forEach(r => {
        const tr = document.createElement('tr');
        if (tab === 'weight') tr.innerHTML = `<td>${r.date}</td><td>${r.weight} kg</td><td>${r.note || '-'}</td><td><button onclick="delRecord('weight',${r.id})" class="danger" style="padding:4px 10px;font-size:12px;">删除</button></td>`;
        else if (tab === 'exercise') tr.innerHTML = `<td>${r.date}</td><td>${r.type}</td><td>${r.duration}min</td><td>${r.calories || 0}</td><td>${r.note || '-'}</td><td><button onclick="delRecord('exercise',${r.id})" class="danger" style="padding:4px 10px;font-size:12px;">删除</button></td>`;
        else if (tab === 'water') tr.innerHTML = `<td>${r.date}</td><td>${r.amount} ml</td><td><button onclick="delRecord('water',${r.id})" class="danger" style="padding:4px 10px;font-size:12px;">删除</button></td>`;
        else if (tab === 'sleep') tr.innerHTML = `<td>${r.date}</td><td>${r.start_time}</td><td>${r.end_time}</td><td>${'⭐'.repeat(r.quality)}</td><td>${r.note || '-'}</td><td><button onclick="delRecord('sleep',${r.id})" class="danger" style="padding:4px 10px;font-size:12px;">删除</button></td>`;
        tbody.appendChild(tr);
    });
}

async function delRecord(type, id) {
    if (!confirm('确认删除？')) return;
    await api(`/health/api/${type}/${id}`, 'DELETE');
    loadTabData(currentTab);
    loadDashboard();
}

async function handleSubmit(e) {
    e.preventDefault();
    const date = document.getElementById('fdate').value;
    const val = document.getElementById('val').value;
    const val2 = document.getElementById('val2')?.value;
    const note = document.getElementById('fnote').value;
    let url = '', body = {};

    try {
        if (currentTab === 'weight') {
            if (!val || parseFloat(val) <= 0) { showToast('请输入有效体重', true); return; }
            url = '/health/api/weight'; body = { weight: parseFloat(val), date, note };
        } else if (currentTab === 'exercise') {
            if (!val) { showToast('请输入运动类型', true); return; }
            if (!val2 || parseInt(val2) <= 0) { showToast('请输入运动时长', true); return; }
            const calories = parseFloat(document.getElementById('val3')?.value) || 0;
            url = '/health/api/exercise'; body = { type: val, duration: parseInt(val2), calories, date, note };
        } else if (currentTab === 'water') {
            if (!val || parseInt(val) <= 0) { showToast('请输入饮水量', true); return; }
            url = '/health/api/water'; body = { amount: parseInt(val), date };
        } else if (currentTab === 'sleep') {
            if (!val || !val2) { showToast('请输入入睡和起床时间', true); return; }
            const quality = parseInt(note) || 3;
            url = '/health/api/sleep';
            body = { start_time: `${date} ${val}`, end_time: `${date} ${val2}`, quality: Math.min(5, Math.max(1, quality)), date };
        }
        const resp = await api(url, 'POST', body);
        if (resp.code === 201) {
            const emoji = {weight:'⚖️',exercise:'🏃',water:'💧',sleep:'😴'};
            showToast(emoji[currentTab] + ' 记录成功');
            document.getElementById('val').value = '';
            if (document.getElementById('val2')) document.getElementById('val2').value = '';
            if (document.getElementById('val3')) document.getElementById('val3').value = '';
            document.getElementById('val').focus();
            loadTabData(currentTab);
            loadDashboard();
        } else { showToast(resp.message, true); }
    } catch (err) { showToast('提交失败', true); }
}
