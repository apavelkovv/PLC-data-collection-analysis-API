/* ────────────────────────────────────────────────────────────────────────────
   app.js — LabControl SPA
   ──────────────────────────────────────────────────────────────────────────── */

let state = {
    currentUser: null,
    experiments: [],
    stands: [],
    currentExperiment: null,
    telemetryInterval: null,
    activeTab: 'experiments',
    telemetryHistory: {}, // { paramName: [{ value, recorded_at }] }
    selectedParam: null,
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function fmtDateTime(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('ru-RU');
}

function statusTag(status) {
    const map = {
        'created':  ['tag-neutral', 'Создан'],
        'running':  ['tag-green',   'Идёт'],
        'paused':   ['tag-amber',   'Пауза'],
        'stopped':  ['tag-red',     'Остановлен'],
        'finished': ['tag-blue',    'Завершён'],
    };
    const [cls, label] = map[status] || ['tag-neutral', status];
    return `<span class="tag ${cls}"><span class="tag-dot"></span>${label}</span>`;
}

function severityTag(severity) {
    const map = { info: 'tag-blue', warning: 'tag-amber', critical: 'tag-red', error: 'tag-red' };
    return `<span class="tag ${map[severity] || 'tag-neutral'}">${severity}</span>`;
}

function roleTag(role) {
    const map = { admin: 'tag-red', teacher: 'tag-blue', student: 'tag-neutral' };
    return `<span class="tag ${map[role] || 'tag-neutral'}">${role}</span>`;
}

function showToast(msg, type = 'info') {
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    document.getElementById('toast-container').appendChild(t);
    setTimeout(() => t.classList.add('show'), 10);
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, 3000);
}

function setLoading(id, loading) {
    const el = document.getElementById(id);
    if (!el) return;
    el.disabled = loading;
    el.dataset.orig = el.dataset.orig || el.textContent;
    el.textContent = loading ? '...' : el.dataset.orig;
}

// ─── Init ─────────────────────────────────────────────────────────────────────

async function init() {
    try {
        state.currentUser = await api.getMe();
    } catch {
        window.location.href = 'login.html';
        return;
    }
    updateUserFooter();
    updateNavForRole();
    await loadExperimentsList();
    await loadStandsList();
    switchTab('experiments');

    document.getElementById('btn-logout').addEventListener('click', api.logout);
}

function updateUserFooter() {
    const u = state.currentUser;
    if (!u) return;
    const initials = u.username.slice(0, 2).toUpperCase();
    document.getElementById('user-ava').textContent = initials;
    document.getElementById('user-name').textContent = u.username;
    document.getElementById('user-role').textContent = `${u.role.toUpperCase()}`;
}

function updateNavForRole() {
    const role = state.currentUser?.role;
    const adminItems = document.querySelectorAll('[data-role="admin"]');
    const teacherItems = document.querySelectorAll('[data-role="teacher-admin"]');
    adminItems.forEach(el => { el.style.display = role === 'admin' ? '' : 'none'; });
    teacherItems.forEach(el => { el.style.display = (role === 'admin' || role === 'teacher') ? '' : 'none'; });
}

// ─── Tab Switching ────────────────────────────────────────────────────────────

function switchTab(tab) {
    state.activeTab = tab;
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.nav-item[data-tab]').forEach(n => n.classList.remove('active'));
    const panel = document.getElementById(`tab-${tab}`);
    if (panel) panel.classList.remove('hidden');
    const navItem = document.querySelector(`.nav-item[data-tab="${tab}"]`);
    if (navItem) navItem.classList.add('active');

    // Update breadcrumb section title
    const tabNames = { experiments: 'Эксперименты', stands: 'Стенды', users: 'Пользователи', logs: 'Логи системы' };
    const sectionEl = document.getElementById('breadcrumb-section');
    if (sectionEl) sectionEl.textContent = tabNames[tab] || tab;

    if (tab === 'experiments') renderExperimentsTab();
    if (tab === 'stands') renderStandsTab();
    if (tab === 'users') renderUsersTab();
    if (tab === 'logs') renderLogsTab();
}

document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', () => switchTab(item.dataset.tab));
});

// ─── EXPERIMENTS TAB ──────────────────────────────────────────────────────────

async function loadExperimentsList() {
    state.experiments = await api.getExperiments() || [];
}

