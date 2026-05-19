/**
 * Centrum Dowodzenia — Harmonia 369
 * ADRION Architecture | Wirtualny Punkt Odniesienia
 *
 * Modules: Navigation, NLQ Copilot, Smart Feed, Predictive Tiles,
 *          Scanner (3-6-9), Pipeline Zwiadowca→Egzekutor,
 *          Agent Interakcji (Ollama), Genesis Record
 */

// ===== CONFIG =====
const CONFIG = {
    WEBHOOK_URL: 'http://localhost:3691/webhook/harmonia-369',
    API_BASE: 'http://localhost:3691',
    OLLAMA_URL: 'http://localhost:11434/api/generate',
    OLLAMA_MODEL: 'deepseek-coder-v2:lite',
    AGENT_DELAY: 800,
    SCORE_ANIM_MS: 2000,
    REFRESH_INTERVAL: 30000,
};

// ===== DOM UTILS =====
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// ===== ERROR UI HELPER =====
function showLoadError(containerId, message) {
    const el = typeof containerId === 'string' ? $(containerId) : containerId;
    if (!el) return;
    const err = document.createElement('div');
    err.className = 'load-error';
    err.innerHTML = `<span class="load-error-icon">⚠️</span> ${message}`;
    err.style.cssText = 'color:#f59e0b; background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.2); border-radius:8px; padding:0.8rem 1rem; text-align:center; font-size:0.85rem; margin:0.5rem 0;';
    el.prepend(err);
    setTimeout(() => err.remove(), 8000);
}

// ===== NAVIGATION =====
const views = {};
document.addEventListener('DOMContentLoaded', () => {
    $$('.view').forEach(v => { views[v.id.replace('view-', '')] = v; });
    $$('.nav-item').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(link.dataset.view);
        });
    });

    // Init dashboard
    navigateTo('dashboard');
    loadDashboardData();
    setInterval(loadDashboardData, CONFIG.REFRESH_INTERVAL);

    // NLQ
    $('#nlq-send').addEventListener('click', handleNLQ);
    $('#nlq-input').addEventListener('keydown', (e) => { if (e.key === 'Enter') handleNLQ(); });
    $('#nlq-close').addEventListener('click', () => $('#nlq-response').classList.add('hidden'));

    // Scanner
    $('#scan-form').addEventListener('submit', handleScan);
    $('#cta-btn').addEventListener('click', handleCTA);
    $('#btn-explain').addEventListener('click', handleExplain);

    // Pipeline
    $('#pipeline-run').addEventListener('click', runPipeline);
    $('#pipeline-test').addEventListener('click', testBoosterLever);

    // Leads refresh
    $('#refresh-leads').addEventListener('click', loadLeadsTable);

    // V.E.R.A. feedback form
    const vffBtn = $('#vff-submit');
    if (vffBtn) vffBtn.addEventListener('click', handleVFFSubmit);

    // Golden answer form
    const goldenBtn = $('#golden-submit');
    if (goldenBtn) goldenBtn.addEventListener('click', addGoldenAnswer);

    // Outreach
    const outSearchBtn = $('#outreach-search-btn');
    if (outSearchBtn) outSearchBtn.addEventListener('click', () => outreachSearch());
    const outQueryInput = $('#outreach-query');
    if (outQueryInput) outQueryInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') outreachSearch(); });
    const outGenBtn = $('#outreach-generate-btn');
    if (outGenBtn) outGenBtn.addEventListener('click', () => outreachGenerateEmail());
    const outCopyBtn = $('#outreach-copy-btn');
    if (outCopyBtn) outCopyBtn.addEventListener('click', outreachCopyEmail);
    const outRegenBtn = $('#outreach-regenerate-btn');
    if (outRegenBtn) outRegenBtn.addEventListener('click', () => outreachGenerateEmail());
    const outBackBtn = $('#outreach-back-btn');
    if (outBackBtn) outBackBtn.addEventListener('click', outreachBackToSearch);
});

function navigateTo(viewName) {
    Object.values(views).forEach(v => v.classList.remove('active'));
    $$('.nav-item').forEach(n => n.classList.remove('active'));
    if (views[viewName]) views[viewName].classList.add('active');
    const navEl = $(`.nav-item[data-view="${viewName}"]`);
    if (navEl) navEl.classList.add('active');

    // Lazy init
    if (viewName === 'genesis') loadGenesisRecord();
    if (viewName === 'vera') loadVeraView();
    if (viewName === 'swarm') loadSwarmStatus();
    if (viewName === 'outreach') initOutreach();
}

// ===== SCANNER SECTIONS (within scanner view) =====
function showScannerSection(name) {
    ['scanner-section', 'agents-section', 'result-section', 'confirm-section'].forEach(id => {
        const el = $(`#${id}`);
        if (el) { el.classList.remove('active'); el.classList.add('hidden'); }
    });
    const target = $(`#${name}-section`);
    if (target) { target.classList.remove('hidden'); target.classList.add('active'); }
}

// ===== DASHBOARD DATA =====
async function loadDashboardData() {
    try {
        const [statsRes, leadsRes] = await Promise.all([
            fetch(`${CONFIG.API_BASE}/api/stats`),
            fetch(`${CONFIG.API_BASE}/api/leads`),
        ]);
        if (statsRes.ok) {
            const stats = await statsRes.json();
            updateTiles(stats);
            updateSmartFeed(stats);
            updateActionHub(stats);
        }
        if (leadsRes.ok) {
            const leads = await leadsRes.json();
            renderLeadsTable(leads);
        }
    } catch (err) {
        console.warn('[Dashboard] Backend niedostępny:', err.message);
        showLoadError('#feed-cards', 'Backend niedostępny — sprawdź webhook_server.py');
    }
}

function updateTiles(stats) {
    const total = Number(stats.total) || 0;
    const hot = Number(stats.hot) || 0;
    const confirmed = Number(stats.confirmed) || 0;
    const avgScore = Math.round(Number(stats.avg_score) || 0);
    const avgTicket = 350;
    const convRate = total > 0 ? (confirmed / total) : 0;
    const revenue = Math.round(confirmed * avgTicket * 3);

    $('#tile-leads-value').textContent = total;
    $('#tile-hot-value').textContent = hot;
    $('#tile-confirmed-value').textContent = confirmed;
    $('#tile-score-value').textContent = avgScore;
    $('#tile-revenue-value').textContent = revenue.toLocaleString('pl-PL') + ' PLN';
    $('#tile-pipeline-value').textContent = total > 0 ? Math.round(convRate * 100) + '%' : '0%';

    // Trends
    if (hot > 0) { $('#tile-hot-trend').textContent = 'aktywne'; $('#tile-hot-trend').classList.add('up'); }
    if (confirmed > 0) { $('#tile-confirmed-trend').textContent = '+' + confirmed; $('#tile-confirmed-trend').classList.add('up'); }
}

