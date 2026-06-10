var currentTab = 'weight';
var healthChart = null;

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('fdate').value = new Date().toISOString().slice(0, 10);
    document.getElementById('health-form').addEventListener('submit', handleSubmit);
    document.getElementById('val').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); handleSubmit(e); }
    });
    document.querySelectorAll('.tabs button').forEach(function(btn) {
        btn.addEventListener('click', function() { switchTab(btn.dataset.tab); });
    });
    loadDashboard();
    switchTab('weight');
});

async function loadDashboard() {
    var resp = await api('/health/api/dashboard');
    var d = resp.data;
    document.getElementById('dashboard').innerHTML =
        '<div class="card"><div class="value">' + (d.weight || '--') + ' <small style="font-size:14px;">kg</small></div><div class="label">最近体重</div></div>' +
        '<div class="card"><div class="value">' + d.water_total + ' <small style="font-size:14px;">ml</small></div><div class="label">今日饮水</div></div>' +
        '<div class="card"><div class="value">' + d.exercise_today + ' <small style="font-size:14px;">min</small></div><div class="label">今日运动</div></div>' +
        '<div class="card"><div class="value">' + (d.sleep_last ? d.sleep_last.quality + '/5' : '--') + '</div><div class="label">最近睡眠质量</div></div>';
}

function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tabs button').forEach(function(b) { b.classList.remove('active'); });
    document.querySelector('[data-tab="' + tab + '"]').classList.add('active');
    var extra = document.getElementById('extra-field');
    var val = document.getElementById('val');
    var note = document.getElementById('fnote');
    var qa = document.getElementById('quick-actions');
    extra.innerHTML = ''; qa.innerHTML = '';
    val.type = 'text'; val.placeholder = '数值'; val.value = '';
    note.style.display = ''; note.placeholder = '备注'; note.value = '';

    var titles = {weight: '体重趋势', exercise: '运动统计', water: '饮水记录', sleep: '睡眠质量'};
    document.getElementById('chart-title').textContent = titles[tab] || '';
    document.getElementById('table-title').textContent = ({
        weight: '体重记录', exercise: '运动记录', water: '饮水记录', sleep: '睡眠记录'
    })[tab] || '';

    if (tab === 'weight') {
        val.type = 'number'; val.placeholder = '体重 (kg)'; val.step = '0.1';
        qa.innerHTML = ['50','55','60','65','70','75','80','85','90'].map(function(w) {
            return '<button type="button" onclick="document.getElementById(\'val\').value=' + w + '" class="chip">' + w + 'kg</button>';
        }).join('');
    } else if (tab === 'exercise') {
        val.placeholder = '运动类型';
        extra.innerHTML = '<input type="number" id="val2" placeholder="时长(分钟)" min="1"><input type="number" id="val3" placeholder="消耗(千卡)" min="0">';
        qa.innerHTML = ['跑步','散步','游泳','骑行','健身','瑜伽','篮球','跳绳'].map(function(t) {
            return '<button type="button" onclick="document.getElementById(\'val\').value=\'' + t + '\'" class="chip">' + t + '</button>';
        }).join('');
    } else if (tab === 'water') {
        val.type = 'number'; val.placeholder = '饮水量 (ml)'; val.step = '50';
        note.style.display = 'none';
        qa.innerHTML = [
            {l:'小杯 200ml',v:200},{l:'中杯 300ml',v:300},{l:'大杯 500ml',v:500},{l:'水壶 1000ml',v:1000}
        ].map(function(c) {
            return '<button type="button" onclick="quickWater(' + c.v + ')" class="chip">' + c.l + '</button>';
        }).join('');
    } else if (tab === 'sleep') {
        val.placeholder = '入睡 (如 23:00)';
        extra.innerHTML = '<input type="text" id="val2" placeholder="起床 (如 07:00)">';
        note.placeholder = '质量 (1-5)';
        qa.innerHTML = [
            {l:'22:00→06:00 (8h)',s:'22:00',e:'06:00'},
            {l:'23:00→07:00 (8h)',s:'23:00',e:'07:00'},
            {l:'00:00→08:00 (8h)',s:'00:00',e:'08:00'}
        ].map(function(c) {
            return '<button type="button" onclick="quickSleep(\'' + c.s + '\',\'' + c.e + '\')" class="chip">' + c.l + '</button>';
        }).join('');
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
    var resp;
    if (tab === 'weight') resp = await api('/health/api/weight');
    else if (tab === 'exercise') resp = await api('/health/api/exercise');
    else if (tab === 'water') resp = await api('/health/api/water');
    else if (tab === 'sleep') resp = await api('/health/api/sleep');

    var rows = resp.data || [];
    renderTable(tab, rows);
    renderChart(tab, rows);
    renderStats(tab, rows);
}

