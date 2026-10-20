// 模拟工具下检查教学脚本的控制流；不模拟 QuickJS 安全边界。
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const files = {
  'package.json': JSON.stringify({ name: 'root', scripts: { test: 'node --test' }, unused: 'x'.repeat(1000) }),
  'packages/api/package.json': JSON.stringify({ name: 'api', scripts: {} }),
  'packages/web/package.json': JSON.stringify({ name: 'web', scripts: { test: 'vitest' } }),
};
const state = {};
const writes = {};
const tools = {
  read: async ({ path }) => {
    if (!(path in files)) throw new Error(`ENOENT: ${path}`);
    return files[path];
  },
  bash: async () => ({ output: 'one test failed', exit_code: 1, truncated: false }),
  write: async ({ path, content }) => { writes[path] = content; return 'written'; },
};

async function run(name) {
  const code = await readFile(new URL(`./scripts/${name}`, import.meta.url), 'utf8');
  const output = [];
  const pending = structuredClone(state);
  try {
    await new AsyncFunction('tools', 'text', 'load', 'store', code)(
      tools, value => output.push(value), key => structuredClone(pending[key]),
      (key, value) => { if (value === undefined) delete pending[key]; else pending[key] = structuredClone(value); },
    );
    for (const key of Object.keys(state)) delete state[key];
    Object.assign(state, pending);
    return { ok: true, output };
  } catch (error) {
    return { ok: false, output, error };
  }
}

const selected = await run('01-select-fields.js');
assert.equal(selected.ok, true);
assert.deepEqual(selected.output[0].map(x => [x.name, x.hasTest]), [['root', true], ['api', false], ['web', true]]);
assert.ok(!JSON.stringify(selected.output).includes('unused'));
const partial = await run('02-partial-failure.js');
assert.equal(partial.ok, true);
assert.equal(partial.output[0][0].name, 'root');
assert.match(partial.output[0][1].error, /ENOENT/);
const shell = await run('03-check-exit-code.js');
assert.equal(shell.output[0].passed, false);
assert.equal(shell.ok, true); // Promise fulfilled，不等于 shell 成功。
await run('04-branch-state.js');
assert.equal(state.inspected, 1);
await run('04-branch-state.js');
assert.equal(state.inspected, 2);
const failed = await run('05-failed-state.js');
assert.equal(failed.ok, false);
assert.equal(state.inspected, 2); // 失败不提交 store。
assert.ok(writes['disposable.txt']); // 已完成外部副作用不回滚。
assert.equal(12 * 20000, 240000);
assert.equal(12 * 300, 3600);
console.log('PASS: 5 scripts; field filtering, partial failures, exit code, store commit, persistent side effects, illustrative arithmetic.');
console.log('Scope: Node + mock tools only; not a QuickJS, provider, MCP, cloud or security conformance test.');