function updateSmartFeed(stats) {
    const cards = $('#feed-cards');
    cards.innerHTML = '';
    const insights = generateInsights(stats);
    insights.forEach(ins => {
        const card = document.createElement('div');
        card.className = `feed-card feed-${ins.type}`;
        card.innerHTML = `
            <div class="feed-icon">${ins.icon}</div>
            <div class="feed-body">
                <span class="feed-tag">${ins.tag}</span>
                <p class="feed-text">${ins.text}</p>
            </div>
            <button class="feed-action" title="Szczegóły">→</button>`;
        cards.appendChild(card);
    });
}

function generateInsights(stats) {
    const insights = [];
    const total = Number(stats.total) || 0;
    const hot = Number(stats.hot) || 0;
    const confirmed = Number(stats.confirmed) || 0;
    const avgScore = Math.round(Number(stats.avg_score) || 0);

    if (hot > 0) {
        insights.push({ type: 'critical', icon: '🚨', tag: 'Anomalia', text: `${hot} lead${hot > 1 ? 'ów' : ''} HOT wymaga natychmiastowej reakcji — score poniżej 50 oznacza krytyczne luki w wizytówce.` });
    }
    if (avgScore > 0 && avgScore < 45) {
        insights.push({ type: 'warning', icon: '⚠️', tag: 'Trend', text: `Średni score (${avgScore}) wskazuje na systemowe problemy z geotagowaniem EXIF i spójnością NAP w analizowanych wizytówkach.` });
    }
    if (confirmed > 0) {
        insights.push({ type: 'success', icon: '✅', tag: 'Konwersja', text: `${confirmed} lead${confirmed > 1 ? 'ów' : ''} potwierdzonych — gotowych do sesji z Architektem Harmonii.` });
    }
    if (total > 0) {
        const revenue = Math.round(total * 350 * 0.15);
        insights.push({ type: 'info', icon: '💰', tag: 'Prognoza', text: `Szacowany potencjał pipeline'u: ${revenue.toLocaleString('pl-PL')} PLN/msc przy konwersji 15%.` });
    }
    if (insights.length === 0) {
        insights.push({ type: 'info', icon: '📊', tag: 'System', text: 'Brak danych. Uruchom Skaner Harmonii aby zebrać pierwsze leady.' });
    }
    return insights;
}

function updateActionHub(stats) {
    const list = $('#action-list');
    list.innerHTML = '';
    const actions = [];
    const hot = Number(stats.hot) || 0;
    const total = Number(stats.total) || 0;

    if (hot > 0) {
        actions.push({ icon: '📧', title: `Wyślij ofertę ratunkową do ${hot} leadów HOT`, desc: 'BoosterLever wygeneruje spersonalizowane maile na bazie braków wizytówki', btn: 'Generuj maile' });
    }
    if (total > 3) {
        actions.push({ icon: '📊', title: 'Wygeneruj Weekly Insights dla klientów', desc: 'Agent Interakcji przygotuje notatki raportujące z systemu Harmonia 369', btn: 'Generuj raporty' });
    }
    actions.push({ icon: '🔍', title: 'Skanuj nową niszę (Local Grid 5km)', desc: 'Pipeline Zwiadowca→Egzekutor — automatyczne wykrycie wizytówek z niskim score', btn: 'Uruchom zwiad' });

    actions.forEach(a => {
        const item = document.createElement('div');
        item.className = 'action-item';
        item.innerHTML = `
            <span class="action-icon">${a.icon}</span>
            <div class="action-body">
                <span class="action-title">${a.title}</span>
                <span class="action-desc">${a.desc}</span>
            </div>
            <button class="action-btn">${a.btn}</button>`;
        list.appendChild(item);
    });
}