async function renderExperimentsTab() {
    await loadExperimentsList();
    const select = document.getElementById('exp-list-select');
    const prevVal = select.value;
    select.innerHTML = '<option value="">Выберите эксперимент...</option>';
    state.experiments.forEach(exp => {
        const opt = document.createElement('option');
        opt.value = exp.id;
        opt.textContent = `${exp.title} (${exp.status})`;
        select.appendChild(opt);
    });
    if (prevVal) select.value = prevVal;

    // Populate stands in create modal
    const standsSelect = document.getElementById('select-stand');
    standsSelect.innerHTML = '';
    state.stands.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.textContent = s.name;
        standsSelect.appendChild(opt);
    });

    if (state.currentExperiment) {
        loadExperimentView(state.currentExperiment.id);
    } else {
        showEmptyView();
    }
}

function showEmptyView() {
    document.getElementById('view-empty').classList.remove('hidden');
    document.getElementById('view-main').classList.add('hidden');
    stopTelemetryPolling();
}

async function loadExperimentView(id) {
    if (!id) { showEmptyView(); return; }
    try {
        const exp = await api.getExperiment(id);
        state.currentExperiment = exp;
        document.getElementById('view-empty').classList.add('hidden');
        document.getElementById('view-main').classList.remove('hidden');
        renderExperimentView(exp);
        startTelemetryPolling(id);
    } catch {
        showToast('Ошибка загрузки эксперимента', 'error');
        showEmptyView();
    }
}

function renderExperimentView(exp) {
    document.getElementById('exp-title').textContent = exp.title;
    document.getElementById('exp-id-tag').textContent = `#EXP-${exp.id}`;
    document.getElementById('exp-status-tag').innerHTML = statusTag(exp.status);
    document.getElementById('exp-stand-id').textContent = exp.stand_id;

    const stand = state.stands.find(s => s.id === exp.stand_id);
    document.getElementById('exp-stand-name').textContent = stand ? stand.name : `Стенд #${exp.stand_id}`;
    document.getElementById('exp-started-at').textContent = exp.started_at ? `Запущен: ${fmtDate(exp.started_at)}` : 'Не запущен';
    document.getElementById('exp-description').textContent = exp.description || '—';

    // Breadcrumb
    document.getElementById('breadcrumb-exp').textContent = `EXP-${exp.id} — ${exp.title}`;

    // Buttons
    const status = exp.status;
    document.getElementById('btn-start').disabled = status === 'running';
    document.getElementById('btn-pause').disabled = status !== 'running';
    document.getElementById('btn-stop').disabled = status === 'stopped' || status === 'finished' || status === 'created';
    document.getElementById('btn-export-csv').disabled = false;
}

// Telemetry polling
function startTelemetryPolling(expId) {
    stopTelemetryPolling();
    state.telemetryHistory = {};
    state.selectedParam = null;
    refreshTelemetry(expId);
    loadExperimentEvents(expId);
    state.telemetryInterval = setInterval(() => {
        refreshTelemetry(expId);
        loadExperimentEvents(expId);
    }, 2500);
}

function stopTelemetryPolling() {
    if (state.telemetryInterval) {
        clearInterval(state.telemetryInterval);
        state.telemetryInterval = null;
    }
}

async function refreshTelemetry(expId) {
    try {
        const data = await api.getTelemetry(expId, { limit: 200 });
        if (!data || !data.length) {
            // Нет данных — сбрасываем отображение
            document.getElementById('params-grid').innerHTML =
                '<div style="padding:20px;text-align:center;color:var(--ink4);font-size:12px;grid-column:1/-1;">Нет данных телеметрии</div>';
            
            document.getElementById('tele-val').textContent = '—';
            document.getElementById('tele-unit').textContent = 'нет данных';
            document.getElementById('tele-unit-tab').textContent = 'нет данных';
            document.getElementById('tele-trend').textContent = '—';
            document.getElementById('tele-trend').className = 'chart-cur-delta delta-ok';
            document.getElementById('tele-time').textContent = '—';
            document.getElementById('tele-min').textContent = '—';
            document.getElementById('tele-max').textContent = '—';

            const canvas = document.getElementById('tele-sparkline');
            if (canvas) canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
            return;
        }
        renderTelemetry(data);
    } catch { /* silent */ }
}

