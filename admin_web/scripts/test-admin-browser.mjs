// Browser regression against synthetic HTTP responses only; no backend data is used.
// Run after npm run build. Chrome can be overridden with CHROME_PATH.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const adminRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const temporaryRoot = resolve(tmpdir());
const profile = await mkdtemp(join(temporaryRoot, 'tlangua-admin-browser-'));
const requests = [];
const results = [];
let role = 'admin';
let failPublish = false;
let failLists = false;
let failDashboard = false;
let forceUserValidation = false;
const logs = Array.from({ length: 123 }, (_, index) => ({ id: index + 1, client_id: 'synthetic-client', source_text: `source ${index + 1}`, translated_text: `translation ${index + 1}`, source_lang: 'en', target_lang: 'vi', is_flagged: true, is_reviewed: false, latency: 0, created_at: '2026-09-13T00:00:00' }));
const users = Array.from({ length: 123 }, (_, index) => ({ id: index + 1, username: `user${index + 1}`, role: 'employee', public_id: `test-${index}`, is_active: true }));
const keys = Array.from({ length: 123 }, (_, index) => ({ id: index + 1, name: `key${index + 1}`, prefix: `tk_${index}`, scopes: ['translate'], expires_at: '2099-01-01T00:00:00Z', created_at: '2026-09-13T00:00:00Z', is_active: true }));
let dictionary = Array.from({ length: 1003 }, (_, index) => ({ source_text: index === 0 ? 'qa/a?b#c%' : `word${index + 1}`, translated_text: `term${index + 1}`, source_lang: 'en', target_lang: 'vi' }));
const settings = [
  { id: 1, key: 'max_chars_per_request', value: '5000', description: 'Giới hạn ký tự' },
  { id: 2, key: 'rate_limit_rpm', value: '60', description: 'Giới hạn yêu cầu' },
  { id: 3, key: 'enable_cache', value: 'true', description: 'Bộ nhớ đệm' },
];
const deployments = ['whisper', 'nllb', 'tts_eng', 'tts_vie'].map((component, index) => ({
  component, active_model: `synthetic/${component}-v1`, canary_model: null,
  canary_percent: 0, previous_active_model: null, version: index + 1,
  requires_runtime_reload: true,
}));
const trainingOverview = {
  runtime: { status: 'online', gpu: { cuda_available: true, device_name: 'Synthetic GPU', reserved_mb: 1024, total_mb: 16384 }, worker: 'idle', active_job_id: null },
  whisper: { samples: 12, hours: 0.1, speakers: 3, hours_by_language: { vi: 0.08, en: 0.02 }, splits: { train: 10, validation: 1, test: 1 }, ready: true, recommended_hours: 10, recommended_speakers: 30 },
  nllb: { samples: 20, directions: { 'vi-en': 10, 'en-vi': 10 }, splits: { train: 16, validation: 2, test: 2 }, ready: true, recommended_pairs_per_direction: 5000 },
  playground: { available: false, reason: 'Synthetic candidate runner is not configured' },
};

function paginate(data, url) {
  const query = (url.searchParams.get('search') || '').toLowerCase();
  const matches = data.filter(item => Object.values(item).some(value => String(value).toLowerCase().includes(query)));
  const skip = Number(url.searchParams.get('skip') || 0);
  return matches.slice(skip, skip + Number(url.searchParams.get('limit') || 100));
}