function renderTable(tab, rows) {
    var headers = {
        weight: ['日期','体重','备注'], exercise: ['日期','类型','时长','卡路里','备注'],
        water: ['日期','饮水量'], sleep: ['日期','入睡','起床','质量','备注']
    };
    var thead = document.getElementById('health-thead');
    thead.innerHTML = '<tr>' + headers[tab].map(function(h) { return '<th>' + h + '</th>'; }).join('') + '<th>操作</th></tr>';
    var tbody = document.getElementById('health-table-body');
    tbody.innerHTML = '';
    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="' + (headers[tab].length + 1) + '" style="text-align:center;color:var(--muted);padding:24px;">暂无数据</td></tr>';
        return;
    }
    rows.forEach(function(r) {
        var tr = document.createElement('tr');
        if (tab === 'weight')
            tr.innerHTML = '<td>' + r.date + '</td><td><strong>' + r.weight + ' kg</strong></td><td>' + (r.note || '-') + '</td><td><button onclick="delRecord(\'weight\',' + r.id + ')" class="btn btn-sm btn-danger">删</button></td>';
        else if (tab === 'exercise')
            tr.innerHTML = '<td>' + r.date + '</td><td>' + r.type + '</td><td>' + r.duration + 'min</td><td>' + (r.calories || 0) + '</td><td>' + (r.note || '-') + '</td><td><button onclick="delRecord(\'exercise\',' + r.id + ')" class="btn btn-sm btn-danger">删</button></td>';
        else if (tab === 'water')
            tr.innerHTML = '<td>' + r.date + '</td><td><strong>' + r.amount + ' ml</strong></td><td><button onclick="delRecord(\'water\',' + r.id + ')" class="btn btn-sm btn-danger">删</button></td>';
        else if (tab === 'sleep')
            tr.innerHTML = '<td>' + r.date + '</td><td>' + r.start_time + '</td><td>' + r.end_time + '</td><td>' + '⭐'.repeat(r.quality) + '</td><td>' + (r.note || '-') + '</td><td><button onclick="delRecord(\'sleep\',' + r.id + ')" class="btn btn-sm btn-danger">删</button></td>';
        tbody.appendChild(tr);
    });
}