function renderTelemetry(records) {
    // Group by parameter
    const grouped = {};
    records.forEach(r => {
        if (!grouped[r.parameter_name]) grouped[r.parameter_name] = [];
        grouped[r.parameter_name].push(r);
    });

    const container = document.getElementById('params-grid');
    container.innerHTML = '';

    const paramNames = Object.keys(grouped);

    // Ensure selected param is valid
    if (!state.selectedParam || !grouped[state.selectedParam]) {
        state.selectedParam = paramNames[0] || null;
    }

    Object.entries(grouped).forEach(([name, values]) => {
        values.sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at));
        const latest = values[values.length - 1];
        const cell = document.createElement('div');
        const isSelected = name === state.selectedParam;
        cell.className = 'param-cell' + (isSelected ? ' param-cell-active' : '');
        cell.style.cursor = 'pointer';
        const trend = values.length > 1
            ? (latest.value > values[values.length - 2].value ? '↑' : '↓')
            : '—';
        cell.innerHTML = `
            <div class="param-name">${name}</div>
            <div class="param-value">${latest.value.toFixed(2)}<span class="param-unit">${latest.unit || ''}</span></div>
            <div class="param-trend">${trend} последнее</div>
        `;
        cell.addEventListener('click', () => {
            state.selectedParam = name;
            renderTelemetry(records);
        });
        container.appendChild(cell);
    });

    // Show big value and sparkline for selected param
    const selectedRecords = state.selectedParam && grouped[state.selectedParam]
        ? grouped[state.selectedParam]
        : [];

    if (selectedRecords.length) {
        const last = selectedRecords[selectedRecords.length - 1];
        const prev = selectedRecords.length > 1 ? selectedRecords[selectedRecords.length - 2] : last;

        document.getElementById('tele-val').textContent = last.value.toFixed(2);
        document.getElementById('tele-unit').textContent = last.unit || '';
        document.getElementById('tele-unit-tab').textContent = last.parameter_name;
        document.getElementById('tele-time').textContent = fmtDateTime(last.recorded_at);

        const vals = selectedRecords.map(r => r.value);
        document.getElementById('tele-min').textContent = Math.min(...vals).toFixed(2);
        document.getElementById('tele-max').textContent = Math.max(...vals).toFixed(2);

        const trendEl = document.getElementById('tele-trend');
        const diff = last.value - prev.value;
        if (diff > 0) {
            trendEl.textContent = '↑ +' + diff.toFixed(2);
            trendEl.className = 'chart-cur-delta delta-up';
        } else if (diff < 0) {
            trendEl.textContent = '↓ ' + diff.toFixed(2);
            trendEl.className = 'chart-cur-delta delta-down';
        } else {
            trendEl.textContent = '— ст.';
            trendEl.className = 'chart-cur-delta delta-ok';
        }

        drawSparkline(selectedRecords);
    }
}

function drawSparkline(records) {
    const canvas = document.getElementById('tele-sparkline');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Fit canvas to container size dynamically
    const rect = canvas.parentElement.getBoundingClientRect();
    const W = rect.width;
    const H = rect.height;
    if (canvas.width !== W) canvas.width = W;
    if (canvas.height !== H) canvas.height = H;

    ctx.clearRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = '#E2E5EE';
    ctx.lineWidth = 1;
    ctx.beginPath();
    const gridSteps = 4;
    for (let i = 1; i <= gridSteps; i++) {
        const y = (H / gridSteps) * i;
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
    }
    ctx.stroke();

    if (records.length < 2) return;
    const values = records.map(r => r.value);
    const min = Math.min(...values), max = Math.max(...values);
    const range = max - min || 1;

    // Map points to canvas coordinates with padding
    const points = values.map((v, i) => {
        const x = (i / (values.length - 1)) * W;
        const y = H - ((v - min) / range) * (H * 0.7) - (H * 0.15);
        return { x, y };
    });

    // Fill Gradient
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, 'rgba(26,107,255,0.12)');
    grad.addColorStop(1, 'rgba(26,107,255,0)');

    ctx.beginPath();
    ctx.moveTo(points[0].x, H);
    ctx.lineTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    const lastP = points[points.length - 1];
    ctx.lineTo(lastP.x, lastP.y);
    ctx.lineTo(lastP.x, H);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Smooth Line Stroke
    ctx.beginPath();
    ctx.strokeStyle = '#1A6BFF';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    ctx.lineTo(lastP.x, lastP.y);
    ctx.stroke();

    // Live End Dot
    ctx.beginPath();
    ctx.arc(lastP.x, lastP.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = '#1A6BFF';
    ctx.fill();

    // Halo around dot
    ctx.beginPath();
    ctx.arc(lastP.x, lastP.y, 7, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(26,107,255,0.3)';
    ctx.lineWidth = 1;
    ctx.stroke();
}

async function loadExperimentEvents(expId) {
    try {
        const events = await api.getExperimentEvents(expId, 0, 50);
        renderEventLog(events, 'exp-event-log');
    } catch { /* silent */ }
}

function renderEventLog(events, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (!events || !events.length) {
        container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--ink4);">Нет событий</div>';
        return;
    }
    container.innerHTML = events.slice(0, 50).map(e => {
        const colorMap = { info: 'blue', warning: 'amber', critical: 'red', error: 'red' };
        const color = colorMap[e.severity] || 'blue';
        const time = new Date(e.created_at).toLocaleTimeString('ru-RU');
        return `
        <div class="log-entry">
            <span class="log-time">${time}</span>
            <span class="log-indicator ${color}"></span>
            <span class="log-msg"><strong>${e.event_type}</strong> — ${e.message}</span>
        </div>`;
    }).join('');
}