const server = createServer(async (request, response) => {
  try {
    const url = new URL(request.url, 'http://localhost');
    if (!url.pathname.startsWith('/admin/') && url.pathname !== '/api/session/logout') {
      const relative = url.pathname.startsWith('/assets/') ? url.pathname.slice(1) : 'index.html';
      const file = resolve(adminRoot, 'dist', relative);
      if (!file.startsWith(resolve(adminRoot, 'dist') + sep)) throw new Error('Invalid static path');
      response.setHeader('Content-Type', relative.endsWith('.js') ? 'text/javascript' : relative.endsWith('.css') ? 'text/css' : 'text/html');
      response.end(await readFile(file));
      return;
    }
    let body = '';
    for await (const chunk of request) body += chunk;
    const contentType = request.headers['content-type'] || '';
    const data = contentType.includes('application/json') && body ? JSON.parse(body) : null;
    requests.push({ method: request.method, path: url.pathname, params: Object.fromEntries(url.searchParams), data, multipart: url.pathname.endsWith('/upload') ? body : undefined });
    const respond = (value, status = 200) => { response.writeHead(status, { 'Content-Type': 'application/json' }); response.end(JSON.stringify(value)); };
    const user = () => ({ id: 999, username: role, role, public_id: 'synthetic-admin', is_active: true });
    if (url.pathname === '/admin/login') { role = new URLSearchParams(body).get('username') === 'superadmin' ? 'superadmin' : 'admin'; respond({ access_token: 'synthetic-session', token_type: 'bearer', expires_in: 3600, user: user() }); }
    else if (url.pathname === '/admin/me') respond(user());
    else if (url.pathname === '/api/session/logout') respond({ ok: true });
    else if (url.pathname === '/admin/quality/logs') {
      if (failLists) { respond({ detail: 'Synthetic list failure' }, 503); return; }
      const status = url.searchParams.get('review_status');
      respond(paginate(logs.filter(log => status === 'pending' ? !log.is_reviewed : status === 'reviewed' ? log.is_reviewed : true), url));
    } else if (/\/quality\/logs\/\d+\/resolve$/.test(url.pathname)) {
      const log = logs.find(item => item.id === Number(url.pathname.split('/').at(-2)));
      Object.assign(log, {
        translated_text: data.corrected_text, stt_corrected: data.corrected_source_text,
        translation_status: data.translation_status, stt_status: data.stt_status,
        consent_for_training: data.consent_for_training, pii_status: data.pii_status,
        use_for_nllb: data.use_for_nllb, use_for_whisper: data.use_for_whisper,
        domain: data.domain, is_reviewed: true, is_flagged: false,
      });
      respond({ ok: true });
    } else if (url.pathname === '/admin/dictionary/delete') {
      dictionary = dictionary.filter(item => item.source_text !== data.source_text || item.source_lang !== data.source_lang || item.target_lang !== data.target_lang);
      respond({ ok: true });
    } else if (url.pathname === '/admin/dictionary/upload') respond({ ok: true, added: 1 });
    else if (url.pathname === '/admin/dictionary' && request.method === 'POST') {
      if (failPublish) { failPublish = false; respond({ detail: 'Synthetic publish unavailable' }, 503); }
      else { dictionary.unshift(data); respond({ ok: true }); }
    } else if (url.pathname === '/admin/dictionary') respond(paginate(dictionary, url));
    else if (url.pathname === '/admin/users' && request.method === 'POST') {
      if (forceUserValidation) respond({ detail: [{ loc: ['body', 'username'], type: 'string_too_short', msg: 'String should have at least 3 characters', ctx: { min_length: 3 } }] }, 422);
      else respond({ id: 9000, ...data, is_active: true });
    } else if (/\/admin\/users\/\d+$/.test(url.pathname) && request.method === 'PATCH') {
      const item = users.find(value => value.id === Number(url.pathname.split('/').at(-1)));
      Object.assign(item, data); respond(item);
    } else if (url.pathname === '/admin/users') respond(paginate(users, url));
    else if (url.pathname === '/admin/apikeys') respond(paginate(keys, url));
    else if (url.pathname === '/admin/settings') respond(settings);
    else if (url.pathname === '/admin/audit') respond([]);
    else if (url.pathname === '/admin/models/deployments') respond(deployments);
    else if (url.pathname === '/admin/training/overview') respond(trainingOverview);
    else if (url.pathname === '/admin/training/datasets/preview-from-qa') respond({
      task: data.task, reviewed: 4, eligible: 1, splits: { train: 1, validation: 0, test: 0 },
      directions: { 'vi->en': 1 }, duration_seconds: 0, ready: false,
      blockers: { no_consent: 2, pii_not_cleared: 2, not_approved: 1, missing_audio: 0 },
      reasons: ['Thiếu dữ liệu validation'],
    });
    else if (url.pathname === '/admin/training/datasets') respond([]);
    else if (url.pathname === '/admin/training/jobs') respond([]);
    else if (url.pathname === '/admin/training/models') respond([]);
    else if (/\/admin\/models\/[^/]+\/(canary|promote|rollback)$/.test(url.pathname)) {
      const parts = url.pathname.split('/');
      const component = parts.at(-2); const operation = parts.at(-1);
      const deployment = deployments.find(item => item.component === component);
      if (operation === 'canary') {
        deployment.canary_model = data.model_id; deployment.canary_percent = data.percent;
      } else if (operation === 'promote') {
        deployment.previous_active_model = deployment.active_model; deployment.active_model = deployment.canary_model;
        deployment.canary_model = null; deployment.canary_percent = 0;
      } else {
        const current = deployment.active_model; deployment.active_model = deployment.previous_active_model;
        deployment.previous_active_model = current; deployment.canary_model = null; deployment.canary_percent = 0;
      }
      deployment.version += 1; respond(deployment);
    }
    else if (url.pathname.startsWith('/admin/settings/')) {
      const setting = settings.find(item => item.key === url.pathname.split('/').at(-1));
      setting.value = setting.key === 'enable_cache' ? data.value.trim().toLowerCase() : String(Number(data.value));
      respond(setting);
    } else if (url.pathname === '/admin/metrics/dashboard') {
      if (failDashboard) respond({ detail: 'Synthetic metric failure' }, 503);
      else respond({ total_translations: 12, unique_clients: 2, avg_latency: 0.4, flagged_translations: 1, sample_limit: 1000, scope: 'since_process_start', started_at: '2026-09-13T00:00:00Z' });
    } else if (url.pathname === '/admin/system/status') respond({ cpu_usage: 1, ram_usage: 20, ram_total: 16, disk_usage: 30, disk_total: 100, inference_runtime: { whisper_device: 'cpu', whisper_compute_type: 'int8', whisper_cpu_fallback: true } });
    else if (url.pathname === '/admin/metrics/timeseries' || url.pathname === '/admin/metrics/languages') respond([]);
    else if (url.pathname === '/admin/metrics/pipeline') {
      const stage = { p50: 12, p90: 24, p99: 40, avg: 15 };
      respond({ active_turns: 0, total_completed: 12, total_errors: 0, throughput_turns_per_sec: 0.2, latencies_ms: Object.fromEntries(['queue_wait', 'stt', 'translate', 'tts_first_chunk', 'tts_total', 'end_to_end'].map(name => [name, stage])) });
    } else respond({ detail: `Unmocked endpoint ${url.pathname}` }, 404);
  } catch (error) { response.writeHead(500); response.end(String(error)); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const chrome = spawn(process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank',
], { windowsHide: true, stdio: 'ignore' });
let socket;
const sleep = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
const pending = new Map();
let sequence = 0;
const browserErrors = [];
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
    pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text + ': ' + result.exceptionDetails.exception?.description);
  return result.result.value;
}
async function waitFor(expression) {
  for (let index = 0; index < 100; index++) { if (await evaluate(expression)) return; await sleep(60); }
  throw new Error(`Timed out waiting: ${expression}\n${await evaluate('document.body.innerText')}`);
}
async function click(expression) {
  await waitFor(`!!(${expression}) && !(${expression}).disabled`);
  const rect = await evaluate(`(() => { const element = ${expression}; element.scrollIntoView({block:'center'}); const r = element.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`);
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', button: 'left', clickCount: 1, ...rect });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', button: 'left', clickCount: 1, ...rect });
}
const button = text => `Array.from(document.querySelectorAll('button')).find(element => element.textContent.trim() === ${JSON.stringify(text)})`;
const label = text => `Array.from(document.querySelectorAll('label')).find(element => element.textContent.trim() === ${JSON.stringify(text)})?.control`;
async function fill(expression, value) {
  await waitFor(`!!(${expression})`);
  await evaluate(`(() => { const element=${expression}; const proto=element.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(proto,'value').set.call(element,${JSON.stringify(value)}); element.dispatchEvent(new Event('input',{bubbles:true})); })()`);
}
async function navigate(path) { await click(`document.querySelector('a[href="${path}"]')`); await waitFor(`location.pathname === ${JSON.stringify(path)}`); }
async function login(username) {
  await fill(label('Tên đăng nhập'), username);
  await fill(label('Mật khẩu'), 'SyntheticPassword123!');
  await click(`document.querySelector('button[type="submit"]')`);
  await waitFor("location.pathname === '/' && document.body.innerText.includes('Khách hàng đã phục vụ')");
}
async function check(name, work) { await work(); results.push(name); console.log(`PASS ${name}`); }

