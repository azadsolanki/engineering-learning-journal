/**
 * Tests null-ordering options through the Snowflake SQL API (POST /api/v2/statements),
 * the API the app team moved to from the SDK.
 *
 *   Test 0  Baseline: no settings                        -> expect 1, 2, NULL (Snowflake default is LAST)
 *   Test 1  DEFAULT_NULL_ORDERING in "parameters"        -> expect an error (the reported issue)
 *   Test 2  ALTER SESSION + SELECT in one request        -> expect NULL, 1, 2
 *   Test 3  Explicit ORDER BY ... NULLS FIRST            -> expect NULL, 1, 2
 *   Test 4  Baseline again after Test 2                  -> checks the ALTER SESSION didn't leak
 *                                                           into a later request
 *   Test 5  ALTER SESSION ... FIRST + ORDER BY DESC      -> expect 2, 1, NULL (original behavior)
 *   Test 6  ORDER BY ... DESC NULLS FIRST                -> expect NULL, 2, 1 (differs from Test 5)
 *   Test 7  ORDER BY ... DESC NULLS LAST                 -> expect 2, 1, NULL (matches Test 5)
 *
 * No npm packages needed (Node 18+). Uses the same env vars as repro.js:
 *   SF_ACCOUNT, SF_USER, SF_ROLE, SF_WAREHOUSE, SF_PRIVATE_KEY_PATH
 *
 * Run: node sqlapi_test.js
 */

const crypto = require('crypto');
const fs = require('fs');

const env = process.env;
for (const k of ['SF_ACCOUNT', 'SF_USER', 'SF_WAREHOUSE', 'SF_PRIVATE_KEY_PATH']) {
  if (!env[k]) { console.error(`Missing env var ${k}`); process.exit(1); }
}

const ACCOUNT = env.SF_ACCOUNT;
const HOST = `https://${ACCOUNT.toLowerCase()}.snowflakecomputing.com`;
const SQL = 'SELECT column1 AS V FROM VALUES (2), (NULL), (1) ORDER BY column1';
const DESC_SQL = 'SELECT column1 AS V FROM VALUES (2), (NULL), (1) ORDER BY column1 DESC';

// The SQL API accepted the statement count as an upper-case key with a string value.
// A lower-case key was read as a count of 1 and the request failed with HTTP 422.
const MULTI_2 = { MULTI_STATEMENT_COUNT: '2' };

// ---------- key-pair JWT auth ----------

function makeJwt() {
  const privateKey = crypto.createPrivateKey(fs.readFileSync(env.SF_PRIVATE_KEY_PATH));
  const pubDer = crypto.createPublicKey(privateKey).export({ type: 'spki', format: 'der' });
  const fingerprint = 'SHA256:' + crypto.createHash('sha256').update(pubDer).digest('base64');

  // The JWT uses the account name in upper case, with "." replaced by "-".
  const acct = ACCOUNT.toUpperCase().replace(/\./g, '-');
  const user = env.SF_USER.toUpperCase();
  const now = Math.floor(Date.now() / 1000);

  const b64url = (obj) => Buffer.from(JSON.stringify(obj)).toString('base64url');
  const header = b64url({ alg: 'RS256', typ: 'JWT' });
  const payload = b64url({
    iss: `${acct}.${user}.${fingerprint}`,
    sub: `${acct}.${user}`,
    iat: now,
    exp: now + 3600,
  });
  const signature = crypto.sign('RSA-SHA256', Buffer.from(`${header}.${payload}`), privateKey)
    .toString('base64url');
  return `${header}.${payload}.${signature}`;
}

const HEADERS = {
  Authorization: `Bearer ${makeJwt()}`,
  'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
  'Content-Type': 'application/json',
  Accept: 'application/json',
  'User-Agent': 'null-ordering-test/1.0',
};

// ---------- SQL API helpers ----------

