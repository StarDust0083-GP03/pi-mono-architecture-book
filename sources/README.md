# 本地源码副本

本目录保留可复核的资料，但不把四个完整源码树上传到电子书仓库。

- `pi-v1.4.0/`：本版端点，固定 `v1.4.0` 的 Git worktree。
- `pi-mono/`：上一版参照，仍固定 `v1.3.0`。
- `pi-v0.9.4/`：固定 `v0.9.4` 的 Git worktree。
- `pi-v0.99.2/`：固定 `v0.99.2` 的 Git worktree。
- `versions.json`：官方 release API 返回，以及标签对应的提交。
- `source-index.json`：29 条来源的固定版本链接。
- `*.txt`：完整文件级 diff 清单。

源码压缩包在 GitHub Release `book-v1.4.0` 的 `pi-mono-v1.4.0.zip` 附件中。四个检出点共享 Git 对象，不要单独删除其中一个目录里的 `.git` 文件。