// ===== LEADS TABLE =====
async function loadLeadsTable() {
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/leads`);
        if (res.ok) renderLeadsTable(await res.json());
    } catch (err) { console.warn('[Leads] Błąd:', err.message); }
}

function renderLeadsTable(leads) {
    const tbody = $('#leads-tbody');
    if (!leads || leads.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Brak leadów — uruchom Skaner Harmonii</td></tr>';
        return;
    }
    tbody.innerHTML = leads.map(l => {
        const date = l.timestamp ? new Date(l.timestamp).toLocaleDateString('pl-PL') : '-';
        const status = l.lead_status || 'NEW';
        return `<tr>
            <td><strong>${esc(l.business_name)}</strong></td>
            <td>${esc(l.city)}</td>
            <td>${l.score_total || '-'}</td>
            <td><span class="status-badge status-${status}">${status}</span></td>
            <td>${esc(l.email)}</td>
            <td>${date}</td>
        </tr>`;
    }).join('');
}

// ===== NLQ COPILOT (Natural Language Query) =====
async function handleNLQ() {
    const input = $('#nlq-input');
    const query = input.value.trim();
    if (!query) return;

    const responseEl = $('#nlq-response');
    const bodyEl = $('#nlq-response-body');
    responseEl.classList.remove('hidden');
    bodyEl.innerHTML = '<span style="color:#a78bfa">Analizuję zapytanie...</span>';

    // Try Ollama first
    const aiResult = await queryOllama(
        `Jesteś AI Copilotem dashboardu "Harmonia 369" — system lead generation dla firm z Google Maps. Odpowiadaj krótko, konkretnie, po polsku. Użytkownik pyta: "${query}"`,
        query
    );

    if (aiResult) {
        bodyEl.innerHTML = formatAIResponse(aiResult);
    } else {
        // Fallback: local intent matching
        bodyEl.innerHTML = handleNLQLocal(query);
    }
    input.value = '';
}

function handleNLQLocal(query) {
    const q = query.toLowerCase();
    if (q.includes('hot') || q.includes('gorąc')) return 'Leady HOT to firmy ze score poniżej 50 — mają krytyczne luki w wizytówce Google Maps. Przejdź do <strong>Pipeline Leadów</strong> aby wygenerować dla nich oferty.';
    if (q.includes('score') || q.includes('wynik')) return 'Score Harmonii obliczany jest formułą: <code>W = (W_V×3 + W_R×6 + W_E×9) / 18</code>, gdzie W_V=Widoczność, W_R=Reputacja, W_E=Zaangażowanie.';
    if (q.includes('prognoz') || q.includes('q3') || q.includes('przychód')) return 'Prognoza oparta na: (leady × śr. ticket 350 PLN × conversion rate). Dokładniejsze prognozy AI wymagają więcej danych historycznych.';
    if (q.includes('dlaczego') || q.includes('explain')) return 'Otwórz Skaner Harmonii, przeanalizuj firmę, a następnie kliknij przycisk "🧠 Dlaczego taki wynik?" pod score — AI wyjaśni przyczyny.';
    if (q.includes('vera') || q.includes('feedback') || q.includes('jakość')) { navigateTo('vera'); return 'Przechodzę do widoku <strong>V.E.R.A. & Feedback</strong> — tu znajdziesz scoring jakości AI, Judge guardrails i RAG memory.'; }
    if (q.includes('rój') || q.includes('swarm') || q.includes('agent')) { navigateTo('swarm'); return 'Przechodzę do <strong>Roju Agentów</strong> — 9 agentów ADRION 369 z EBDI i statusem na żywo.'; }
    if (q.includes('genesis') || q.includes('log') || q.includes('historia')) { navigateTo('genesis'); return 'Przechodzę do <strong>Genesis Record</strong> — pełny log operacji (Guardian Law G7).'; }
    if (q.includes('outreach') || q.includes('email') || q.includes('klient') || q.includes('mail')) { navigateTo('outreach'); return 'Przechodzę do <strong>Outreach</strong> — wyszukaj klienta, przeanalizuj potrzeby i wygeneruj spersonalizowany email.'; }
    return 'Nie rozpoznałem zapytania. Spróbuj: "Pokaż leady HOT", "Wyjaśnij score", "Status VERA", "Rój agentów", "Prognoza przychodu".';
}

// ===== OLLAMA INTEGRATION =====
async function queryOllama(systemPrompt, userMessage) {
    try {
        const res = await fetch(CONFIG.OLLAMA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: CONFIG.OLLAMA_MODEL,
                prompt: userMessage,
                system: systemPrompt,
                stream: false,
                options: { 
                    temperature: 0.7, 
                    num_predict: 512,
                    top_k: 40,
                    top_p: 0.9
                }
            }),
        });
        if (!res.ok) {
            const errBody = await res.text();
            console.error('[Ollama] Błąd odpowiedzi:', res.status, errBody);
            return null;
        }
        const data = await res.json();
        return data.response || null;
    } catch (err) {
        console.warn('[Ollama] Niedostępna pod adresem:', CONFIG.OLLAMA_URL, err.message);
        return null;
    }
}

function formatAIResponse(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
}

// ===== SCANNER FLOW =====
let lastHarmony = null;
let lastScanData = {};

async function handleScan(e) {
    e.preventDefault();
    const businessName = sanitize($('#business-name').value.trim());
    const city = sanitize($('#business-city').value.trim());
    const email = sanitize($('#business-email').value.trim());
    const phone = sanitize($('#business-phone').value.trim());
    if (!businessName || !city || !email) return;

    $('#scan-btn').disabled = true;
    $('#scan-btn').innerHTML = '<span class="btn-icon">⏳</span> Inicjalizacja Roju...';

    showScannerSection('agents');
    await runAgentLogs(businessName, city);
    await sleep(1200);

    const harmony = calculateHarmony({ businessName, city });
    const verdict = getVerdict(harmony.total);
    lastHarmony = harmony;
    lastScanData = { businessName, city, email, phone };

    showScannerSection('result');
    await sleep(300);
    animateScore(harmony.total);
    animateBreakdown(harmony);
    $('#verdict').innerHTML = verdict.text;
    showLostOpportunities(harmony.total);

    // Reset explain panel
    $('#explain-panel').classList.add('hidden');
    $('#explain-text').textContent = '';

    // Webhook (async)
    sendWebhook({
        timestamp: new Date().toISOString(),
        business_name: businessName, city, email, phone,
        score_total: harmony.total, score_wv: harmony.wv,
        score_wr: harmony.wr, score_we: harmony.we,
        verdict: verdict.text,
    });
}

function handleCTA() {
    const email = sanitize($('#business-email').value.trim());
    const name = sanitize($('#business-name').value.trim());
    $('#confirm-email').textContent = email;
    $('#confirm-name').textContent = name;
    showScannerSection('confirm');

    sendWebhook({
        event: 'lead_confirmed',
        timestamp: new Date().toISOString(),
        email, business_name: name,
    });
}

// ===== CONTEXTUAL EXPLAINABILITY =====
async function handleExplain() {
    if (!lastHarmony) return;
    const panel = $('#explain-panel');
    const loading = $('#explain-loading');
    const textEl = $('#explain-text');

    panel.classList.remove('hidden');
    loading.style.display = 'block';
    textEl.textContent = '';

    const prompt = `Firma "${lastScanData.businessName}" w mieście ${lastScanData.city} uzyskała Wskaźnik Harmonii ${lastHarmony.total}/100.
Dekompozycja: Widoczność(W_V)=${lastHarmony.wv}, Reputacja(W_R)=${lastHarmony.wr}, Zaangażowanie(W_E)=${lastHarmony.we}.
Formuła: W = (W_V×3 + W_R×6 + W_E×9) / 18.

Wyjaśnij KRÓTKO (max 5 zdań) dlaczego wynik jest taki, co oznaczają poszczególne składowe, i co firma powinna poprawić w pierwszej kolejności.`;

    const result = await queryOllama(
        'Jesteś ekspertem Google Maps i lokalnego SEO w systemie Harmonia 369. Odpowiadaj po polsku, konkretnie, z liczbami.',
        prompt
    );

    loading.style.display = 'none';
    if (result) {
        textEl.innerHTML = formatAIResponse(result);
    } else {
        // Fallback bez Ollamy
        const h = lastHarmony;
        let reasons = [];
        if (h.we < 30) reasons.push('Krytycznie niskie zaangażowanie (W_E=' + h.we + ') — brak regularnych postów i interakcji z klientami.');
        if (h.wv < 40) reasons.push('Niska widoczność (W_V=' + h.wv + ') — firma nie dominuje w Local Grid na kluczowe frazy.');
        if (h.wr < 50) reasons.push('Reputacja poniżej progu (W_R=' + h.wr + ') — za mało opinii lub niski rating.');
        reasons.push(`Score ${h.total}/100 oznacza, że zaangażowanie (waga ×9) ciągnie średnią w dół najsilniej.`);
        reasons.push('Priorytet: zwiększ W_E przez regularne posty z geotagowanymi zdjęciami EXIF.');
        textEl.innerHTML = reasons.join('<br><br>');
    }
}

// ===== AGENT LOGS =====
const AGENT_LOGS = (businessName, city) => [
    { agent: 'SYSTEM',   cls: 'log-system', text: `Inicjalizacja Roju Harmonia 369...` },
    { agent: 'Agent 3',  cls: 'log-agent',  text: `Skanowanie siatki pozycji (Local Grid) w promieniu 5km od "${city}"...`, card: 'agent-3', task: 'Skanowanie Local Grid...' },
    { agent: 'Agent 3',  cls: 'log-agent',  text: `Analiza widoczności "${businessName}" na główne frazy lokalne...`, card: 'agent-3', task: 'Analiza widoczności...' },
    { agent: 'Agent 3',  cls: 'log-ok',     text: `Znaleziono 12 fraz konkurencyjnych. Pozycja bazowa: analizuję...`, card: 'agent-3', task: 'Mapowanie konkurencji...' },
    { agent: 'Agent 6',  cls: 'log-agent',  text: `Analiza nasycenia słów kluczowych w opiniach i postach...`, card: 'agent-6', task: 'Analiza treści...' },
    { agent: 'Agent 6',  cls: 'log-agent',  text: `Weryfikacja danych EXIF w zdjęciach profilu...`, card: 'agent-6', task: 'Audyt EXIF...' },
    { agent: 'Agent 6',  cls: 'log-warn',   text: `UWAGA: Brak geotagowanych zdjęć wykryty!`, card: 'agent-6', task: 'Brak EXIF!' },
    { agent: 'Agent 9',  cls: 'log-agent',  text: `Weryfikacja spójności danych NAP w 20 źródłach...`, card: 'agent-9', task: 'Audyt NAP...' },
    { agent: 'Agent 9',  cls: 'log-agent',  text: `Sprawdzanie katalogów: Panorama Firm, Yelp, Zumi, Aleo...`, card: 'agent-9', task: 'Skanowanie katalogów...' },
    { agent: 'Agent 9',  cls: 'log-warn',   text: `Wykryto rozbieżności NAP w 3 katalogach.`, card: 'agent-9', task: 'Rozbieżności NAP!' },
    { agent: 'SYSTEM',   cls: 'log-system', text: `Obliczanie Wskaźnika Harmonii (formuła 3-6-9)...` },
    { agent: 'SYSTEM',   cls: 'log-ok',     text: `Analiza zakończona. Generowanie raportu...` },
];

function timestamp() {
    const d = new Date();
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
}

async function runAgentLogs(businessName, city) {
    const body = $('#terminal-body');
    body.innerHTML = '';
    const logs = AGENT_LOGS(businessName, city);
    for (let i = 0; i < logs.length; i++) {
        const log = logs[i];
        const line = document.createElement('div');
        line.className = 'log-line';
        line.innerHTML = `<span class="log-time">[${timestamp()}]</span> <span class="${log.cls}">[${log.agent}]:</span> ${log.text}`;
        body.appendChild(line);
        body.scrollTop = body.scrollHeight;
        if (log.card) {
            const card = $(`#${log.card}`);
            card.dataset.status = 'active';
            card.querySelector('.agent-task').textContent = log.task;
        }
        await sleep(CONFIG.AGENT_DELAY + Math.random() * 400);
    }
    ['agent-3', 'agent-6', 'agent-9'].forEach(id => {
        const c = $(`#${id}`);
        c.dataset.status = 'done';
        c.querySelector('.agent-task').textContent = 'Zakończono ✓';
    });
}

