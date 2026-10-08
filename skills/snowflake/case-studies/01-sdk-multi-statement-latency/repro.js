/**
 * Reproduce the per-statement latency an app team reported with the Snowflake Node.js SDK.
 *
 * It compares four ways of running the same SELECT:
 *   A. The app's original pattern: new connection per request + 4-statement multi-statement query
 *   B. Same multi-statement query, but on one reused connection
 *   C. Single fully-qualified SELECT on a reused connection, with warehouse/db/schema
 *      set in the connection config (no USE / ALTER SESSION statements)
 *   D. Same as C, but through a connection pool (snowflake.createPool)
 *
 * Setup:
 *   npm install snowflake-sdk
 *
 *   export SF_ACCOUNT=myorg-myaccount
 *   export SF_USER=REPRO_USER
 *   export SF_ROLE=REPRO_ROLE
 *   export SF_WAREHOUSE=REPRO_WH
 *   # Auth, pick one:
 *   export SF_PRIVATE_KEY_PATH=/path/to/rsa_key.p8   # key-pair (recommended)
 *   export SF_PASSWORD=...                            # or password (fails if MFA is enforced)
 *
 *   # Optional:
 *   export SF_DATABASE=SNOWFLAKE_SAMPLE_DATA SF_SCHEMA=TPCH_SF1 SF_TABLE=NATION
 *   export ITER=10
 *
 *   node repro.js
 *
 * Tip: run it from the same cloud region / network as the real app. Latency from a
 * laptop will differ, because every round trip is multiplied by the distance.
 */

const snowflake = require('snowflake-sdk');
const { performance } = require('perf_hooks');

snowflake.configure({ logLevel: 'ERROR' });

const env = process.env;
const DB = env.SF_DATABASE || 'SNOWFLAKE_SAMPLE_DATA';
const SCHEMA = env.SF_SCHEMA || 'TPCH_SF1';
const TABLE = env.SF_TABLE || 'NATION';
const WH = env.SF_WAREHOUSE;
const ITER = parseInt(env.ITER || '10', 10);

for (const k of ['SF_ACCOUNT', 'SF_USER', 'SF_WAREHOUSE']) {
  if (!env[k]) { console.error(`Missing env var ${k}`); process.exit(1); }
}

const baseConfig = {
  account: env.SF_ACCOUNT,
  username: env.SF_USER,
  role: env.SF_ROLE,
  ...(env.SF_PRIVATE_KEY_PATH
    ? { authenticator: 'SNOWFLAKE_JWT', privateKeyPath: env.SF_PRIVATE_KEY_PATH }
    : { password: env.SF_PASSWORD }),
};

// Config for the original pattern (A, B). A multi-statement request needs a warehouse on the
// session before its first statement runs, so the in-batch USE WAREHOUSE isn't enough.
// The real app presumably gets this from a user default or its connection config.
const multiConfig = { ...baseConfig, warehouse: WH };

// Config for the "fixed" scenarios: context comes from the connection, not from SQL.
const configWithDefaults = { ...baseConfig, warehouse: WH, database: DB, schema: SCHEMA };

// The original 4-statement request
const MULTI_SQL = [
  `USE WAREHOUSE ${WH}`,
  `USE SCHEMA "${DB}"."${SCHEMA}"`,
  `ALTER SESSION SET DEFAULT_NULL_ORDERING = 'FIRST', STATEMENT_TIMEOUT_IN_SECONDS = 300`,
  `SELECT * FROM "${TABLE}"`,
].join(';\n');

const SINGLE_SQL = `SELECT * FROM "${DB}"."${SCHEMA}"."${TABLE}"`;

// ---------- helpers ----------

function connect(config) {
  const conn = snowflake.createConnection(config);
  return new Promise((resolve, reject) =>
    conn.connect((err, c) => (err ? reject(err) : resolve(c))));
}

function destroy(conn) {
  return new Promise((resolve) => conn.destroy(() => resolve()));
}

function queryIdOf(stmt) {
  if (typeof stmt.getQueryId === 'function') return stmt.getQueryId();
  if (typeof stmt.getStatementId === 'function') return stmt.getStatementId();
  return '?';
}

// Runs a multi-statement request, skipping all results except the last one (the original pattern).
function execMulti(conn, sqlText, count) {
  return new Promise((resolve, reject) => {
    const t0 = performance.now();
    const ids = [];
    conn.execute({
      sqlText,
      parameters: { MULTI_STATEMENT_COUNT: count },
      complete: (err, stmt, rows) => {
        if (err) return reject(err);
        ids.push(queryIdOf(stmt));
        if (typeof stmt.hasNext === 'function' && stmt.hasNext()) {
          stmt.NextResult();
          return;
        }
        resolve({ ms: performance.now() - t0, rows: rows ? rows.length : 0, ids });
      },
    });
  });
}

