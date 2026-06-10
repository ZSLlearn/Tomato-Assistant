document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('city-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') searchWeather();
    });
    loadDefaultCity();
});

async function loadDefaultCity() {
    try {
        const resp = await api('/settings/api/config');
        const city = resp.data.default_city;
        if (city) {
            document.getElementById('city-input').value = city;
            searchWeather();
        }
    } catch (e) {}
}

async function searchWeather() {
    const city = document.getElementById('city-input').value.trim();
    if (!city) { showToast('请输入城市名', true); return; }

    const result = document.getElementById('weather-result');
    result.innerHTML = '<p style="color:var(--muted);">查询中…</p>';

    try {
        const nowResp = await api('/weather/api/now?city=' + encodeURIComponent(city));
        const forecastResp = await api('/weather/api/forecast?city=' + encodeURIComponent(city) + '&days=7');

        if (nowResp.code !== 200) {
            result.innerHTML = '<p style="color:var(--danger);">' + nowResp.message + '</p>';
            return;
        }

        const now = nowResp.data;
        result.innerHTML =
            '<div class="weather-now">' +
                '<div>' +
                    '<div style="font-size:var(--text-lg);font-weight:600;margin-bottom:4px;">' + now.city + '</div>' +
                    '<div class="temp">' + now.temp + '&deg;C</div>' +
                    '<div style="color:var(--muted);">' + now.text + '</div>' +
                '</div>' +
                '<div style="text-align:right;font-size:var(--text-sm);color:var(--muted);line-height:1.8;">' +
                    '<div>体感 ' + now.feels_like + '&deg;C</div>' +
                    '<div>湿度 ' + now.humidity + '%</div>' +
                    '<div>' + now.wind_dir + ' ' + now.wind_speed + '</div>' +
                '</div>' +
            '</div>';

        if (forecastResp.code === 200 && forecastResp.data.length > 0) {
            var forecastHTML = '<div class="section-header" style="margin-top:20px;">7 天预报</div><div class="forecast-list">';
            forecastResp.data.forEach(function(d) {
                forecastHTML += '<div class="forecast-item">' +
                    '<div class="day">' + d.date.slice(5) + '</div>' +
                    '<div class="icon">' + d.text_day + '</div>' +
                    '<div class="temps"><span class="high">' + d.temp_max + '&deg;</span> <span class="low">' + d.temp_min + '&deg;</span></div>' +
                '</div>';
            });
            forecastHTML += '</div>';
            result.innerHTML += forecastHTML;
        }
    } catch (e) {
        result.innerHTML = '<p style="color:var(--danger);">天气服务不可用: ' + e.message + '</p>';
    }
}