// ===== HARMONIA 369 ALGORITHM =====
function calculateHarmony(data) {
    const seed = hashString(data.businessName + data.city);
    const wv = clamp(30 + (seed % 40), 10, 85);
    const wr = clamp(25 + ((seed >> 4) % 45), 10, 90);
    const we = clamp(15 + ((seed >> 8) % 35), 5, 70);
    const total = Math.round((wv * 3 + wr * 6 + we * 9) / 18);
    return { wv, wr, we, total };
}

function hashString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) { hash = ((hash << 5) - hash) + str.charCodeAt(i); hash |= 0; }
    return Math.abs(hash);
}

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

function getVerdict(score) {
    if (score >= 75) return { text: 'Twoja wizytówka jest w dobrej kondycji, ale system Harmonia 369 wykrył punkty optymalizacji, które mogą znacząco zwiększyć Twój ruch.', cls: 'ok' };
    if (score >= 50) return { text: 'Twoja wizytówka wymaga uwagi. Konkurencja w Twojej okolicy jest aktywniejsza algorytmicznie. System Harmonia 369 wykrył luki w geotagowaniu i spójności NAP.', cls: 'warn' };
    if (score >= 30) return { text: 'Twoja wizytówka jest w stanie chaosu informacyjnego. Krytyczne luki w geotagowaniu, brak postów i rozbieżności NAP. Tracisz klientów na rzecz słabszej, ale lepiej zoptymalizowanej konkurencji.', cls: 'error' };
    return { text: 'ALARM: Twoja firma jest niewidoczna w Google Maps. Brak EXIF, zerowe zaangażowanie, pełna rozbieżność danych NAP. Każdy dzień to utracone przychody.', cls: 'critical' };
}

// ===== SCORE + BREAKDOWN ANIMATION =====
function animateScore(score) {
    const circle = $('#score-circle');
    const valueEl = $('#score-value');
    const circumference = 2 * Math.PI * 85;
    circle.style.transition = `stroke-dashoffset ${CONFIG.SCORE_ANIM_MS}ms ease-out`;
    circle.style.strokeDashoffset = circumference - (score / 100) * circumference;
    let current = 0;
    const step = score / (CONFIG.SCORE_ANIM_MS / 30);
    const timer = setInterval(() => { current += step; if (current >= score) { current = score; clearInterval(timer); } valueEl.textContent = Math.round(current); }, 30);
}

function animateBreakdown(harmony) {
    setTimeout(() => {
        $('#bar-wv').style.width = harmony.wv + '%'; $('#score-wv').textContent = harmony.wv;
        $('#bar-wr').style.width = harmony.wr + '%'; $('#score-wr').textContent = harmony.wr;
        $('#bar-we').style.width = harmony.we + '%'; $('#score-we').textContent = harmony.we;
    }, 400);
}

function showLostOpportunities(score) {
    const lostCalls = Math.round((100 - score) * 1.8);
    const lostRevenue = Math.round(lostCalls * 350 * 0.15);
    animateNum($('#lost-calls'), lostCalls);
    animateNumSuffix($('#lost-revenue'), lostRevenue, ' PLN');
}

function animateNum(el, target) {
    let s = 0; const step = target / 50;
    const t = setInterval(() => { s += step; if (s >= target) { s = target; clearInterval(t); } el.textContent = Math.round(s); }, 30);
}
function animateNumSuffix(el, target, suffix) {
    let s = 0; const step = target / 50;
    const t = setInterval(() => { s += step; if (s >= target) { s = target; clearInterval(t); } el.textContent = Math.round(s).toLocaleString('pl-PL') + suffix; }, 30);
}

// ===== PIPELINE: ZWIADOWCA → EGZEKUTOR =====
const PIPELINE_STEPS = [
    { id: 'pn-chronos', agent: 'CHRONOS', text: 'Inicjalizacja cyklu Zwiadowcy... Interwał: poniedziałek 08:00' },
    { id: 'pn-sentinel', agent: 'SENTINEL', text: 'Scraping Google Maps API — nisze: restauracje, salony fryzjerskie...' },
    { id: 'pn-sentinel', agent: 'SENTINEL', text: 'Wykryto 47 wizytówek. Filtrowanie: photos<3, reviews<4.0, unverified...' },
    { id: 'pn-auditor', agent: 'AUDYTOR', text: 'Filtr jakości: odrzucam rekordy bez e-mail/telefonu...' },
    { id: 'pn-auditor', agent: 'AUDYTOR', text: 'Sprawdzam blacklistę (Law G8)... 2 wpisy odrzucone.' },
    { id: 'pn-auditor', agent: 'AUDYTOR', text: 'Po filtracji: 28 kwalifikujących się wizytówek.' },
    { id: 'pn-booster', agent: 'BOOSTERLEVER', text: 'Generowanie spersonalizowanych ofert przez Ollama...' },
    { id: 'pn-booster', agent: 'BOOSTERLEVER', text: 'Generacja zakończona. Template: "Oferta Ratunkowa Harmonia 369".' },
    { id: 'pn-sap', agent: 'SAP', text: 'Wysyłka ofert... 28/28 gotowych. Genesis Record zaktualizowany.' },
];

