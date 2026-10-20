const paths = ["package.json", "missing/package.json"];
const results = await Promise.allSettled(
  paths.map(async (path) => JSON.parse(await tools.read({ path })))
);
text(results.map((r, i) => r.status === "fulfilled"
  ? { path: paths[i], name: r.value.name }
  : { path: paths[i], error: String(r.reason) }
));
