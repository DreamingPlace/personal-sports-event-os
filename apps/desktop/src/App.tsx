import { useState } from "react";
import { open, save } from "@tauri-apps/plugin-dialog";
import { call, type Dict, type State } from "./api";
import { SetupPage } from "./pages/SetupPage";
import { PricesPage } from "./pages/PricesPage";
import { SplitPage } from "./pages/SplitPage";
import { InventoryPage } from "./pages/InventoryPage";
import { ForecastPage } from "./pages/ForecastPage";
import { VersionsPage } from "./pages/VersionsPage";
import { DamaiPage } from "./pages/DamaiPage";
import { LivePage } from "./pages/LivePage";

export type PageProps = {
  state: State;
  /** Apply edit operations to the book; the new state comes back from the sidecar. */
  edit: (ops: Dict[], note?: string) => Promise<void>;
  /** Any other sidecar call that returns a new state. */
  run: (method: string, params?: Dict) => Promise<any>;
};

const PAGES = [
  { id: "setup", name: "赛事与场次", Page: SetupPage },
  { id: "prices", name: "票价与座席", Page: PricesPage },
  { id: "split", name: "座位分配", Page: SplitPage },
  { id: "inventory", name: "库存", Page: InventoryPage },
  { id: "forecast", name: "票房测算", Page: ForecastPage },
  { id: "damai", name: "大麦销售", Page: DamaiPage },
  { id: "live", name: "现场入场", Page: LivePage },
  { id: "versions", name: "版本", Page: VersionsPage },
] as const;

const FILTERS = [{ name: "票务总表", extensions: ["ticketbook"] }];

export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [page, setPage] = useState<string>("setup");
  const [error, setError] = useState<string>("");
  const [busy, setBusy] = useState(false);
  // Bumped when a call fails, to redraw the page so refused input goes back to the saved value.
  const [failures, setFailures] = useState(0);

  const guard = async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
    setBusy(true);
    setError("");
    try {
      return await fn();
    } catch (e: any) {
      setError(e?.message || String(e));
      setFailures((n) => n + 1);
      return undefined;
    } finally {
      setBusy(false);
    }
  };

  const run = async (method: string, params: Dict = {}) =>
    guard(async () => {
      const result = await call(method, params);
      if (result && result.book) setState(result as State);
      return result;
    });
  const edit = async (ops: Dict[], note = "") => {
    await run("edit", { ops, note });
  };

  if (!state) return <Start run={run} error={error} busy={busy} />;

  const current = PAGES.find((p) => p.id === page) || PAGES[0];
  const problems = state.ledger.problems as Dict[];
  const errors = problems.filter((p) => p.level === "error").length;
  return (
    <div className="shell">
      <nav className="sidebar" aria-label="页面">
        <div className="brand">
          <strong>{state.book.event.name || "未命名赛事"}</strong>
          <span>{state.book.event.year || ""}</span>
        </div>
        {PAGES.map((p) => (
          <button key={p.id} className={p.id === page ? "nav selected" : "nav"} aria-current={p.id === page ? "page" : undefined} onClick={() => setPage(p.id)}>
            {p.name}
          </button>
        ))}
        <div className="sidebar-foot">
          <span className={errors ? "badge error" : problems.length ? "badge warning" : "badge ok"}>
            {errors ? `${errors} 个错误` : problems.length ? `${problems.length} 个提醒` : "没有问题"}
          </span>
          <span className="file" title={state.path}>
            🔒 {state.path.split(/[\\/]/).pop()}
          </span>
          <button onClick={() => run("close").then(() => setState(null))}>关闭文件</button>
        </div>
      </nav>
      <main className="main">
        {error && (
          <div className="error-bar" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="关闭提示">
              ×
            </button>
          </div>
        )}
        <current.Page key={page === "forecast" || page === "damai" ? page : `${page}-${failures}`} state={state} edit={edit} run={run} />
      </main>
      {busy && <div className="busy" aria-live="polite">处理中…</div>}
    </div>
  );
}

function Start({ run, error, busy }: { run: (m: string, p?: Dict) => Promise<any>; error: string; busy: boolean }) {
  const [mode, setMode] = useState<"new" | "open" | "example" | null>(null);
  const [path, setPath] = useState("");
  const [name, setName] = useState("");
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [local, setLocal] = useState("");

  const choose = async () => {
    const picked = mode === "open" ? await open({ multiple: false, filters: FILTERS }) : await save({ filters: FILTERS, defaultPath: (name || "赛事") + ".ticketbook" });
    if (typeof picked === "string") setPath(picked);
  };
  const submit = async () => {
    setLocal("");
    if (!path) return setLocal("请选择文件位置");
    if (!pw) return setLocal("请输入密码");
    if (mode === "open") return run("open_book", { path, password: pw });
    if (pw !== pw2) return setLocal("两次输入的密码不一致");
    return run("create_book", { path, password: pw, name, year: Number(year) || null, example: mode === "example" });
  };

  return (
    <div className="start">
      <h1>票务总表</h1>
      <p className="hint">一届赛事一个文件。文件加密保存在你的电脑上，不会上传。</p>
      {!mode && (
        <div className="start-choices">
          <button className="primary" onClick={() => setMode("new")}>
            新建赛事
          </button>
          <button onClick={() => setMode("open")}>打开已有文件</button>
          <button onClick={() => setMode("example")}>用示例数据试用</button>
        </div>
      )}
      {mode && (
        <form
          className="start-form"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <h2>{mode === "open" ? "打开文件" : mode === "example" ? "示例数据（虚构）" : "新建赛事"}</h2>
          {mode === "new" && (
            <>
              <label>
                赛事名称
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label>
                年份
                <input value={year} onChange={(e) => setYear(e.target.value)} inputMode="numeric" />
              </label>
            </>
          )}
          <label>
            文件
            <span className="row">
              <input value={path} readOnly placeholder="未选择" aria-label="文件位置" />
              <button type="button" onClick={choose}>
                {mode === "open" ? "选择文件" : "选择保存位置"}
              </button>
            </span>
          </label>
          <label>
            密码
            <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete={mode === "open" ? "current-password" : "new-password"} />
          </label>
          {mode !== "open" && (
            <label>
              再输入一次密码
              <input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} autoComplete="new-password" />
            </label>
          )}
          {mode !== "open" && <p className="hint">忘记密码就无法打开文件，请记好。</p>}
          {(local || error) && (
            <p className="form-error" role="alert">
              {local || error}
            </p>
          )}
          <div className="row">
            <button type="button" onClick={() => setMode(null)}>
              返回
            </button>
            <button className="primary" type="submit" disabled={busy}>
              {mode === "open" ? "打开" : "创建"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