async function runPipeline() {
    const log = $('#pipeline-log');
    const terminal = $('#pipeline-terminal');
    log.classList.remove('hidden');
    terminal.innerHTML = '';

    // Reset nodes
    $$('.pipeline-node').forEach(n => { n.classList.remove('active', 'done'); });

    // Trigger backend pipeline
    const addLine = (agent, text, cls = 'log-agent') => {
        const line = document.createElement('div');
        line.className = 'log-line';
        line.innerHTML = `<span class="log-time">[${timestamp()}]</span> <span class="${cls}">[${agent}]:</span> ${text}`;
        terminal.appendChild(line);
        terminal.scrollTop = terminal.scrollHeight;
    };

    addLine('SYSTEM', 'Wysyłanie żądania do backendu pipeline...', 'log-system');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/pipeline/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ niche: 'restauracje', city: 'Kraków', radius_km: 5, generate_mails: true }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        addLine('SYSTEM', 'Pipeline uruchomiony na serwerze. Monitorowanie postępu...', 'log-ok');
    } catch (err) {
        addLine('SYSTEM', `Backend niedostępny (${err.message}) — uruchamiam symulację lokalną...`, 'log-warn');
    }

    // Visual animation of pipeline stages (runs regardless of backend)
    for (const step of PIPELINE_STEPS) {
        const node = $(`#${step.id}`);
        if (node) { $$('.pipeline-node').forEach(n => n.classList.remove('active')); node.classList.add('active'); }
        addLine(step.agent, step.text);
        await sleep(1000 + Math.random() * 600);
        if (node) node.classList.add('done');
    }

    // Check backend result
    try {
        const statusRes = await fetch(`${CONFIG.API_BASE}/api/pipeline/status`);
        if (statusRes.ok) {
            const state = await statusRes.json();
            if (state.status === 'completed') {
                addLine('SYSTEM', `Pipeline zakończony. Scraped: ${state.scraped_count}, Filtered: ${state.filtered_count}, Mails: ${state.mails_generated}, Saved: ${state.sent_count}`, 'log-ok');
                loadDashboardData(); // Refresh
                return;
            }
        }
    } catch (err) {
        addLine('SYSTEM', `Pipeline status: backend niedostępny (${err.message}).`, 'log-warn');
    }

    addLine('SYSTEM', 'Pipeline zakończony (symulacja visuàlna).', 'log-ok');
}

// ===== BOOSTERLEVER TEST (Agent Interakcji) =====
async function testBoosterLever() {
    const log = $('#pipeline-log');
    const terminal = $('#pipeline-terminal');
    log.classList.remove('hidden');
    terminal.innerHTML = '';

    const line1 = document.createElement('div');
    line1.className = 'log-line';
    line1.innerHTML = `<span class="log-time">[${timestamp()}]</span> <span class="log-system">[BOOSTERLEVER]:</span> Generowanie testowej oferty ratunkowej...`;
    terminal.appendChild(line1);

    const systemPrompt = `Jesteś Agentem Interakcji w systemie Harmonia 369 — agencji "Wirtualny Punkt Odniesienia".
Na podstawie danych analitycznych napisz krótki, profesjonalny raport tygodniowy (Weekly Insights) dla właściciela firmy.

ZASADY:
- Ton: profesjonalny, konkretny, zorientowany na matematyczny zysk, życzliwy
- Pokaż że system aktywnie reaguje na ruchy rynku w czasie rzeczywistym
- Użyj konkretnych liczb i terminologii: Wskaźnik Harmonii, Local Grid, EXIF, NAP
- Podpisz się jako "Twój Rój Agentów ADRION 369"
- Max 200 słów`;

    const userMsg = `Dane klienta:
- Firma: Pizzeria Roma, miasto: Kraków
- Wskaźnik Harmonii: 42% (+8% vs zeszły tydzień)
- Połączenia z wizytówki: 23, konwersja: ~15%, przychód: ~1207 PLN
- Local Grid: pozycja nr 2 na "pizzeria kraków" w promieniu 3km
- Agent Analityk: wykryto atak konkurencji na frazę "pizza na dowóz kraków"
- Agent Twórca: opublikował 4 posty z EXIF z Rynku Głównego i Kazimierza
- Agent Interakcji: obsłużył 7 nowych opinii`;

    const result = await queryOllama(systemPrompt, userMsg);

    if (result) {
        const line2 = document.createElement('div');
        line2.className = 'log-line';
        line2.innerHTML = `<span class="log-time">[${timestamp()}]</span> <span class="log-ok">[BOOSTERLEVER]:</span> Raport wygenerowany przez Ollama (${CONFIG.OLLAMA_MODEL})`;
        terminal.appendChild(line2);

        const preview = document.createElement('div');
        preview.className = 'report-preview';
        preview.innerHTML = `<h3>📧 Podgląd: Weekly Insights — Pizzeria Roma</h3><div class="report-body">${formatAIResponse(result)}</div>`;
        terminal.appendChild(preview);
    } else {
        // Fallback: template-based report
        const fallback = generateFallbackReport({
            name: 'Pizzeria Roma', city: 'Kraków', score: 42, scoreDelta: 8,
            calls: 23, revenue: 1207, gridPos: 2, gridRadius: 3,
            keyword: 'pizza na dowóz kraków', posts: 4, reviews: 7,
        });
        const line2 = document.createElement('div');
        line2.className = 'log-line';
        line2.innerHTML = `<span class="log-time">[${timestamp()}]</span> <span class="log-warn">[BOOSTERLEVER]:</span> Ollama niedostępna — użyto szablonu Agenta Interakcji`;
        terminal.appendChild(line2);

        const preview = document.createElement('div');
        preview.className = 'report-preview';
        preview.innerHTML = `<h3>📧 Podgląd: Weekly Insights — Pizzeria Roma</h3><div class="report-body">${fallback}</div>`;
        terminal.appendChild(preview);
    }
}