async function call(method, path, body) {
  const res = await fetch(HOST + path, {
    method,
    headers: HEADERS,
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let json;
  try { json = JSON.parse(text); } catch { json = { raw: text }; }
  return { status: res.status, json };
}

// Waits while a statement is still running (HTTP 202).
async function waitFor(handle) {
  for (;;) {
    const r = await call('GET', `/api/v2/statements/${handle}`);
    if (r.status !== 202) return r;
    await new Promise((ok) => setTimeout(ok, 250));
  }
}

async function submit(statement, parameters = {}) {
  const t0 = Date.now();
  let r = await call('POST', '/api/v2/statements', {
    statement,
    timeout: 300, // request-level replacement for STATEMENT_TIMEOUT_IN_SECONDS
    warehouse: env.SF_WAREHOUSE,
    role: env.SF_ROLE,
    parameters,
  });
  if (r.status === 202) r = await waitFor(r.json.statementHandle);
  return { ...r, ms: Date.now() - t0 };
}

// Submits a multi-statement request and returns only the last statement's result.
async function submitLastOnly(statement) {
  const r = await submit(statement, MULTI_2);
  if (r.status !== 200 || !Array.isArray(r.json.statementHandles)) return r;
  const handles = r.json.statementHandles;
  const last = await waitFor(handles[handles.length - 1]);
  return { ...last, ms: r.ms };
}

const values = (r) => (r.json.data || []).map((row) => row[0]);
const fmt = (vals) => vals.map((v) => (v === null ? 'NULL' : v)).join(', ');

function report(name, expected, r) {
  if (r.status !== 200) {
    console.log(`${name}\n  HTTP ${r.status}  code=${r.json.code}  message=${r.json.message || JSON.stringify(r.json)}\n`);
    return;
  }
  const got = fmt(values(r));
  const verdict = got === expected ? 'AS EXPECTED' : 'DIFFERENT FROM EXPECTED';
  console.log(`${name}\n  result: ${got}   (expected ${expected})  ${verdict}  [${r.ms} ms]\n`);
}

// ---------- tests ----------

(async () => {
  console.log(`SQL API host: ${HOST}\n`);

  const t0 = await submit(SQL);
  if (t0.status === 401 || t0.status === 403) {
    console.error(`Auth failed (HTTP ${t0.status}): ${t0.json.message || JSON.stringify(t0.json)}`);
    process.exit(1);
  }
  report('Test 0: baseline, no settings', '1, 2, NULL', t0);

  report('Test 1: DEFAULT_NULL_ORDERING in "parameters" (expect an error)', 'NULL, 1, 2',
    await submit(SQL, { default_null_ordering: 'FIRST' }));

  report('Test 2: ALTER SESSION + SELECT in one request', 'NULL, 1, 2',
    await submitLastOnly(`ALTER SESSION SET DEFAULT_NULL_ORDERING = 'FIRST';\n${SQL}`));

  report('Test 3: ORDER BY ... NULLS FIRST', 'NULL, 1, 2',
    await submit(`${SQL} NULLS FIRST`));

  report('Test 4: baseline again after Test 2 (checks for leaking session settings)', '1, 2, NULL',
    await submit(SQL));

  // ---- Descending sorts: does NULLS FIRST really match DEFAULT_NULL_ORDERING = 'FIRST'? ----

  report('Test 5: DEFAULT_NULL_ORDERING = FIRST with ORDER BY DESC (original behavior)', '2, 1, NULL',
    await submitLastOnly(`ALTER SESSION SET DEFAULT_NULL_ORDERING = 'FIRST';\n${DESC_SQL}`));

  report('Test 6: ORDER BY ... DESC NULLS FIRST (expected to differ from Test 5)', 'NULL, 2, 1',
    await submit(`${DESC_SQL} NULLS FIRST`));

  report('Test 7: ORDER BY ... DESC NULLS LAST (expected to match Test 5)', '2, 1, NULL',
    await submit(`${DESC_SQL} NULLS LAST`));
})().catch((e) => { console.error('Unexpected error:', e); process.exit(1); });