function execSingle(conn, sqlText) {
  return new Promise((resolve, reject) => {
    const t0 = performance.now();
    conn.execute({
      sqlText,
      complete: (err, stmt, rows) => {
        if (err) return reject(err);
        resolve({ ms: performance.now() - t0, rows: rows ? rows.length : 0, ids: [queryIdOf(stmt)] });
      },
    });
  });
}

function stats(arr) {
  const s = [...arr].sort((a, b) => a - b);
  const pick = (p) => s[Math.min(s.length - 1, Math.floor(p * s.length))];
  return {
    median: pick(0.5).toFixed(0),
    p95: pick(0.95).toFixed(0),
    min: s[0].toFixed(0),
    max: s[s.length - 1].toFixed(0),
  };
}

// ---------- scenarios ----------

async function scenarioA() {
  // New connection per request, multi-statement (worst case)
  const total = [], queryOnly = [], connectOnly = [];
  let lastIds = [];
  for (let i = 0; i <= ITER; i++) {
    const t0 = performance.now();
    const conn = await connect(multiConfig);
    const t1 = performance.now();
    const r = await execMulti(conn, MULTI_SQL, 4);
    const t2 = performance.now();
    await destroy(conn);
    if (i === 0) continue; // warm-up
    connectOnly.push(t1 - t0); queryOnly.push(r.ms); total.push(t2 - t0);
    lastIds = r.ids;
  }
  return { name: 'A: new conn + 4-stmt multi', total, queryOnly, connectOnly, lastIds };
}

async function scenarioB() {
  // Reused connection, still multi-statement
  const conn = await connect(multiConfig);
  const queryOnly = [];
  let lastIds = [];
  for (let i = 0; i <= ITER; i++) {
    const r = await execMulti(conn, MULTI_SQL, 4);
    if (i === 0) continue;
    queryOnly.push(r.ms); lastIds = r.ids;
  }
  await destroy(conn);
  return { name: 'B: reused conn + 4-stmt multi', queryOnly, lastIds };
}

async function scenarioC() {
  // Reused connection, context from connection config, single SELECT
  const conn = await connect(configWithDefaults);
  const queryOnly = [];
  let lastIds = [];
  for (let i = 0; i <= ITER; i++) {
    const r = await execSingle(conn, SINGLE_SQL);
    if (i === 0) continue;
    queryOnly.push(r.ms); lastIds = r.ids;
  }
  await destroy(conn);
  return { name: 'C: reused conn + single SELECT', queryOnly, lastIds };
}

async function scenarioD() {
  // Pooled connections, single SELECT
  const pool = snowflake.createPool(configWithDefaults, { max: 2, min: 1 });
  const queryOnly = [];
  let lastIds = [];
  for (let i = 0; i <= ITER; i++) {
    const t0 = performance.now();
    const r = await pool.use(async (conn) => execSingle(conn, SINGLE_SQL));
    const ms = performance.now() - t0; // includes pool acquire
    if (i === 0) continue;
    queryOnly.push(ms); lastIds = r.ids;
  }
  await pool.drain();
  await pool.clear();
  return { name: 'D: pool + single SELECT', queryOnly, lastIds };
}

// ---------- main ----------

(async () => {
  const startedAt = new Date();
  console.log(`Running ${ITER} iterations per scenario (+1 warm-up) against ${DB}.${SCHEMA}.${TABLE}\n`);

  const results = [];
  for (const fn of [scenarioA, scenarioB, scenarioC, scenarioD]) {
    try {
      const r = await fn();
      results.push(r);
      console.log(`done: ${r.name}`);
    } catch (e) {
      console.error(`failed: ${fn.name}: ${e.message}`);
    }
  }

  console.log('\nClient-side timings (ms):');
  const rows = {};
  for (const r of results) {
    rows[r.name] = { ...stats(r.queryOnly), ...(r.connectOnly ? { connect_median: stats(r.connectOnly).median } : {}) };
    if (r.total) rows[r.name].total_median = stats(r.total).median;
  }
  console.table(rows);

  console.log('\nQuery IDs from the last iteration of each scenario:');
  for (const r of results) console.log(`  ${r.name}: ${r.lastIds.join(', ')}`);

  console.log(`
Compare against server-side timings (run in a worksheet as an admin):

SELECT query_id, query_type, LEFT(query_text, 60) AS query_text,
       start_time, end_time,
       compilation_time, queued_provisioning_time, queued_overload_time,
       execution_time, total_elapsed_time
FROM TABLE(information_schema.query_history_by_user(
       user_name => '${env.SF_USER.toUpperCase()}',
       end_time_range_start => '${startedAt.toISOString()}'::timestamp_ltz,
       result_limit => 1000))
ORDER BY start_time;

Client time minus total_elapsed_time = network + SDK overhead.
Gaps between one child statement's end_time and the next one's start_time = round trips.
`);
})();