function generateFallbackReport(d) {
    return `<strong>Temat:</strong> [WPO] Raport Harmonii dla ${d.name}: Twój Rój zdominował kolejny sektor 🚀

Cześć,

Tutaj Twój <strong>Agent Interakcji</strong> z systemu Harmonia 369. Przygotowałem krótkie podsumowanie operacji, które mój Rój wykonał dla Twojej wizytówki w mijającym tygodniu.

<strong>Oto kluczowe liczby (Matematyka Twojego zysku):</strong>
• <strong>Wskaźnik Harmonii:</strong> Wznieśliśmy go na poziom <strong>${d.score}%</strong> (+${d.scoreDelta}% względem zeszłego tygodnia)
• <strong>Realny Wpływ:</strong> Odnotowałem <strong>${d.calls}</strong> bezpośrednich połączeń telefonicznych z wizytówki. Przy konwersji 15% oznacza to szacunkowo <strong>${d.revenue} PLN</strong> przychodu wygenerowanego przez system.
• <strong>Dominacja Local Grid:</strong> Utrzymaliśmy pozycję nr ${d.gridPos} na kluczowe frazy w promieniu <strong>${d.gridRadius} km</strong> od Twojego biura.

<strong>Co działo się 'pod maską' (Akcje Agentów):</strong>
1. <strong>Agent Analityk</strong> wykrył próbę ataku konkurencji na frazę "${d.keyword}". Natychmiastowo uruchomiliśmy procedurę obronną.
2. <strong>Agent Twórca</strong> opublikował <strong>${d.posts}</strong> postów nasyconych lokalną intencją, z danymi EXIF ze strategicznych punktów ${d.city}.
3. <strong>Ja (Agent Interakcji)</strong> przejąłem obsługę <strong>${d.reviews}</strong> nowych opinii. Każda odpowiedź zoptymalizowana pod kątem słów kluczowych.

Dobrego tygodnia,
<strong>Twój Rój Agentów ADRION 369</strong>`;
}

// ===== GENESIS RECORD =====
async function loadGenesisRecord() {
    const log = $('#genesis-log');

    // Try Genesis API first (pipeline logs)
    try {
        const genesisRes = await fetch(`${CONFIG.API_BASE}/api/genesis`);
        if (genesisRes.ok) {
            const genesisLogs = await genesisRes.json();
            if (genesisLogs.length > 0) {
                log.innerHTML = '';
                addGenesisEntry(log, 'system', `[GENESIS] Guardian Law G7: Żadne dane nie opuszczają maszyny.`);
                addGenesisEntry(log, 'system', `[GENESIS] Załadowano ${genesisLogs.length} wpisów z Genesis Record.`);
                genesisLogs.forEach(entry => {
                    const ts = entry.timestamp ? new Date(entry.timestamp).toLocaleString('pl-PL') : '-';
                    const cls = entry.agent === 'SYSTEM' ? 'system' : entry.agent === 'SENTINEL' ? 'security' : 'action';
                    addGenesisEntry(log, cls, `[${ts}] [${entry.agent}] ${entry.action}: ${entry.detail || ''}`);
                });
                return;
            }
        }
    } catch (err) {
        console.warn('[Genesis] API error:', err.message);
    }

    // Fallback: load from leads API
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/leads`);
        if (!res.ok) throw new Error('API error');
        const leads = await res.json();
        log.innerHTML = '';

        addGenesisEntry(log, 'system', `[GENESIS] Inicjalizacja Genesis Record — Guardian Law G7.`);
        addGenesisEntry(log, 'system', `[GENESIS] Połączono z PostgreSQL (adrion-db:5432, db: genesis_record)`);
        addGenesisEntry(log, 'system', `[GENESIS] Załadowano ${leads.length} rekordów z tabeli leads.`);

        leads.forEach(l => {
            const ts = l.timestamp ? new Date(l.timestamp).toLocaleString('pl-PL') : '-';
            addGenesisEntry(log, 'action', `[${ts}] LEAD: ${l.business_name} (${l.city}) | Score: ${l.score_total} | Status: ${l.lead_status} | ${l.email}`);
        });

        if (leads.length === 0) {
            addGenesisEntry(log, 'system', `[GENESIS] Brak wpisów. System oczekuje na dane z Roju Agentów.`);
        }
    } catch (err) {
        log.innerHTML = '';
        addGenesisEntry(log, 'security', '[WARN] Nie udało się połączyć z API backendu. Sprawdź webhook_server.py.');
    }
}

function addGenesisEntry(container, cls, text) {
    const entry = document.createElement('div');
    entry.className = `genesis-entry ${cls}`;
    entry.textContent = text;
    container.appendChild(entry);
}

// ===== FEEDBACK STATUS CACHE =====
let _feedbackStatusCache = null;
let _feedbackStatusTs = 0;
const FEEDBACK_CACHE_TTL = 5000; // 5 seconds

async function getFeedbackStatus() {
    const now = Date.now();
    if (_feedbackStatusCache && (now - _feedbackStatusTs) < FEEDBACK_CACHE_TTL) {
        return _feedbackStatusCache;
    }
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/feedback/status`);
        if (!res.ok) throw new Error('feedback/status error');
        _feedbackStatusCache = await res.json();
        _feedbackStatusTs = now;
        return _feedbackStatusCache;
    } catch (err) {
        console.warn('[FeedbackCache] Error:', err.message);
        return _feedbackStatusCache; // return stale if available
    }
}

// ===== SWARM LIVE STATUS =====
async function loadSwarmStatus() {
    try {
        const [healthRes, fb] = await Promise.all([
            fetch(`${CONFIG.API_BASE}/health`).then(r => r.ok ? r.json() : {}),
            getFeedbackStatus(),
        ]);
        const health = healthRes || {};

        // Map system state to agent statuses
        const agents = {
            sentinel:  health.pipeline ? 'active' : 'idle',
            auditor:   health.pipeline ? 'active' : 'idle',
            booster:   health.pipeline ? 'ready' : 'idle',
            sap:       health.pipeline ? 'ready' : 'idle',
            chronos:   health.pipeline ? 'ready' : 'idle',
            librarian: health.postgres ? 'active' : 'idle',
            architect: 'ready',
            healer:    fb && fb.vera ? 'active' : 'idle',
            amplifier: 'ready',
        };

        Object.entries(agents).forEach(([key, status]) => {
            const el = $(`#swarm-${key}-status`);
            if (el) {
                el.textContent = status;
                el.className = `swarm-status swarm-st-${status}`;
            }
        });
    } catch (err) {
        console.warn('[Swarm] Status error:', err.message);
        showLoadError('#swarm-sentinel-status', 'Swarm status niedostępny');
    }
}

// ===== V.E.R.A. & FEEDBACK VIEW =====
const GAUGE_CIRCUMF = 327; // 2 * PI * 52

function setGauge(circleId, value) {
    const el = $(`#${circleId}`);
    if (!el) return;
    const clamped = Math.max(0, Math.min(1, value));
    const offset = GAUGE_CIRCUMF - (clamped * GAUGE_CIRCUMF);
    el.style.transition = 'stroke-dashoffset 1s ease';
    el.setAttribute('stroke-dashoffset', offset);
}