try {
  let debuggingPort;
  for (let i = 0; i < 100; i++) {
    try { debuggingPort = Number((await readFile(join(profile, 'DevToolsActivePort'), 'utf8')).split('\n')[0]); break; } catch { await sleep(100); }
  }
  assert(debuggingPort, 'Chrome did not start');
  const targets = await (await fetch(`http://127.0.0.1:${debuggingPort}/json`)).json();
  socket = new WebSocket(targets.find(target => target.type === 'page').webSocketDebuggerUrl);
  await new Promise(resolve => socket.addEventListener('open', resolve, { once: true }));
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const job = pending.get(message.id); pending.delete(message.id);
      if (job) { if (message.error) job.reject(new Error(message.error.message)); else job.resolve(message.result); }
    }
    else if (message.method === 'Page.javascriptDialogOpening') void send('Page.handleJavaScriptDialog', { accept: true });
    else if (message.method === 'Runtime.exceptionThrown') browserErrors.push(message.params.exceptionDetails.text);
  });
  console.log('Chrome connected', await send('Browser.getVersion'));
  await send('Page.enable'); await send('Runtime.enable');
  await send('Emulation.setTimezoneOverride', { timezoneId: 'Asia/Bangkok' });
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: `${origin}/login` });
  await waitFor("document.querySelectorAll('label').length === 3");
  await check('Login labels link to all three controls', async () => assert.equal(await evaluate("Array.from(document.querySelectorAll('label')).every(label => !!label.control)"), true));
  await login('admin');
  await navigate('/qa');
  await waitFor("document.querySelectorAll('tbody tr').length === 25");
  await check('Admin cannot publish dictionary from QA', async () => {
    assert.equal(await evaluate("document.body.innerText.includes('Thêm vào từ điển')"), false);
    await click(button('Kiểm tra'));
    assert.equal(await evaluate("document.body.innerText.includes('Có quyền huấn luyện')"), true);
    await click(button('Hủy'));
  });
  await click(button('Đăng xuất')); await waitFor("location.pathname === '/login'"); await login('superadmin');
  await navigate('/training-center'); await waitFor("document.body.innerText.includes('Trung tâm huấn luyện AI')");
  await check('Training Center exposes five real workflow tabs and safe A/B state', async () => {
    assert.equal(await evaluate("document.querySelectorAll('[role=tab]').length"), 5);
    assert.equal(await evaluate("document.body.innerText.includes('Synthetic GPU')"), true);
    await click(button('A/B Playground'));
    await waitFor("document.body.innerText.includes('Playground đang khóa an toàn')");
    assert.equal(await evaluate("document.body.innerText.includes('Synthetic candidate runner is not configured')"), true);
  });
  await click(button('Datasets'));
  await fill(label('Tên dataset'), 'synthetic-preview');
  await check('Dataset preview explains blockers before snapshot creation', async () => {
    await click(button('Kiểm tra dữ liệu'));
    await waitFor("document.body.innerText.includes('Chưa thể tạo dataset train được')");
    assert.equal(await evaluate("document.body.innerText.includes('Thiếu dữ liệu validation')"), true);
    assert.equal(await evaluate("Array.from(document.querySelectorAll('button')).find(button => button.textContent.trim() === 'Tạo dataset').disabled"), true);
  });
  await navigate('/qa'); await waitFor("document.querySelectorAll('tbody tr').length === 25");
  await check('QA save carries training rights, PII state and model eligibility', async () => {
    await click(button('Kiểm tra')); await fill("document.querySelector('textarea[aria-label^=\"Bản dịch\"]')", 'Bản sửa tổng hợp');
    await click("Array.from(document.querySelectorAll('label')).find(label => label.textContent.includes('Có quyền huấn luyện')).querySelector('input')");
    await evaluate("(() => { const element=Array.from(document.querySelectorAll('label')).find(label => label.textContent.includes('Kiểm tra PII')).querySelector('select'); element.value='clean'; element.dispatchEvent(new Event('change',{bubbles:true})); })()");
    await evaluate("(() => { const element=Array.from(document.querySelectorAll('label')).find(label => label.textContent.includes('Tập dữ liệu NLLB')).querySelector('select'); element.value='validation'; element.dispatchEvent(new Event('change',{bubbles:true})); })()");
    await click(button('Lưu'));
    await waitFor("document.body.innerText.includes('lần tạo snapshot dataset tiếp theo') && !document.querySelector('textarea')");
    assert.equal(requests.filter(request => request.path.endsWith('/1/resolve')).length, 1);
    const saved = requests.find(request => request.path.endsWith('/1/resolve')).data;
    assert.equal(saved.consent_for_training, true); assert.equal(saved.pii_status, 'clean');
    assert.equal(saved.use_for_nllb, true); assert.equal(saved.nllb_split, 'validation'); assert.equal(saved.corrected_text, 'Bản sửa tổng hợp');
  });
  await check('QA filters apply server-side across pages', async () => {
    await click(button('Đã chỉnh sửa')); await waitFor("document.querySelectorAll('tbody tr').length === 1");
    assert.equal(requests.filter(request => request.path === '/admin/quality/logs').at(-1).params.review_status, 'reviewed');
  });
  await navigate('/history'); await waitFor("document.querySelectorAll('tbody tr').length === 25");
  await check('UTC timestamp and zero latency display correctly', async () => {
    const row = await evaluate("document.querySelector('tbody tr').innerText");
    assert.match(row, /07:00:00/); assert.match(row, /0\.000s/);
  });
  await check('Draft search does not affect pagination; submit starts page one', async () => {
    await fill(label('Tìm kiếm nội dung'), 'source 123'); await click(button('Sau'));
    await waitFor("document.querySelector('tbody tr').innerText.includes('#26')");
    let request = requests.filter(request => request.path === '/admin/quality/logs').at(-1);
    assert.equal(request.params.skip, '25'); assert.equal(request.params.search, undefined);
    await click(button('Tìm kiếm')); await waitFor("document.querySelector('tbody tr').innerText.includes('#123')");
    request = requests.filter(request => request.path === '/admin/quality/logs').at(-1);
    assert.equal(request.params.skip, '0'); assert.equal(request.params.search, 'source 123');
  });
  await check('List refresh failure is marked stale, then retry recovers', async () => {
    failLists = true; await click(button('Tìm kiếm'));
    await waitFor("document.body.innerText.includes('Danh sách vẫn là dữ liệu tải lần trước.')");
    assert.equal(await evaluate("document.querySelector('tbody tr').innerText.includes('#123')"), true);
    failLists = false; await click(button('Thử lại'));
    await waitFor("!document.body.innerText.includes('Danh sách vẫn là dữ liệu tải lần trước.')");
  });
  await check('Mobile heading and menu do not overlap; Escape closes menu', async () => {
    await send('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
    const boxes = await evaluate("(() => {const a=document.querySelector('h1').getBoundingClientRect(),b=document.querySelector('[aria-controls=admin-sidebar]').getBoundingClientRect(); return {headingY:a.y,menuBottom:b.bottom};})()");
    assert(boxes.headingY >= boxes.menuBottom);
    await click("document.querySelector('[aria-controls=admin-sidebar]')");
    assert.equal(await evaluate("document.querySelector('[aria-controls=admin-sidebar]').getAttribute('aria-expanded')"), 'true');
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await waitFor("document.querySelector('[aria-controls=admin-sidebar]').getAttribute('aria-expanded') === 'false'");
    await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });
  });
  for (const [path, inputLabel, term] of [['/users', 'Tìm tên đăng nhập', 'user123'], ['/apikeys', 'Tìm tên hoặc tiền tố mã API', 'key123'], ['/dictionary', 'Tìm kiếm nội dung', 'word1003']]) {
    await navigate(path); await waitFor("document.querySelectorAll('tbody tr').length === 25");
    await check(`${path}: page two and search beyond old limit`, async () => {
      await click(button('Sau')); await waitFor("document.body.innerText.includes('Trang 2')");
      await fill(label(inputLabel), term); await click(button('Tìm kiếm'));
      await waitFor(`document.querySelector('tbody').innerText.includes(${JSON.stringify(term)})`);
      const request = requests.filter(request => request.path === `/admin${path}` && request.method === 'GET').at(-1);
      assert.equal(request.params.search, term); assert.equal(request.params.skip, '0');
    });
  }
  await check('Delete source containing slash, question mark, hash and percent uses JSON', async () => {
    await fill(label('Tìm kiếm nội dung'), 'qa/a'); await click(button('Tìm kiếm'));
    await waitFor("document.querySelector('tbody').innerText.includes('qa/a?b#c%')");
    await click("document.querySelector('button[aria-label=\"Xóa cặp dịch qa/a?b#c%\"]')");
    await waitFor("document.body.innerText.includes('Đã xóa cặp dịch.')");
    const deletion = requests.find(request => request.path === '/admin/dictionary/delete');
    assert.deepEqual(deletion.data, { source_text: 'qa/a?b#c%', source_lang: 'en', target_lang: 'vi' });
    assert.equal(await evaluate("document.querySelector('input[type=file]').accept"), '.csv,.xlsx');
  });
  await check('Manual dictionary addition includes the selected language direction', async () => {
    await fill(label('Văn bản gốc (Tiếng Việt)'), 'xin chào tổng hợp');
    await fill(label('Bản dịch chuẩn (Tiếng Anh)'), 'synthetic hello');
    await click(button('Thêm vào bộ nhớ'));
    await waitFor("document.body.innerText.includes('Đã lưu cặp dịch (Tiếng Việt → Tiếng Anh) vào từ điển.')");
    const entry = requests.filter(request => request.path === '/admin/dictionary' && request.method === 'POST').at(-1).data;
    assert.equal(entry.source_lang, 'vi'); assert.equal(entry.target_lang, 'en');
  });
  await check('Dictionary upload rejects XLS and carries language fields for CSV', async () => {
    const chooseFile = filename => evaluate(`(() => { const transfer=new DataTransfer(); transfer.items.add(new File(['xin chào,hello'],${JSON.stringify(filename)},{type:'text/csv'})); const input=document.querySelector('input[type=file]'); input.files=transfer.files; input.dispatchEvent(new Event('change',{bubbles:true})); })()`);
    await chooseFile('synthetic.xls');
    await waitFor("document.body.innerText.includes('Chọn file CSV UTF-8 hoặc XLSX có dữ liệu')");
    assert.equal(requests.filter(request => request.path === '/admin/dictionary/upload').length, 0);
    await chooseFile('synthetic.csv');
    await waitFor("document.body.innerText.includes('Đã nhập 1 cặp dịch vào từ điển.')");
    const upload = requests.find(request => request.path === '/admin/dictionary/upload').multipart;
    assert.match(upload, /name="source_lang"\r\n\r\nvi/); assert.match(upload, /name="target_lang"\r\n\r\nen/);
    assert.equal(await evaluate("document.querySelector('input[type=file]').value"), '');
  });
  await navigate('/users'); await waitFor("document.querySelectorAll('tbody tr').length === 25");
  await check('Unicode password byte limit is explained without submitting', async () => {
    await fill(label('Tên đăng nhập'), 'new-user'); await fill(label('Mật khẩu (ít nhất 12 ký tự)'), 'ấ'.repeat(30));
    const before = requests.filter(request => request.path === '/admin/users' && request.method === 'POST').length;
    await click(button('Tạo mới')); await waitFor("document.body.innerText.includes('Mật khẩu tối đa 72 byte UTF-8.')");
    assert.equal(requests.filter(request => request.path === '/admin/users' && request.method === 'POST').length, before);
  });
  await check('422 field errors identify the field and constraint', async () => {
    forceUserValidation = true; await fill(label('Mật khẩu (ít nhất 12 ký tự)'), 'ValidTestPassword123!'); await click(button('Tạo mới'));
    await waitFor("document.body.innerText.includes('Tên đăng nhập: Ít nhất 3 ký tự')");
  });
  await check('User role and password editor calls the protected update API', async () => {
    await click("document.querySelector('button[aria-label=\"Chỉnh sửa user1\"]')");
    await waitFor("document.body.innerText.includes('Quyền của user1')");
    await evaluate(`(() => { const element=${label('Quyền của user1')}; element.value='admin'; element.dispatchEvent(new Event('change',{bubbles:true})); })()`);
    await fill(label('Mật khẩu mới của user1 (để trống nếu giữ nguyên)'), 'ReplacementPassword123!');
    await click(button('Lưu')); await waitFor("!document.body.innerText.includes('Quyền của user1')");
    const update = requests.find(request => request.path === '/admin/users/1' && request.method === 'PATCH');
    assert.equal(update.data.role, 'admin'); assert.equal(update.data.password, 'ReplacementPassword123!');
  });
  await navigate('/settings'); await waitFor("document.body.innerText.includes('Triển khai & Quản lý Model AI')");
  await check('Settings use canonical saved value and success feedback', async () => {
    const maxCharacters = `document.querySelector('input[type="number"]')`;
    await fill(maxCharacters, '00042'); await click(button('Lưu thiết lập'));
    await waitFor("document.body.innerText.includes('Đã lưu')");
    assert.equal(await evaluate(`${maxCharacters}.value`), '42');
  });
  await check('Model canary configuration is sent with an explicit traffic percentage', async () => {
    const nllbCanary = `Array.from(document.querySelectorAll('label')).filter(element => element.textContent.trim() === 'Mã model Canary (hoặc chọn từ danh sách trên)')[1]?.control`;
    await fill(nllbCanary, 'synthetic/nllb-v2');
    await click("Array.from(document.querySelectorAll('button')).filter(element => element.textContent.includes('Lưu Canary'))[1]");
    await waitFor(`${nllbCanary}.value === 'synthetic/nllb-v2'`);
    const canary = requests.find(request => request.path === '/admin/models/nllb/canary');
    assert.equal(canary.data.percent, 10);
  });
  await check('First dashboard failure does not display fabricated zero metrics', async () => {
    failDashboard = true; await navigate('/');
    await waitFor("document.body.innerText.includes('Synthetic metric failure')");
    assert.equal(await evaluate("document.body.innerText.includes('Khách hàng đã phục vụ')"), false);
    failDashboard = false; await click(button('Thử lại'));
    await waitFor("document.body.innerText.includes('Khách hàng đã phục vụ')");
    assert.equal(await evaluate("document.body.innerText.includes('Đang dùng CPU dự phòng')"), true);
  });
  await navigate('/analytics'); await waitFor("document.body.innerText.includes('Độ trễ toàn trình (P50 / P90 / P99)')");
  await check('Analytics percentile labels and persisted time filters are clear', async () => {
    assert.equal(await evaluate("document.body.innerText.includes('P95')"), false);
    assert.equal(await evaluate("document.body.innerText.includes('Tất cả')"), true);
  });
  assert.deepEqual(browserErrors, []);
  console.log(JSON.stringify({ passed: results.length, failed: 0, browserErrors, results }, null, 2));
} finally {
  if (socket?.readyState === WebSocket.OPEN) { try { await send('Browser.close'); } catch { /* Already closed. */ } socket.close(); }
  chrome.kill();
  await new Promise(resolve => server.close(resolve));
  // Only remove the unique test profile whose resolved path is inside the OS temp directory.
  if (resolve(profile).startsWith(temporaryRoot + sep) && profile.includes('tlangua-admin-browser-')) {
    await rm(profile, { recursive: true, force: true, maxRetries: 6, retryDelay: 300 });
  }
}