// Experiment buttons
document.getElementById('exp-list-select').addEventListener('change', e => {
    const id = parseInt(e.target.value);
    if (id) loadExperimentView(id); else showEmptyView();
});

document.getElementById('btn-start').addEventListener('click', async () => {
    if (!state.currentExperiment) return;
    setLoading('btn-start', true);
    try {
        const exp = await api.startExperiment(state.currentExperiment.id);
        state.currentExperiment = exp;
        renderExperimentView(exp);
        showToast('Эксперимент запущен', 'success');
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-start', false);
});

document.getElementById('btn-pause').addEventListener('click', async () => {
    if (!state.currentExperiment) return;
    setLoading('btn-pause', true);
    try {
        const exp = await api.pauseExperiment(state.currentExperiment.id);
        state.currentExperiment = exp;
        renderExperimentView(exp);
        showToast('Эксперимент на паузе', 'success');
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-pause', false);
});

document.getElementById('btn-stop').addEventListener('click', async () => {
    if (!state.currentExperiment) return;
    if (!confirm('Остановить эксперимент? Это действие нельзя отменить.')) return;
    setLoading('btn-stop', true);
    try {
        const exp = await api.stopExperiment(state.currentExperiment.id);
        state.currentExperiment = exp;
        renderExperimentView(exp);
        stopTelemetryPolling();
        showToast('Эксперимент остановлен', 'success');
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-stop', false);
});

document.getElementById('btn-export-csv').addEventListener('click', async () => {
    if (!state.currentExperiment) return;
    try {
        await api.exportCsv(state.currentExperiment.id);
        showToast('Экспорт CSV начат', 'success');
    } catch (e) { showToast(e.message, 'error'); }
});

// Create experiment modal
document.getElementById('open-create-modal').addEventListener('click', () => {
    document.getElementById('modal-create').classList.remove('hidden');
});
document.getElementById('btn-cancel-create').addEventListener('click', () => {
    document.getElementById('modal-create').classList.add('hidden');
});
document.getElementById('btn-confirm-create').addEventListener('click', async () => {
    const name = document.getElementById('input-exp-name').value.trim();
    const standId = parseInt(document.getElementById('select-stand').value);
    const desc = document.getElementById('input-exp-desc').value.trim();
    if (!name) { showToast('Введите название', 'error'); return; }
    if (!standId) { showToast('Выберите стенд', 'error'); return; }
    setLoading('btn-confirm-create', true);
    try {
        const newExp = await api.createExperiment(name, standId, desc);
        document.getElementById('modal-create').classList.add('hidden');
        document.getElementById('input-exp-name').value = '';
        document.getElementById('input-exp-desc').value = '';
        await loadExperimentsList();
        await renderExperimentsTab();
        document.getElementById('exp-list-select').value = newExp.id;
        loadExperimentView(newExp.id);
        showToast('Эксперимент создан', 'success');
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-confirm-create', false);
});

// ─── STANDS TAB ───────────────────────────────────────────────────────────────

async function loadStandsList() {
    state.stands = await api.getStands() || [];
}

async function renderStandsTab() {
    await loadStandsList();
    const tbody = document.getElementById('stands-tbody');
    if (!state.stands.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--ink4);">Стенды не найдены</td></tr>';
        return;
    }
    tbody.innerHTML = state.stands.map(s => `
        <tr>
            <td><span class="mono">#${s.id}</span></td>
            <td><strong>${s.name}</strong>${s.description ? `<div style="font-size:11px;color:var(--ink3);margin-top:2px;">${s.description}</div>` : ''}</td>
            <td><span class="mono">${s.plc_host}:${s.plc_port}</span></td>
            <td>${s.is_active ? '<span class="tag tag-green"><span class="tag-dot"></span>Активен</span>' : '<span class="tag tag-neutral">Неактивен</span>'}</td>
            <td><span class="mono">${fmtDate(s.created_at)}</span></td>
            <td class="actions-cell">
                <button class="btn-icon" onclick="openStandModal(${s.id})" title="Редактировать">✏️</button>
                <button class="btn-icon btn-icon-danger" onclick="deleteStand(${s.id})" title="Удалить">🗑</button>
            </td>
        </tr>
    `).join('');
}

function openStandModal(id = null) {
    const stand = id ? state.stands.find(s => s.id === id) : null;
    document.getElementById('stand-modal-title').textContent = stand ? 'Редактировать стенд' : 'Новый стенд';
    document.getElementById('stand-modal-id').value = id || '';
    document.getElementById('stand-input-name').value = stand?.name || '';
    document.getElementById('stand-input-desc').value = stand?.description || '';
    document.getElementById('stand-input-host').value = stand?.plc_host || '';
    document.getElementById('stand-input-port').value = stand?.plc_port || 502;
    if (stand) {
        document.getElementById('stand-active-row').style.display = '';
        document.getElementById('stand-input-active').checked = stand.is_active;
    } else {
        document.getElementById('stand-active-row').style.display = 'none';
    }
    document.getElementById('modal-stand').classList.remove('hidden');
}

document.getElementById('btn-cancel-stand').addEventListener('click', () => {
    document.getElementById('modal-stand').classList.add('hidden');
});

document.getElementById('btn-save-stand').addEventListener('click', async () => {
    const id = document.getElementById('stand-modal-id').value;
    const data = {
        name: document.getElementById('stand-input-name').value.trim(),
        description: document.getElementById('stand-input-desc').value.trim() || null,
        plc_host: document.getElementById('stand-input-host').value.trim(),
        plc_port: parseInt(document.getElementById('stand-input-port').value),
    };
    if (id) data.is_active = document.getElementById('stand-input-active').checked;
    if (!data.name || !data.plc_host) { showToast('Заполните обязательные поля', 'error'); return; }
    setLoading('btn-save-stand', true);
    try {
        if (id) {
            await api.updateStand(parseInt(id), data);
            showToast('Стенд обновлён', 'success');
        } else {
            await api.createStand(data);
            showToast('Стенд создан', 'success');
        }
        document.getElementById('modal-stand').classList.add('hidden');
        await loadStandsList();
        renderStandsTab();
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-save-stand', false);
});

async function deleteStand(id) {
    if (!confirm('Удалить стенд? Все эксперименты стенда будут удалены.')) return;
    try {
        await api.deleteStand(id);
        showToast('Стенд удалён', 'success');
        await loadStandsList();
        renderStandsTab();
    } catch (e) { showToast(e.message, 'error'); }
}

document.getElementById('btn-add-stand').addEventListener('click', () => openStandModal());

// ─── USERS TAB ────────────────────────────────────────────────────────────────

async function renderUsersTab() {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--ink4);">Загрузка...</td></tr>';
    try {
        const users = await api.getUsers();
        if (!users || !users.length) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--ink4);">Пользователи не найдены</td></tr>';
            return;
        }
        tbody.innerHTML = users.map(u => `
            <tr>
                <td><span class="mono">#${u.id}</span></td>
                <td><strong>${u.username}</strong></td>
                <td>${u.email}</td>
                <td>${roleTag(u.role)}</td>
                <td>${u.is_active ? '<span class="tag tag-green"><span class="tag-dot"></span>Активен</span>' : '<span class="tag tag-red">Заблокирован</span>'}</td>
                <td><span class="mono">${fmtDate(u.created_at)}</span></td>
                <td class="actions-cell">
                    <button class="btn-icon" onclick="openUserModal(${u.id})" title="Редактировать">✏️</button>
                    <button class="btn-icon btn-icon-danger" onclick="deleteUser(${u.id})" title="Удалить">🗑</button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--red);">${e.message}</td></tr>`;
    }
}

let editingUserId = null;
async function openUserModal(id) {
    editingUserId = id;
    const user = await api.getUser(id);
    document.getElementById('user-modal-email').value = user.email;
    document.getElementById('user-modal-role').value = user.role;
    document.getElementById('user-modal-active').checked = user.is_active;
    document.getElementById('modal-user').classList.remove('hidden');
}

document.getElementById('btn-cancel-user').addEventListener('click', () => {
    document.getElementById('modal-user').classList.add('hidden');
});

document.getElementById('btn-save-user').addEventListener('click', async () => {
    const data = {
        email: document.getElementById('user-modal-email').value.trim(),
        role: document.getElementById('user-modal-role').value,
        is_active: document.getElementById('user-modal-active').checked,
    };
    setLoading('btn-save-user', true);
    try {
        await api.updateUser(editingUserId, data);
        showToast('Пользователь обновлён', 'success');
        document.getElementById('modal-user').classList.add('hidden');
        renderUsersTab();
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-save-user', false);
});

document.getElementById('btn-add-user').addEventListener('click', () => {
    document.getElementById('modal-register').classList.remove('hidden');
});
document.getElementById('btn-cancel-register').addEventListener('click', () => {
    document.getElementById('modal-register').classList.add('hidden');
});
document.getElementById('btn-save-register').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('reg-username').value.trim(),
        email: document.getElementById('reg-email').value.trim(),
        password: document.getElementById('reg-password').value,
        role: document.getElementById('reg-role').value,
    };
    if (!data.username || !data.email || !data.password) { showToast('Заполните все поля', 'error'); return; }
    setLoading('btn-save-register', true);
    try {
        await api.register(data.username, data.email, data.password, data.role);
        showToast('Пользователь создан', 'success');
        document.getElementById('modal-register').classList.add('hidden');
        renderUsersTab();
    } catch (e) { showToast(e.message, 'error'); }
    setLoading('btn-save-register', false);
});

