import { useCallback, useEffect, useRef, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { isTauri } from "@tauri-apps/api/core";
import {
  sportsOS,
  BackendError,
  Dict,
  Workspace,
  moduleName,
  display,
} from "./api";
import { Modal, Status, Empty, GateView } from "./components";
import { ModuleEditor } from "./Editor";

const errorLabels: Dict = {
  VALIDATION_BLOCK: "数据检查未通过",
  DEPENDENCY: "模块依赖冲突",
  APPROVAL: "未能记录批准",
  SNAPSHOT: "快照暂不可生成",
  PROTOCOL: "通信协议错误",
  SIDECAR: "后端连接中断",
  UNEXPECTED: "出现意外错误",
  PROJECT: "请先打开项目",
  CONFLICT: "工作区已在别处修改",
};
export default function App() {
  const [health, setHealth] = useState<Dict | null>(null),
    [state, setState] = useState<Workspace | null>(null),
    [page, setPage] = useState("Overview"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState<BackendError | null>(null),
    [notice, setNotice] = useState(""),
    [wizard, setWizard] = useState(false),
    [approval, setApproval] = useState<string | null>(null),
    [ref, setRef] = useState(""),
    [dirty, setDirty] = useState(false),
    [pending, setPending] = useState<(() => void) | null>(null),
    [collapsed, setCollapsed] = useState(false),
    [snapshot, setSnapshot] = useState<Dict | null>(null),
    [snapshots, setSnapshots] = useState<Dict[]>([]),
    [moduleView, setModuleView] = useState<{
      id: string;
      schema: Dict;
      data: Dict;
    } | null>(null),
    [result, setResult] = useState<Dict | null>(null),
    [diff, setDiff] = useState<Dict | null>(null),
    [old, setOld] = useState(""),
    [newVersion, setNewVersion] = useState("WORKING"),
    [ack, setAck] = useState(false);
  const [locateSource, setLocateSource] = useState("");
  useEffect(() => {
    if (!moduleView || !locateSource) return;
    const field = document.querySelector<HTMLElement>(
      `[aria-label="${CSS.escape(locateSource)}"]`,
    );
    if (field) {
      let ancestor = field.parentElement;
      while (ancestor) {
        if (ancestor instanceof HTMLDetailsElement) ancestor.open = true;
        ancestor = ancestor.parentElement;
      }
      field.scrollIntoView({ block: "center" });
      field.focus();
    }
    setLocateSource("");
  }, [moduleView, locateSource]);
  const [recent, setRecent] = useState<Dict[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("sports-os.recents") || "[]");
    } catch {
      return [];
    }
  });
  const run = useCallback(async (fn: () => Promise<any>) => {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      const err =
        e instanceof BackendError
          ? e
          : new BackendError("UNEXPECTED", String(e));
      setError(err);
      if (err.code === "SIDECAR") setHealth(null);
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);
  // Workspace to reopen after the sidecar restarts (everything is persisted, so nothing is lost).
  const lastWorkspace = useRef<string | null>(null);
  useEffect(() => {
    lastWorkspace.current = state?.workspace ?? null;
  }, [state?.workspace]);
  const connect = useCallback(
    () =>
      run(async () => {
        setHealth(await sportsOS.call("health"));
        setDirty(false);
        setSnapshot(null);
        setModuleView(null);
        const reopen = lastWorkspace.current;
        if (!reopen) {
          setState(null);
          return;
        }
        try {
          setState(
            await sportsOS.call<Workspace>("open_project", {
              workspace: reopen,
            }),
          );
          setNotice("后端已重新连接，项目已从磁盘重新打开。");
        } catch {
          setState(null);
        }
      }),
    [run],
  );
  useEffect(() => {
    void connect();
  }, [connect]);
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === "Tab") document.documentElement.dataset.input = "keyboard";
    };
    const pointer = () => {
      document.documentElement.dataset.input = "pointer";
    };
    window.addEventListener("keydown", key);
    window.addEventListener("pointerdown", pointer);
    return () => {
      window.removeEventListener("keydown", key);
      window.removeEventListener("pointerdown", pointer);
    };
  }, []);
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  useEffect(() => {
    if (!isTauri()) return;
    let disposed = false;
    let off: (() => void) | undefined;
    void getCurrentWindow()
      .onCloseRequested((e) => {
        if (dirty) {
          e.preventDefault();
          setPending(() => () => void getCurrentWindow().destroy());
        }
      })
      .then((unlisten) => {
        if (disposed) unlisten();
        else off = unlisten;
      });
    return () => {
      disposed = true;
      off?.();
    };
  }, [dirty]);
  const remember = (s: Workspace) => {
    const item = {
      ...s.project.manifest.project,
      path: s.workspace,
      modified: s.modified_at,
      quality: s.quality.status,
    };
    const list = [item, ...recent.filter((x) => x.path !== s.workspace)].slice(
      0,
      12,
    );
    setRecent(list);
    localStorage.setItem("sports-os.recents", JSON.stringify(list));
  };
  const adopt = (s: Workspace) => {
    setState(s);
    remember(s);
    setSnapshot(null);
    setDirty(false);
    setPage("Overview");
    setModuleView(null);
    setNotice("项目已打开 · SYNTHETIC");
  };
  const navigate = (next: () => void) => {
    if (dirty) setPending(() => next);
    else next();
  };
  const loadPage = (p: string) => {
    setPage(p);
    setModuleView(null);
    setResult(null);
    setDiff(null);
    if (p === "Snapshots" || p === "Versions")
      void run(async () => {
        const rows = await sportsOS.call("list_snapshots");
        setSnapshots(rows);
        setOld(rows[0]?.snapshot_id || "");
      });
    else if (p === "finance.revenue")
      void run(async () =>
        setResult(
          await sportsOS.call("calculate_module", {
            module_id: p,
            ...(snapshot ? { snapshot_id: snapshot.snapshot_id } : {}),
          }),
        ),
      );
    else if (p.includes("."))
      void run(async () => {
        const schema = await sportsOS.call("get_module_schema", {
          module_id: p,
        });
        const data = snapshot
          ? snapshot.project.modules[p].payload
          : await sportsOS.call("get_module_data", { module_id: p });
        setModuleView({ id: p, schema, data });
      });
  };
  const mutate = async (method: string, params: Dict = {}) => {
    const s = await sportsOS.call<Workspace>(method, params);
    setState(s);
    remember(s);
    if (moduleView && s.project.modules[moduleView.id])
      setModuleView({
        ...moduleView,
        data: s.project.modules[moduleView.id].payload,
      });
    setNotice(
      s.draft
        ? "已保存为未完成草稿：尚未通过检查，请前往 Quality Gate 修正。"
        : "已保存为工作态。",
    );
    return s;
  };
  const current = snapshot ? snapshot.project : state?.project;
  const meta = current?.manifest.project;
  const enabled = Object.keys(current?.manifest.modules || {}).filter(
    (k) => current?.manifest.modules[k],
  );
  const selectFolder = async () => {
    const path = await open({
      directory: true,
      multiple: false,
      title: "选择独立项目文件夹",
    });
    return typeof path === "string" ? path : null;
  };
  const openProject = (path?: string) =>
    void run(async () => {
      const chosen = path || (await selectFolder());
      if (chosen)
        adopt(await sportsOS.call("open_project", { workspace: chosen }));
    });
  const locate = (source: string) => {
    const id = enabled.find((k) => source.startsWith(k));
    if (!id) {
      setNotice("此 Finding 没有可可靠定位的字段，请依据 Source 检查。");
      return;
    }
    setLocateSource(source);
    setNotice(
      "已定位模块：" +
        id +
        "。Source：" +
        source +
        "；仅精确 schema 路径可聚焦字段。",
    );
    navigate(() => loadPage(id));
  };
  return (
    <div className={`app ${collapsed ? "collapsed" : ""}`}>
      <header className="app-bar">
        <button
          className="brand"
          onClick={() =>
            navigate(() => {
              setState(null);
              setSnapshot(null);
              setModuleView(null);
            })
          }
        >
          Sports Event OS
        </button>
        <span className="environment">SYNTHETIC / LOCAL</span>
        <span className="app-version">
          Desktop {health?.desktop_version ?? ""}
        </span>
      </header>
      {!health ? (
        <main className="startup">
          <h1>{busy ? "正在启动本地后端" : "后端不可用"}</h1>
          <p>计算、批准与数据写入仅由本地 Python Sidecar 执行。</p>
          {!busy && <button onClick={connect}>重新连接后端</button>}
        </main>
      ) : !state ? (
        <main className="home">
          <div className="page-heading">
            <div>
              <h1>项目 Projects</h1>
              <p className="muted">
                一个项目，一个文件夹。业务事实、批准与历史版本留在本机。
              </p>
            </div>
            <div className="actions">
              <button disabled={busy} onClick={() => openProject()}>
                打开项目
              </button>
              <button
                className="primary"
                disabled={busy}
                onClick={() => setWizard(true)}
              >
                新建项目
              </button>
            </div>
          </div>
          <div className="section-line">
            <h2>最近项目</h2>
            <button
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  const path = await selectFolder();
                  if (path)
                    adopt(
                      await sportsOS.call("create_demo", { workspace: path }),
                    );
                })
              }
            >
              在空目录创建演示项目
            </button>
          </div>
          {!recent.length ? (
            <Empty title="开始第一个赛事项目">
              新建空项目、选择模块组合，或创建完全虚构的 2027 演示项目。
            </Empty>
          ) : (
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="可横向滚动的数据表"
            >
              <table>
                <caption className="sr-only">最近项目列表</caption>
                <thead>
                  <tr>
                    <th>项目 / ID</th>
                    <th>状态</th>
                    <th>版本</th>
                    <th>最后修改</th>
                    <th>质量</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((p) => (
                    <tr key={p.path}>
                      <td>
                        <button
                          className="text-button"
                          onClick={() => openProject(p.path)}
                        >
                          {p.name}
                        </button>
                        <small>
                          {p.id} · {p.path}
                        </small>
                      </td>
                      <td>
                        <Status value={p.status} />
                      </td>
                      <td>
                        <code>{p.version}</code>
                      </td>
                      <td>{new Date(p.modified).toLocaleString()}</td>
                      <td>
                        <Status value={p.quality} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>
      ) : (
        <>
          <aside className="sidebar">
            <button
              aria-label="收起或展开导航"
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? "展开导航" : "收起导航"}
            </button>
            <div className="project-identity">
              <strong>{meta?.name}</strong>
              <code>{meta?.id}</code>
              <Status value={snapshot ? "READ ONLY" : meta?.status} />
            </div>
            <nav aria-label="项目导航">
              {["Overview", ...enabled]
                .filter(
                  (k) => !snapshot || !["Modules", "Quality Gate"].includes(k),
                )
                .map((p) => (
                  <button
                    aria-current={page === p ? "page" : undefined}
                    key={p}
                    onClick={() => navigate(() => loadPage(p))}
                  >
                    {(
                      {
                        Overview: "概览",
                        Modules: "能力模块",
                        "Quality Gate": "质量检查",
                        Versions: "版本比较",
                        Snapshots: "快照",
                      } as Dict
                    )[p] || moduleName(p)}
                  </button>
                ))}
            </nav>
            <nav className="utility-nav" aria-label="版本与质量导航">
              {["Modules", "Quality Gate", "Versions", "Snapshots"]
                .filter(
                  (k) => !snapshot || !["Modules", "Quality Gate"].includes(k),
                )
                .map((p) => (
                  <button
                    disabled={busy}
                    aria-current={page === p ? "page" : undefined}
                    key={p}
                    onClick={() => navigate(() => loadPage(p))}
                  >
                    {
                      {
                        Modules: "能力模块",
                        "Quality Gate": "质量检查",
                        Versions: "版本比较",
                        Snapshots: "快照",
                      }[p]
                    }
                  </button>
                ))}
            </nav>
            <div className="sidebar-footer">本机项目 · 无平台连接</div>
          </aside>
          <main className="workspace">
            <div className="workspace-bar">
              <div>
                <h1>
                  {(
                    {
                      Overview: "项目概览",
                      Modules: "能力模块",
                      "Quality Gate": "Quality Gate",
                      Versions: "版本比较",
                      Snapshots: "批准快照",
                    } as Dict
                  )[page] || moduleName(page)}
                </h1>
                <span className="muted">
                  {snapshot
                    ? "READ ONLY · " + snapshot.snapshot_id
                    : state.draft
                      ? "Working Copy · 未完成草稿"
                      : "Working Copy"}{" "}
                  · <code>{meta?.version}</code>
                </span>
                {!snapshot && state.draft && (
                  <p className="draft-banner" role="note">
                    当前工作副本是未完成草稿：命令行和桌面端看到的是同一份草稿，修正全部阻断后会自动保存为正式工作态。
                    <button
                      disabled={busy}
                      onClick={() => {
                        if (
                          window.confirm(
                            "放弃草稿中的全部修改，回到上次保存的工作态？此操作不可撤销。",
                          )
                        )
                          void run(() => mutate("discard_draft"));
                      }}
                    >
                      放弃草稿
                    </button>
                  </p>
                )}
              </div>
              <div className="actions">
                {snapshot ? (
                  <button
                    onClick={() => {
                      setSnapshot(null);
                      setPage("Overview");
                      setModuleView(null);
                    }}
                  >
                    返回工作副本
                  </button>
                ) : (
                  <>
                    <button
                      disabled={busy || dirty}
                      onClick={() => void run(() => mutate("save_project"))}
                    >
                      保存项目
                    </button>
                    <button
                      disabled={busy || dirty}
                      onClick={() =>
                        void run(async () => {
                          setState({
                            ...state,
                            quality: await sportsOS.call("validate_project"),
                          });
                          loadPage("Quality Gate");
                        })
                      }
                    >
                      检查
                    </button>
                    <button
                      disabled={busy || dirty}
                      onClick={() => {
                        setRef("");
                        setApproval("PROJECT");
                      }}
                    >
                      记录项目批准
                    </button>
                  </>
                )}
              </div>
            </div>
            {snapshot && (
              <div className="readonly-banner">
                READ ONLY · 冻结快照。任何工作态编辑都不会更改此版本。
              </div>
            )}
            {dirty && (
              <div className="draft-banner">
                存在尚未提交的编辑。提交将使相关模块及项目原批准失效。
              </div>
            )}
            {busy && (
              <div role="status" className="loading-line">
                正在处理，请稍候…
              </div>
            )}
            <div className="content">
              {page === "Overview" && (
                <>
                  <section className="overview-meta">
                    <h2>{meta?.name}</h2>
                    <dl>
                      <dt>项目 ID</dt>
                      <dd>
                        <code>{meta?.id}</code>
                      </dd>
                      <dt>版本</dt>
                      <dd>
                        <code>{meta?.version}</code>
                      </dd>
                      <dt>状态</dt>
                      <dd>
                        <Status value={meta?.status} />
                      </dd>
                      <dt>时区</dt>
                      <dd>{meta?.timezone}</dd>
                      <dt>项目目录</dt>
                      <dd>{state.workspace}</dd>
                    </dl>
                  </section>
                  <div className="section-line">
                    <h2>项目能力</h2>
                    <span>{enabled.length} 个启用模块</span>
                  </div>
                  <table>
                    <caption className="sr-only">启用模块状态</caption>
                    <thead>
                      <tr>
                        <th>模块</th>
                        <th>工作版本</th>
                        <th>批准状态</th>
                        <th>批准引用</th>
                      </tr>
                    </thead>
                    <tbody>
                      {enabled.map((id) => (
                        <tr key={id}>
                          <td>
                            <button
                              className="text-button"
                              onClick={() => loadPage(id)}
                            >
                              {moduleName(id)}
                            </button>
                            <small>{id}</small>
                          </td>
                          <td>
                            <code>{current?.modules[id]?.data_version}</code>
                          </td>
                          <td>
                            <Status
                              value={current?.modules[id]?.status || "DRAFT"}
                            />
                          </td>
                          <td>
                            {current?.modules[id]?.approval_ref || "尚未批准"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!enabled.length && (
                    <Empty title="尚未选择能力模块">
                      前往“能力模块”启用所需功能，不需要票务能力的赛事也可独立运行。
                    </Empty>
                  )}
                </>
              )}
              {page === "Modules" && (
                <>
                  <p className="muted">
                    启停由后端校验依赖；禁用保留数据，不会修改历史快照。
                  </p>
                  <ModuleList
                    modules={state.modules}
                    selected={enabled}
                    busy={busy}
                    onToggle={(id) =>
                      void run(() =>
                        mutate(
                          enabled.includes(id)
                            ? "disable_module"
                            : "enable_module",
                          { module_id: id },
                        ),
                      )
                    }
                  />
                </>
              )}
              {moduleView && page === moduleView.id && (
                <>
                  <div className="section-line">
                    <code>{moduleView.id}</code>
                    <Status value={current?.modules[page]?.status || "DRAFT"} />
                    <code>{current?.modules[page]?.data_version}</code>
                    {!snapshot && (
                      <button
                        disabled={busy || dirty}
                        onClick={() => {
                          setRef("");
                          setApproval(page);
                        }}
                      >
                        记录模块批准
                      </button>
                    )}
                  </div>
                  <ModuleEditor
                    key={moduleView.id + (snapshot?.snapshot_id || "working")}
                    id={moduleView.id}
                    schema={moduleView.schema}
                    data={moduleView.data}
                    readOnly={!!snapshot}
                    onDirty={setDirty}
                    onSubmit={async (payload) => {
                      const s = await run(() =>
                        mutate("update_module_data", {
                          module_id: page,
                          payload,
                        }),
                      );
                      if (s) {
                        setModuleView({
                          ...moduleView,
                          data: s.project.modules[page].payload,
                        });
                        setDirty(false);
                      }
                    }}
                  />
                </>
              )}
              {page === "Quality Gate" && (
                <GateView gate={state.quality} onLocate={locate} />
              )}
              {page === "finance.revenue" &&
                (result ? (
                  <Revenue result={result} />
                ) : (
                  <Empty title="收入结果暂不可用">
                    请先处理 Quality Gate
                    中的阻断项；界面不会使用旧数据伪装本次结果。
                  </Empty>
                ))}
              {page === "Snapshots" && (
                <>
                  <div className="section-line">
                    <h2>冻结当前工作版本</h2>
                    {!snapshot && (
                      <>
                        <Status value={state.release_quality.status} />
                        <label>
                          <input
                            type="checkbox"
                            checked={ack}
                            onChange={(e) => setAck(e.target.checked)}
                          />
                          已阅读并确认警告
                        </label>
                        <button
                          className="primary"
                          disabled={
                            busy ||
                            dirty ||
                            state.release_quality.status === "BLOCK" ||
                            (state.release_quality.status === "WARNING" && !ack)
                          }
                          onClick={() =>
                            void run(async () => {
                              await sportsOS.call("create_snapshot", {
                                ack_warnings: ack,
                              });
                              setSnapshots(
                                await sportsOS.call("list_snapshots"),
                              );
                              setNotice("快照及发布件已生成，历史数据只读。");
                            })
                          }
                        >
                          冻结 Snapshot
                        </button>
                      </>
                    )}
                  </div>
                  {state.release_quality.status === "BLOCK" && !snapshot && (
                    <p className="muted">
                      发布存在阻断或未批准模块。先检查、记录人工批准，再冻结。
                    </p>
                  )}
                  {!snapshots.length ? (
                    <Empty title="尚无快照">
                      当前工作副本通过发布门禁并完成批准后，可生成第一个不可变版本。
                    </Empty>
                  ) : (
                    <table>
                      <caption className="sr-only">快照列表</caption>
                      <thead>
                        <tr>
                          <th>Snapshot ID</th>
                          <th>创建时间</th>
                          <th>项目版本</th>
                          <th>质量</th>
                        </tr>
                      </thead>
                      <tbody>
                        {snapshots.map((s) => (
                          <tr key={s.snapshot_id}>
                            <td>
                              <button
                                className="text-button"
                                onClick={() =>
                                  void run(async () => {
                                    setSnapshot(
                                      await sportsOS.call("get_snapshot", {
                                        snapshot_id: s.snapshot_id,
                                      }),
                                    );
                                    setPage("Overview");
                                  })
                                }
                              >
                                {s.snapshot_id}
                              </button>
                            </td>
                            <td>{s.created_at}</td>
                            <td>{s.project.manifest.project.version}</td>
                            <td>
                              <Status value={s.quality_gate.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </>
              )}
              {page === "Versions" && (
                <>
                  <div className="compare-controls">
                    <label>
                      旧版本
                      <select
                        value={old}
                        onChange={(e) => setOld(e.target.value)}
                      >
                        <option value="">选择快照</option>
                        {snapshots.map((s) => (
                          <option key={s.snapshot_id}>{s.snapshot_id}</option>
                        ))}
                      </select>
                    </label>
                    <span>→</span>
                    <label>
                      新版本
                      <select
                        value={newVersion}
                        onChange={(e) => setNewVersion(e.target.value)}
                      >
                        <option value="WORKING">当前工作副本</option>
                        {snapshots.map((s) => (
                          <option key={s.snapshot_id}>{s.snapshot_id}</option>
                        ))}
                      </select>
                    </label>
                    <button
                      disabled={!old || busy}
                      onClick={() =>
                        void run(async () =>
                          setDiff(
                            await sportsOS.call("compare_versions", {
                              old,
                              new: newVersion,
                            }),
                          ),
                        )
                      }
                    >
                      比较版本
                    </button>
                  </div>
                  {diff ? (
                    <DiffView diff={diff} />
                  ) : (
                    <Empty title="选择两个版本进行比较">
                      支持快照与工作副本、快照与快照；原因由后端证据提供，不做推测补全。
                    </Empty>
                  )}
                </>
              )}
            </div>
          </main>
        </>
      )}
      <footer className="statusbar">
        <span role="status">
          {notice || "离线 / 合成数据"}
          {busy ? " · 正在处理" : ""}
        </span>
      </footer>
      {error && !wizard && !approval && (
        <div className="error-panel" role="alert">
          <strong>{errorLabels[error.code] || error.code}</strong>
          <p>{error.message}</p>
          <details>
            <summary>Technical Details</summary>
            <pre>{display(error.details)}</pre>
          </details>
          {error.code === "CONFLICT" && state && (
            <button
              className="primary"
              onClick={() => {
                const path = state.workspace;
                setError(null);
                openProject(path);
              }}
            >
              重新打开项目（放弃本窗口未保存的修改）
            </button>
          )}
          <button onClick={() => setError(null)}>关闭错误提示</button>
        </div>
      )}
      <Modal title="新建项目" open={wizard} onClose={() => setWizard(false)}>
        {error && <ErrorNotice error={error} onClose={() => setError(null)} />}
        {health && (
          <Wizard
            modules={health.modules}
            profiles={health.profiles}
            busy={busy}
            onCreate={async (values) => {
              const s = await run(async () => {
                const path = await selectFolder();
                if (!path) return;
                return sportsOS.call<Workspace>("create_project", {
                  workspace: path,
                  ...values,
                });
              });
              if (s) {
                adopt(s);
                setWizard(false);
              }
            }}
          />
        )}
      </Modal>
      <Modal
        title={approval === "PROJECT" ? "记录项目批准" : "记录模块批准"}
        open={!!approval}
        onClose={() => setApproval(null)}
      >
        {error && <ErrorNotice error={error} onClose={() => setError(null)} />}
        <p>
          此操作只记录在软件之外已发生的人工批准。软件不会替你批准业务决定。
        </p>
        <p>
          当前版本：
          <code>
            {approval === "PROJECT"
              ? state?.project.manifest.project.version
              : state?.project.modules[approval || ""]?.data_version}
          </code>
        </p>
        <label className="field">
          批准引用 Approval Reference
          <input
            autoFocus
            value={ref}
            onChange={(e) => setRef(e.target.value)}
          />
        </label>
        <button
          className="primary"
          disabled={!ref.trim() || busy}
          onClick={() =>
            void run(async () => {
              await mutate(
                approval === "PROJECT" ? "approve_project" : "approve_module",
                approval === "PROJECT"
                  ? {
                      approval_ref: ref,
                      version: state?.project.manifest.project.version,
                    }
                  : {
                      module_id: approval,
                      approval_ref: ref,
                      data_version:
                        state?.project.modules[approval || ""]?.data_version,
                    },
              );
              setApproval(null);
            })
          }
        >
          记录人工批准
        </button>
      </Modal>
      <Modal
        title="尚未提交的编辑"
        open={!!pending}
        onClose={() => setPending(null)}
      >
        <p>离开将丢弃当前界面草稿。已经提交给后端的数据不受影响。</p>
        <button onClick={() => setPending(null)}>继续编辑</button>
        <button
          onClick={() => {
            setDirty(false);
            const action = pending;
            setPending(null);
            action?.();
          }}
        >
          丢弃界面草稿并离开
        </button>
      </Modal>
    </div>
  );
}
const moduleCategory = (id: string) =>
  [
    "ticketing.refund",
    "ticketing.identity",
    "ticketing.transfer",
    "ticketing.launch",
    "ticketing.rights_return",
  ].includes(id)
    ? "Rules"
    : {
        core: "Core",
        quality: "Core",
        ticketing: "Ticketing",
        product: "Product",
        finance: "Finance",
        demand: "Finance",
        project: "Project",
      }[id.split(".")[0]] || "Other";
function ModuleList({
  modules,
  selected,
  onToggle,
  busy,
}: {
  modules: Dict[];
  selected: string[];
  onToggle: (id: string) => void;
  busy: boolean;
}) {
  return (
    <table>
      <caption className="sr-only">模块选择及依赖</caption>
      <thead>
        <tr>
          <th>启用</th>
          <th>模块 / 分类</th>
          <th>Requires</th>
          <th>Provides</th>
        </tr>
      </thead>
      <tbody>
        {modules.map((m) => (
          <tr key={m.module_id}>
            <td>
              <input
                type="checkbox"
                aria-label={`启用 ${m.module_id}`}
                checked={selected.includes(m.module_id)}
                disabled={busy}
                onChange={() => onToggle(m.module_id)}
              />
            </td>
            <td>
              {moduleName(m.module_id)}
              <small>
                {m.module_id} · {moduleCategory(m.module_id)}
              </small>
              <small>
                维护 {moduleName(m.module_id)} 数据；能力：
                {m.provides.join(", ") || "结构化规则 / 质量检查"}
              </small>
            </td>
            <td>
              {[...m.dependencies, ...m.requires_capabilities].join(", ") ||
                "—"}
            </td>
            <td>{m.provides.join(", ") || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
function Wizard({
  modules,
  profiles,
  busy,
  onCreate,
}: {
  modules: Dict[];
  profiles: Dict;
  busy: boolean;
  onCreate: (p: Dict) => void;
}) {
  const [step, setStep] = useState(1),
    [identity, setIdentity] = useState({
      id: "",
      name: "",
      timezone: "Asia/Singapore",
    }),
    [profile, setProfile] = useState(""),
    [selected, setSelected] = useState<string[]>([]);
  return (
    <div className="wizard">
      <p className="step-label">
        {step} / 3 · {["项目身份", "选择预设", "能力模块"][step - 1]}
      </p>
      {step === 1 ? (
        <>
          {(["name", "id", "timezone"] as const).map((k) => (
            <label className="field" key={k}>
              {
                { name: "项目名称", id: "项目 ID", timezone: "时区 Timezone" }[
                  k
                ]
              }
              <input
                value={identity[k]}
                onChange={(e) =>
                  setIdentity({ ...identity, [k]: e.target.value })
                }
              />
            </label>
          ))}
          <p className="muted">仅合成项目，不录入真实公司或个人数据。</p>
        </>
      ) : step === 2 ? (
        <fieldset>
          <legend>预设仅填写模块清单，可以继续调整</legend>
          {["", ...Object.keys(profiles)].map((k) => (
            <label className="profile-choice" key={k}>
              <input
                type="radio"
                name="profile"
                checked={profile === k}
                onChange={() => {
                  setProfile(k);
                  setSelected(profiles[k] || []);
                }}
              />
              {
                (
                  {
                    "": "Blank · 空项目",
                    "non-ticketed-event": "Non-ticketed Event · 非票务赛事",
                    "ticketed-indoor-event": "Ticketed Indoor Event · 室内票务",
                    "multi-session-tournament":
                      "Multi-session Tournament · 多场次",
                  } as Dict
                )[k]
              }
            </label>
          ))}
        </fieldset>
      ) : (
        <div className="wizard-modules">
          <ModuleList
            modules={modules}
            selected={selected}
            busy={busy}
            onToggle={(id) =>
              setSelected(
                selected.includes(id)
                  ? selected.filter((k) => k !== id)
                  : [...selected, id],
              )
            }
          />
        </div>
      )}
      <div className="dialog-actions">
        {step > 1 && <button onClick={() => setStep(step - 1)}>上一步</button>}
        {step < 3 ? (
          <button
            className="primary"
            disabled={Object.values(identity).some((v) => !v.trim())}
            onClick={() => setStep(step + 1)}
          >
            下一步
          </button>
        ) : (
          <button
            className="primary"
            disabled={busy}
            onClick={() => onCreate({ identity, modules: selected })}
          >
            选择文件夹并创建
          </button>
        )}
      </div>
    </div>
  );
}
function Revenue({ result }: { result: Dict }) {
  const [group, setGroup] = useState("by_stage");
  const totals = result.totals;
  return (
    <section>
      <div className="revenue-total">
        <span>满售容量收入 Full Revenue</span>
        <strong>{display(totals.full_revenue)}</strong>
        <small>{result.unit} · 后端精确值 · READ ONLY</small>
      </div>
      <table>
        <caption>需求情景 / 票张与计费口径</caption>
        <thead>
          <tr>
            <th>情景</th>
            <th>收入</th>
            <th>Public Revenue</th>
            <th>Rights Revenue</th>
            <th>Public Expected Tickets</th>
            <th>Rights Allocated</th>
            <th>Rights Expected Fulfilled</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(totals.scenarios).map(([name, s]: [string, any]) => (
            <tr key={name}>
              <th>{name}</th>
              {[
                "revenue",
                "public_revenue",
                "rights_revenue",
                "public_expected_tickets",
                "rights_allocated",
                "rights_expected_fulfilled",
              ].map((k) => (
                <td className="number" key={k}>
                  {display(s[k])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="section-line">
        <label>
          分组查看
          <select value={group} onChange={(e) => setGroup(e.target.value)}>
            <option value="by_stage">阶段 By Stage</option>
            <option value="by_tier">票档 By Tier</option>
            <option value="by_session">场次 By Session</option>
          </select>
        </label>
      </div>
      <table>
        <caption>分组收入</caption>
        <thead>
          <tr>
            <th>分组</th>
            <th>满售收入</th>
            {Object.keys(totals.scenarios).map((k) => (
              <th key={k}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Object.entries(result[group]).map(([k, r]: [string, any]) => (
            <tr key={k}>
              <th>{k}</th>
              <td className="number">{display(r.full_revenue)}</td>
              {Object.keys(totals.scenarios).map((n) => (
                <td className="number" key={n}>
                  {display(r.scenarios[n].revenue)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <details>
        <summary>敏感性与口径说明</summary>
        <pre>{JSON.stringify(result.sensitivity, null, 2)}</pre>
        {result.notes.map((n: string) => (
          <p key={n}>{n}</p>
        ))}
      </details>
    </section>
  );
}
function DiffView({ diff }: { diff: Dict }) {
  const entries = Object.entries(diff.business || {});
  return (
    <section>
      {!entries.length && (
        <Empty title="没有业务事实变化">
          元数据或快照标识仍可能不同，详见下方后端记录。
        </Empty>
      )}
      {entries.map(([id, rows]: [string, any]) => (
        <section key={id}>
          <h2>{moduleName(id)}</h2>
          <table>
            <caption className="sr-only">{id} 版本差异</caption>
            <thead>
              <tr>
                <th>字段 / 事实类型</th>
                <th>Old → New</th>
                <th>原因证据</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r: any, i: number) => (
                <tr key={i}>
                  <td>
                    <code>{r.path}</code>
                    <small>{r.fact_kind}</small>
                  </td>
                  <td>
                    {display(r.old)} → {display(r.new)}
                  </td>
                  <td>
                    {r.reasons?.length
                      ? r.reasons.map((x: any, j: number) => (
                          <p key={j}>{display(x)}</p>
                        ))
                      : "No Evidence · 无直接证据"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      <details>
        <summary>完整后端差异记录（含模块启停与元数据）</summary>
        <pre>{JSON.stringify(diff, null, 2)}</pre>
      </details>
    </section>
  );
}

function ErrorNotice({
  error,
  onClose,
}: {
  error: BackendError;
  onClose: () => void;
}) {
  return (
    <section role="alert">
      <strong>{errorLabels[error.code] || error.code}</strong>
      <p>{error.message}</p>
      <details>
        <summary>Technical Details</summary>
        <pre>{display(error.details)}</pre>
      </details>
      <button onClick={onClose}>关闭错误提示</button>
    </section>
  );
}