function renderChart(tab, rows) {
    if (healthChart) { healthChart.destroy(); healthChart = null; }
    var ctx = document.getElementById('health-chart').getContext('2d');
    if (rows.length < 2 && tab !== 'water') {
        healthChart = new Chart(ctx, {
            type: 'bar', data: {labels: ['暂无足够数据'], datasets: [{data: [0], backgroundColor: 'rgba(0,0,0,0.05)'}]},
            options: {plugins: {legend: {display: false}}}
        });
        return;
    }
    if (tab === 'weight') {
        var labels = rows.map(function(r) { return r.date; }).reverse();
        var data = rows.map(function(r) { return r.weight; }).reverse();
        healthChart = new Chart(ctx, {
            type: 'line', data: {
                labels: labels,
                datasets: [{label: '体重 (kg)', data: data, borderColor: '#3d7a5c', backgroundColor: 'rgba(61,122,92,0.1)', fill: true, tension: 0.3, pointRadius: 4}]
            },
            options: { responsive: true, plugins: {legend: {display: false}}, scales: {y: {beginAtZero: false}}}
        });
    } else if (tab === 'exercise') {
        var byDate = {};
        rows.forEach(function(r) { byDate[r.date] = (byDate[r.date] || 0) + r.duration; });
        var keys = Object.keys(byDate).sort().slice(-14);
        healthChart = new Chart(ctx, {
            type: 'bar', data: {
                labels: keys, datasets: [{label: '运动时长 (min)', data: keys.map(function(k) { return byDate[k]; }),
                backgroundColor: 'rgba(61,122,92,0.6)', borderRadius: 4}]
            },
            options: { responsive: true, plugins: {legend: {display: false}}}
        });
    } else if (tab === 'water') {
        var byDate2 = {};
        rows.forEach(function(r) { byDate2[r.date] = (byDate2[r.date] || 0) + r.amount; });
        var keys2 = Object.keys(byDate2).sort().slice(-14);
        healthChart = new Chart(ctx, {
            type: 'bar', data: {
                labels: keys2, datasets: [{label: '饮水量 (ml)', data: keys2.map(function(k) { return byDate2[k]; }),
                backgroundColor: 'rgba(59,130,246,0.6)', borderRadius: 4}]
            },
            options: { responsive: true, plugins: {legend: {display: false}}}
        });
    } else if (tab === 'sleep') {
        var labels2 = rows.map(function(r) { return r.date; }).reverse().slice(-14);
        var qualities = rows.map(function(r) { return r.quality; }).reverse().slice(-14);
        healthChart = new Chart(ctx, {
            type: 'line', data: {
                labels: labels2, datasets: [{label: '睡眠质量', data: qualities,
                borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)', fill: true, tension: 0.3, pointRadius: 5}]
            },
            options: { responsive: true, plugins: {legend: {display: false}}, scales: {y: {min: 0, max: 5, ticks: {stepSize: 1}}}}
        });
    }
}

function renderStats(tab, rows) {
    var el = document.getElementById('stats-content');
    if (!rows.length) { el.innerHTML = '<p>暂无数据</p>'; return; }
    if (tab === 'weight') {
        var weights = rows.map(function(r) { return r.weight; });
        var avg = (weights.reduce(function(a,b){return a+b;},0) / weights.length).toFixed(1);
        var max = Math.max.apply(null, weights);
        var min = Math.min.apply(null, weights);
        el.innerHTML = '<p>📊 共 <strong>' + rows.length + '</strong> 条记录</p>' +
            '<p>📈 平均：<strong>' + avg + ' kg</strong></p>' +
            '<p>🔺 最高：<strong>' + max + ' kg</strong></p>' +
            '<p>🔻 最低：<strong>' + min + ' kg</strong></p>' +
            '<p>📏 波动：<strong>' + (max - min).toFixed(1) + ' kg</strong></p>';
    } else if (tab === 'exercise') {
        var totalMin = rows.reduce(function(a,b){return a + b.duration;}, 0);
        var totalCal = rows.reduce(function(a,b){return a + (b.calories||0);}, 0);
        var types = {};
        rows.forEach(function(r) { types[r.type] = (types[r.type]||0) + 1; });
        var top = Object.entries(types).sort(function(a,b){return b[1]-a[1];})[0];
        el.innerHTML = '<p>📊 共 <strong>' + rows.length + '</strong> 次运动</p>' +
            '<p>⏱ 总时长：<strong>' + totalMin + ' 分钟</strong></p>' +
            '<p>🔥 总消耗：<strong>' + totalCal + ' 千卡</strong></p>' +
            (top ? '<p>🏅 最爱：<strong>' + top[0] + '</strong>（' + top[1] + '次）</p>' : '');
    } else if (tab === 'water') {
        var total = rows.reduce(function(a,b){return a + b.amount;}, 0);
        var avg2 = Math.round(total / rows.length);
        el.innerHTML = '<p>📊 共 <strong>' + rows.length + '</strong> 条记录</p>' +
            '<p>💧 总计：<strong>' + total + ' ml</strong></p>' +
            '<p>📈 日均：<strong>' + avg2 + ' ml</strong></p>' +
            '<p>🎯 建议：每日 2000-2500 ml</p>';
    } else if (tab === 'sleep') {
        var quals = rows.map(function(r){return r.quality;});
        var avgQ = (quals.reduce(function(a,b){return a+b;},0) / quals.length).toFixed(1);
        el.innerHTML = '<p>📊 共 <strong>' + rows.length + '</strong> 条记录</p>' +
            '<p>⭐ 平均质量：<strong>' + avgQ + ' / 5</strong></p>' +
            '<p>🔺 最高：<strong>' + Math.max.apply(null, quals) + '</strong></p>' +
            '<p>🔻 最低：<strong>' + Math.min.apply(null, quals) + '</strong></p>';
    }
}

async function delRecord(type, id) {
    if (!confirm('确认删除？')) return;
    await api('/health/api/' + type + '/' + id, 'DELETE');
    loadTabData(currentTab);
    loadDashboard();
}

async function handleSubmit(e) {
    e.preventDefault();
    var date = document.getElementById('fdate').value;
    var val = document.getElementById('val').value;
    var val2 = document.getElementById('val2') ? document.getElementById('val2').value : null;
    var note = document.getElementById('fnote').value;
    var url = '', body = {};

    try {
        if (currentTab === 'weight') {
            if (!val || parseFloat(val) <= 0) { showToast('请输入有效体重', true); return; }
            url = '/health/api/weight'; body = {weight: parseFloat(val), date: date, note: note};
        } else if (currentTab === 'exercise') {
            if (!val) { showToast('请输入运动类型', true); return; }
            if (!val2 || parseInt(val2) <= 0) { showToast('请输入运动时长', true); return; }
            var cal = parseFloat(document.getElementById('val3') ? document.getElementById('val3').value : 0) || 0;
            url = '/health/api/exercise'; body = {type: val, duration: parseInt(val2), calories: cal, date: date, note: note};
        } else if (currentTab === 'water') {
            if (!val || parseInt(val) <= 0) { showToast('请输入饮水量', true); return; }
            url = '/health/api/water'; body = {amount: parseInt(val), date: date};
        } else if (currentTab === 'sleep') {
            if (!val || !val2) { showToast('请输入入睡和起床时间', true); return; }
            var quality = parseInt(note) || 3;
            url = '/health/api/sleep';
            body = {start_time: date + ' ' + val, end_time: date + ' ' + val2, quality: Math.min(5,Math.max(1,quality)), date: date};
        }
        var resp = await api(url, 'POST', body);
        if (resp.code === 201) {
            showToast('已记录');
            document.getElementById('val').value = '';
            if (document.getElementById('val2')) document.getElementById('val2').value = '';
            if (document.getElementById('val3')) document.getElementById('val3').value = '';
            document.getElementById('val').focus();
            loadTabData(currentTab);
            loadDashboard();
        } else { showToast(resp.message, true); }
    } catch (err) { showToast('提交失败', true); }
}

// AI refresh
window.addEventListener('ai-refresh', function(e) {
    if (e.detail.module === 'health') { loadTabData(currentTab); loadDashboard(); }
});