async function deleteUser(id) {
    if (id === state.currentUser?.id) { showToast('Нельзя удалить себя', 'error'); return; }
    if (!confirm('Удалить пользователя?')) return;
    try {
        await api.deleteUser(id);
        showToast('Пользователь удалён', 'success');
        renderUsersTab();
    } catch (e) { showToast(e.message, 'error'); }
}

// ─── LOGS TAB ─────────────────────────────────────────────────────────────────

async function renderLogsTab() {
    const container = document.getElementById('global-event-log');
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--ink4);">Загрузка...</div>';
    try {
        const severity = document.getElementById('log-filter-severity').value;
        const params = { limit: 200 };
        if (severity) params.severity = severity;
        const events = await api.getGlobalEvents(params);
        if (!events || !events.length) {
            container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--ink4);">Нет событий</div>';
            return;
        }
        container.innerHTML = events.map(e => {
            const colorMap = { info: 'blue', warning: 'amber', critical: 'red', error: 'red' };
            const color = colorMap[e.severity] || 'blue';
            const dt = fmtDateTime(e.created_at);
            return `
            <div class="log-entry" style="border-bottom: 1px solid var(--bg2);">
                <span class="log-time" style="min-width:130px;">${dt}</span>
                <span class="log-indicator ${color}"></span>
                <span class="log-msg" style="flex:1;">
                    <strong>${e.event_type}</strong> — ${e.message}
                    ${e.experiment_id ? `<span class="mono" style="color:var(--ink4);margin-left:8px;">#EXP-${e.experiment_id}</span>` : ''}
                </span>
                <span>${severityTag(e.severity)}</span>
            </div>`;
        }).join('');
    } catch (e) {
        container.innerHTML = `<div style="padding:20px;text-align:center;color:var(--red);">Нет доступа или ошибка: ${e.message}</div>`;
    }
}

document.getElementById('log-filter-severity').addEventListener('change', renderLogsTab);
document.getElementById('btn-refresh-logs').addEventListener('click', renderLogsTab);

// ─── Close modals on backdrop click ──────────────────────────────────────────

document.querySelectorAll('.modal-backdrop').forEach(m => {
    m.addEventListener('click', e => {
        if (e.target === m) m.classList.add('hidden');
    });
});

// ─── Start ────────────────────────────────────────────────────────────────────
init();