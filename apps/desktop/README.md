# Sports Event OS Desktop 0.1

macOS Apple Silicon，Tauri 2 + React + persistent frozen Python sidecar。中文 UI / 原名技术字段。仅合成数据。

## 从仓库构建

开发机需 macOS、Xcode Command Line Tools、Rust/Cargo、Node ≥22、pnpm 11，以及 Python 3.12。最终用户无需这些环境。

```bash
# repository root
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e . -r apps/desktop/requirements-build.txt
pnpm --dir apps/desktop install --frozen-lockfile
python apps/desktop/scripts/build_sidecar.py
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml
pnpm --dir apps/desktop tauri dev
# close dev, then build
pnpm --dir apps/desktop tauri build
```

生成 `apps/desktop/src-tauri/target/release/bundle/macos/Sports Event OS.app`。可复制到用户 Applications 文件夹；当前未 notarize，跨机器分发须遵循正常 macOS Gatekeeper 流程，不关闭系统保护。未验证 Intel / Windows / Linux。

## 回归

```bash
python -m unittest discover -s tests
pnpm --dir apps/desktop lint
pnpm --dir apps/desktop test
pnpm --dir apps/desktop exec playwright install chromium
pnpm --dir apps/desktop test:e2e
python apps/desktop/scripts/smoke_packaged.py \
  'apps/desktop/src-tauri/target/release/bundle/macos/Sports Event OS.app/Contents/MacOS/sports-os-sidecar'
```

E2E 在临时目录启动真实冻结 sidecar，仅适配原生文件选择和 Tauri IPC。测试使用合成事实，并执行 axe、键盘、三个窗口尺寸检查。打包 smoke 的子进程 PATH=/nonexistent，不依赖系统 Python。

开发 sidecar 路径目前面向 arm64；新增插件需重新冻结并重跑 Registry 测试。无运行时联网依赖；pnpm/Cargo/PyInstaller 仅构建时使用。

## 设计与行为依据

仓库根 `PRODUCT.md` / `DESIGN.md`；本目录 `design/` 保存研究、参考与一次集中审查。外部设计工具安装在项目 `.agents/skills`，不作为应用运行依赖打包或提交二进制。具体官方安装命令和 hook 信任步骤见 `design/TOOLCHAIN.md`。

功能说明、协议、边界与实测结果见根目录 `DESKTOP_USER_FLOW.md`、`DESKTOP_PROTOCOL.md`、`DESKTOP_ARCHITECTURE.md`、`DESKTOP_V0_1_TEST_REPORT.md`。