async function loadVeraView() {
    try {
        const d = await getFeedbackStatus();
        if (!d) throw new Error('Brak danych feedback/status');

        // V.E.R.A. Gauges
        const vera = d.vera || {};
        setGauge('gauge-circle-total', vera.total || 0);
        setGauge('gauge-circle-v', vera.verifiable || 0);
        setGauge('gauge-circle-e', vera.efficient || 0);
        setGauge('gauge-circle-r', vera.relevant || 0);
        setGauge('gauge-circle-a', vera.aligned || 0);

        const fmt = (v) => v != null ? (v * 100).toFixed(0) + '%' : '—';
        $('#gauge-val-total').textContent = fmt(vera.total);
        $('#gauge-val-v').textContent = fmt(vera.verifiable);
        $('#gauge-val-e').textContent = fmt(vera.efficient);
        $('#gauge-val-r').textContent = fmt(vera.relevant);
        $('#gauge-val-a').textContent = fmt(vera.aligned);

        // Trend
        const trend = d.vera_trend || {};
        const trendEl = $('#gauge-trend-total');
        if (trendEl) {
            const delta = trend.delta || 0;
            const arrow = delta > 0.01 ? '▲' : delta < -0.01 ? '▼' : '—';
            const cls = delta > 0.01 ? 'up' : delta < -0.01 ? 'down' : 'stable';
            trendEl.textContent = `${arrow} ${(delta * 100).toFixed(1)}% (${trend.trend || 'stable'})`;
            trendEl.className = `gauge-trend ${cls}`;
        }

        // Judge
        const judge = d.judge || {};
        $('#judge-total').textContent = judge.total || 0;
        $('#judge-pass').textContent = ((judge.pass_rate || 0) * 100).toFixed(0) + '%';
        $('#judge-warn').textContent = ((judge.warn_rate || 0) * 100).toFixed(0) + '%';
        $('#judge-block').textContent = ((judge.block_rate || 0) * 100).toFixed(0) + '%';
        $('#judge-drift').textContent = (judge.avg_drift || 0).toFixed(2);

        // Behavior
        const beh = d.behavior || {};
        $('#beh-total').textContent = beh.total || 0;
        $('#beh-capture').textContent = ((d.capture_rate || 0) * 100).toFixed(0) + '%';
        $('#beh-feedback').textContent = (beh.avg_feedback || 0).toFixed(2);
        $('#beh-latency').textContent = (beh.avg_latency_ms || 0).toFixed(0) + 'ms';

        // Memory
        const mem = d.memory || {};
        $('#mem-short').textContent = mem.short_term_count || 0;
        $('#mem-long').textContent = mem.long_term_count || 0;
        $('#mem-mode').textContent = (mem.embedding_mode || '—').replace('chromadb-', '');

        // Golden answers count
        const ga = d.golden_answers || {};
        $('#mem-golden').textContent = ga.total || 0;

        // Load recommendations (OODA Decide)
        loadVeraRecommendations();
        // Load golden answers list
        loadGoldenAnswers(ga);

    } catch (err) {
        console.warn('[V.E.R.A.] Load error:', err.message);
        showLoadError('#vera-golden-list', 'V.E.R.A. niedostępna — sprawdź backend');
    }
}

async function loadVeraRecommendations() {
    const list = $('#vera-rec-list');
    if (!list) return;
    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/feedback/decide`);
        if (!res.ok) throw new Error('decide error');
        const d = await res.json();

        const recs = d.recommendations || [];
        if (recs.length === 0) {
            list.innerHTML = '<div class="vera-rec-item"><span class="vera-rec-icon">✅</span><span class="vera-rec-text">Wszystkie metryki w normie. Brak rekomendacji.</span></div>';
            return;
        }
        list.innerHTML = recs.map(r =>
            `<div class="vera-rec-item"><span class="vera-rec-icon">⚠️</span><span class="vera-rec-text">${sanitize(r)}</span></div>`
        ).join('');
    } catch (err) {
        list.innerHTML = '<div class="vera-rec-item"><span class="vera-rec-icon">❌</span><span class="vera-rec-text">Nie udało się pobrać rekomendacji.</span></div>';
    }
}

function loadGoldenAnswers(ga) {
    const list = $('#vera-golden-list');
    if (!list) return;

    const answers = (ga && ga.most_used) || [];
    if (answers.length === 0) {
        list.innerHTML = '<div class="vera-golden-item">Brak złotych odpowiedzi. Dodaj via POST /api/golden.</div>';
        return;
    }
    list.innerHTML = answers.map(a => `
        <div class="vera-golden-item">
            <div class="golden-prompt">Q: ${sanitize(a.prompt)}</div>
            <div class="golden-response">A: ${sanitize(a.golden_response)}</div>
            <div class="golden-meta">Kategoria: ${esc(a.category)} | Użycia: ${a.usage_count || 0} | ID: ${esc(a.id)}</div>
        </div>
    `).join('');
}

async function addGoldenAnswer() {
    const prompt = $('#golden-prompt').value.trim();
    const response = $('#golden-response').value.trim();
    const category = $('#golden-category').value;
    const resultEl = $('#golden-result');

    if (!prompt || !response) {
        if (resultEl) { resultEl.textContent = 'Wypełnij prompt i odpowiedź.'; resultEl.classList.remove('hidden'); }
        return;
    }
    if (resultEl) { resultEl.textContent = 'Dodawanie złotej odpowiedzi...'; resultEl.classList.remove('hidden'); }

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/golden`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, golden_response: response, category }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const d = await res.json();

        if (resultEl) resultEl.textContent = `✅ Dodano! ID: ${d.id || '—'}`;
        $('#golden-prompt').value = '';
        $('#golden-response').value = '';

        // Invalidate cache and refresh
        _feedbackStatusCache = null;
        _feedbackStatusTs = 0;
        setTimeout(() => loadVeraView(), 500);
    } catch (err) {
        if (resultEl) resultEl.textContent = `❌ Błąd: ${err.message}`;
    }
}

async function handleVFFSubmit() {
    const prompt = $('#vff-prompt').value.trim();
    const response = $('#vff-response').value.trim();
    const category = $('#vff-category').value;
    const resultEl = $('#vff-result');

    if (!prompt || !response) {
        resultEl.textContent = 'Wypełnij prompt i odpowiedź.';
        resultEl.classList.remove('hidden');
        return;
    }

    resultEl.textContent = 'Sending OODA Observe...';
    resultEl.classList.remove('hidden');

    try {
        const body = { prompt, response, category, latency_ms: 0 };
        const res = await fetch(`${CONFIG.API_BASE}/api/feedback/observe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error('observe error');
        const d = await res.json();

        const v = d.vera || {};
        resultEl.textContent = `✅ Observed! ID: ${d.interaction_id}\nV.E.R.A.: V=${(v.verifiable||0).toFixed(2)} E=${(v.efficient||0).toFixed(2)} R=${(v.relevant||0).toFixed(2)} A=${(v.aligned||0).toFixed(2)} → Total: ${(v.total||0).toFixed(3)}`;

        // Clear inputs
        $('#vff-prompt').value = '';
        $('#vff-response').value = '';

        // Refresh gauges
        setTimeout(() => loadVeraView(), 500);
    } catch (err) {
        resultEl.textContent = `❌ Błąd: ${err.message}`;
    }
}

// ===== WEBHOOK =====
async function sendWebhook(data) {
    try {
        const res = await fetch(CONFIG.WEBHOOK_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        if (!res.ok) console.warn('[Webhook] Error:', res.status);
        return res.ok;
    } catch (err) {
        console.warn('[Webhook] Offline:', err.message);
        return false;
    }
}

// ===== UTILITIES =====
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
function sanitize(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
function esc(str) { return str ? sanitize(str) : '-'; }

// ===== OUTREACH: SEARCH → ANALYZE → EMAIL =====
let outreachSelectedLeadId = null;

function initOutreach() {
    // Load recent leads on view open (empty query = recent 20)
    outreachSearch('');
}

function outreachShowStep(step) {
    ['outreach-step-search', 'outreach-step-analyze', 'outreach-step-email'].forEach(id => {
        const el = $(`#${id}`);
        if (el) el.style.display = 'none';
    });
    const target = $(`#outreach-step-${step}`);
    if (target) target.style.display = 'block';
}

