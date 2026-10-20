const paths = ["package.json", "packages/api/package.json", "packages/web/package.json"];
const rows = await Promise.all(paths.map(async (path) => {
  const pkg = JSON.parse(await tools.read({ path }));
  return { path, name: pkg.name, hasTest: Boolean(pkg.scripts?.test) };
}));
text(rows);