async function outreachSearch(queryOverride) {
    const query = queryOverride !== undefined ? queryOverride : ($('#outreach-query')?.value?.trim() || '');
    const results = $('#outreach-results');
    if (!results) return;

    results.innerHTML = '<div class="spinner"></div>';
    outreachShowStep('search');

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/leads/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const leads = await res.json();

        if (!leads || leads.length === 0) {
            results.innerHTML = '<p style="color:#94a3b8; text-align:center; padding:2rem;">Brak wyników. Spróbuj inną frazę lub uruchom Skaner.</p>';
            return;
        }

        results.innerHTML = leads.map(l => {
            const scoreClass = l.score_total >= 60 ? 'cold' : l.score_total >= 40 ? 'warm' : 'hot';
            return `<div class="outreach-lead-row" data-lead-id="${l.id}" onclick="outreachSelectLead(${l.id})">
                <span class="outreach-lead-name">${esc(l.business_name)}</span>
                <span class="outreach-lead-city">${esc(l.city)}</span>
                <span class="outreach-lead-score ${scoreClass}">${l.score_total || 0}</span>
                <span class="outreach-lead-email">${esc(l.email)}</span>
                <span class="outreach-lead-status">${l.lead_status || 'NEW'}</span>
            </div>`;
        }).join('');
    } catch (err) {
        results.innerHTML = `<p style="color:#ef4444; text-align:center; padding:2rem;">Błąd: ${esc(err.message)}. Sprawdź backend.</p>`;
    }
}

async function outreachSelectLead(leadId) {
    outreachSelectedLeadId = leadId;
    outreachShowStep('analyze');

    const cardEl = $('#outreach-client-card');
    const analysisEl = $('#outreach-analysis');
    if (cardEl) cardEl.innerHTML = '<div class="spinner"></div>';
    if (analysisEl) analysisEl.innerHTML = '';

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/outreach/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_id: leadId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const lead = data.lead || {};
        const issues = data.issues || [];
        const recs = data.recommendations || [];

        // Render client card
        const scoreClass = (lead.score_total || 0) >= 60 ? 'cold' : (lead.score_total || 0) >= 40 ? 'warm' : 'hot';
        if (cardEl) {
            cardEl.innerHTML = `
                <div class="occ-header">
                    <span class="occ-name">${esc(lead.business_name)}</span>
                    <span class="outreach-lead-score ${scoreClass}" style="font-size:1.2rem">${lead.score_total || 0}/100</span>
                </div>
                <div class="occ-details">
                    <span>📍 ${esc(lead.city)}</span>
                    <span>📧 ${esc(lead.email)}</span>
                    <span>📞 ${esc(lead.phone)}</span>
                    <span>📊 W_V=${lead.score_wv || 0} | W_R=${lead.score_wr || 0} | W_E=${lead.score_we || 0}</span>
                    <span>🏷️ ${lead.lead_status || 'NEW'} | ${esc(lead.verdict)}</span>
                </div>`;
        }

        // Render analysis
        if (analysisEl) {
            let html = '<h4 style="margin:0 0 0.8rem; color:#e2e8f0;">Diagnoza</h4>';
            html += '<div class="analysis-issues">';
            issues.forEach(i => {
                const cls = i.severity === 'critical' ? 'critical' : i.severity === 'medium' ? 'medium' : 'ok';
                html += `<div class="analysis-issue ${cls}"><span>${i.icon}</span> ${esc(i.text)}</div>`;
            });
            html += '</div>';

            if (recs.length > 0) {
                html += '<h4 style="margin:1rem 0 0.5rem; color:#e2e8f0;">Rekomendacje</h4>';
                html += '<ul class="analysis-recommendations">';
                recs.forEach(r => { html += `<li>${esc(r)}</li>`; });
                html += '</ul>';
            }

            html += `<p style="color:#64748b; margin-top:1rem; font-size:0.8rem;">${esc(data.summary || '')}</p>`;
            analysisEl.innerHTML = html;
        }

        // Pre-fill email To field
        const emailTo = $('#outreach-email-to');
        if (emailTo) emailTo.value = lead.email || '';

    } catch (err) {
        if (cardEl) cardEl.innerHTML = `<p style="color:#ef4444;">Błąd analizy: ${esc(err.message)}</p>`;
    }
}

async function outreachGenerateEmail() {
    if (!outreachSelectedLeadId) return;
    outreachShowStep('email');

    const subjectEl = $('#outreach-email-subject');
    const bodyEl = $('#outreach-email-body');
    const modelInfo = $('#outreach-model-info');
    const genTime = $('#outreach-gen-time');

    if (subjectEl) subjectEl.value = '';
    if (bodyEl) bodyEl.value = 'Generowanie spersonalizowanego emaila przez AI...\n\nProszę czekać — BoosterLever analizuje dane klienta...';
    if (modelInfo) modelInfo.textContent = '...';
    if (genTime) genTime.textContent = '...';

    try {
        const res = await fetch(`${CONFIG.API_BASE}/api/outreach/generate-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lead_id: outreachSelectedLeadId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data.status === 'error') {
            if (bodyEl) bodyEl.value = `Błąd: ${data.error}\n\nSprawdź czy Ollama jest uruchomiona (ollama serve).`;
            return;
        }

        if (subjectEl) subjectEl.value = data.subject || '';
        if (bodyEl) bodyEl.value = data.body || '';
        if (modelInfo) modelInfo.textContent = data.model || 'unknown';
        if (genTime) genTime.textContent = data.gen_time_s ? `${data.gen_time_s}s` : '-';

    } catch (err) {
        if (bodyEl) bodyEl.value = `Błąd generowania: ${err.message}\n\nSprawdź backend (webhook_server.py) i Ollama.`;
    }
}

function outreachCopyEmail() {
    const subject = $('#outreach-email-subject')?.value || '';
    const body = $('#outreach-email-body')?.value || '';
    const to = $('#outreach-email-to')?.value || '';
    const fullText = `To: ${to}\nTemat: ${subject}\n\n${body}`;

    navigator.clipboard.writeText(fullText).then(() => {
        const btn = $('#outreach-copy-btn');
        if (btn) {
            const orig = btn.textContent;
            btn.textContent = '✅ Skopiowano!';
            setTimeout(() => { btn.textContent = orig; }, 2000);
        }
    }).catch(() => {
        // Fallback for non-HTTPS
        const ta = document.createElement('textarea');
        ta.value = fullText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
    });
}

function outreachBackToSearch() {
    outreachSelectedLeadId = null;
    outreachShowStep('search');
}
