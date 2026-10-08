import { useEffect, useMemo, useState } from "react";
import { save } from "@tauri-apps/plugin-dialog";
import type { Change, Dict } from "../api";
import { bandName, call, yuan } from "../api";
import type { PageProps } from "../App";
import { Cell, Confirm, Section } from "../ui";

const key = (path: (string | number)[]) => JSON.stringify(path);

/** Read a value from the book by the same path format the backend uses (list items by code/id). */
function read(book: Dict, path: (string | number)[]): any {
  let node: any = book;
  for (const p of path) {
    if (Array.isArray(node)) node = node.find((i) => (i.code ?? i.id) === p);
    else node = node?.[p];
    if (node === undefined || node === null) return undefined;
  }
  return node;
}

export function ForecastPage({ state, run }: PageProps) {
  const { book } = state;
  const [changes, setChanges] = useState<Record<string, Change>>({});
  const [preview, setPreview] = useState<Dict | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [scenarioName, setScenarioName] = useState("");
  const list = useMemo(() => Object.values(changes), [changes]);

  // Live preview: recompute on a copy whenever the draft changes. The book is never touched here.
  useEffect(() => {
    let alive = true;
    const t = setTimeout(async () => {
      try {
        const result = await call("forecast_preview", { changes: list });
        if (alive) {
          setPreview(result);
          setPreviewError("");
        }
      } catch (e: any) {
        if (alive) setPreviewError(e?.message || String(e));
      }
    }, 250);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [list, state]);

  const value = (path: (string | number)[]) => (key(path) in changes ? changes[key(path)].value : read(book, path));
  const change = (path: (string | number)[], v: any) =>
    setChanges((c) => {
      const next = { ...c };
      const original = read(book, path);
      if (String(original ?? "") === String(v ?? "")) delete next[key(path)];
      else next[key(path)] = { path, value: v };
      return next;
    });
  const changed = (path: (string | number)[]) => key(path) in changes;
  const input = (path: (string | number)[], label: string, width = 80, asNumber = false, placeholder?: string) => (
    <span className={changed(path) ? "changed" : undefined}>
      <Cell label={label} type="number" value={value(path)} width={width} placeholder={placeholder} onCommit={(v) => change(path, v === "" ? null : asNumber ? v.trim() : v)} />
    </span>
  );

  // A view-blocked tier without its own price follows its base tier (shown grey), using the draft base price.
  const derived = (band: string, t: Dict) => {
    if (!t.blocked_of) return undefined;
    const base = value(["prices", band, t.blocked_of]);
    return base === undefined || base === null || base === "" ? undefined : String(Number(base) - Number(t.blocked_discount || 0));
  };
  const before = preview?.before;
  const after = preview?.after;
  const fc = book.forecast;

  return (
    <div className="page forecast">
      <div className="forecast-totals" aria-live="polite">
        <Total label="预计总票房" before={before?.gross} after={after?.gross} />
        <Total label="代理费" before={before?.agent_fee} after={after?.agent_fee} />
        <Total label="净票房" before={before?.net} after={after?.net} />
        <Total label="满座票房" before={before?.full_value} after={after?.full_value} />
        <div className="forecast-actions">
          <span className="muted">{list.length ? `${list.length} 项修改（未写回）` : "没有修改"}</span>
          <button disabled={!list.length} onClick={() => setChanges({})}>
            放弃修改
          </button>
          <button className="primary" disabled={!list.length || !!previewError} onClick={() => setConfirming(true)}>
            确认写回…
          </button>
        </div>
      </div>
      {previewError && (
        <p className="form-error" role="alert">
          {previewError}
        </p>
      )}
      <p className="hint">这里的修改只是预览，原数据不变；按“确认写回”并确认后才会改到票务总表里（写回前自动保存一个版本）。</p>

      <Section title="上座率">
        <div className="row">
          <label>
            测算方式{" "}
            <select aria-label="测算方式" value={value(["forecast", "method"])} onChange={(e) => change(["forecast", "method"], e.target.value)}>
              <option value="band">按比赛阶段</option>
              <option value="china">按是否有中国队</option>
            </select>
          </label>
          <label>
            代理费 % {input(["event", "agent_fee_pct"], "代理费百分比", 70)}
          </label>
          <label>
            通票/套票售出率 % {input(["forecast", "product_fill"], "通票售出率", 70)}
          </label>
        </div>
        {value(["forecast", "method"]) === "china" ? (
          <div className="row">
            <label>有中国队场次 % {input(["forecast", "china_fill"], "有中国队上座率", 70)}</label>
            <label>其他场次 % {input(["forecast", "other_fill"], "其他场次上座率", 70)}</label>
          </div>
        ) : (
          <div className="row">
            {book.bands.map((b: Dict) => (
              <label key={b.code}>
                {b.name} % {input(["forecast", "band_fill", b.code], `上座率 ${b.name}`, 70)}
              </label>
            ))}
          </div>
        )}
        <details>
          <summary>单独设置某些场次的上座率</summary>
          <div className="row wrap">
            {book.sessions.map((s: Dict) => (
              <label key={s.code}>
                {s.code} {input(["forecast", "session_fill", s.code], `上座率 ${s.code}`, 60)}
              </label>
            ))}
          </div>
        </details>
        {fc.scenarios?.length > 0 && <p className="hint">已保存的方案在页面底部。</p>}
      </Section>

      <Section title="票价">
        <table className="grid">
          <thead>
            <tr>
              <th>比赛阶段</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {book.bands.map((b: Dict) => (
              <tr key={b.code}>
                <th scope="row">{b.name}</th>
                {book.tiers.map((t: Dict) => (
                  <td key={t.code}>{input(["prices", b.code, t.code], `测算票价 ${b.name} ${t.name}`, 80, false, derived(b.code, t))}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="座席">
        <table className="grid">
          <thead>
            <tr>
              <th>布局</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {book.layouts.map((l: Dict) => (
              <tr key={l.code}>
                <th scope="row">{l.name}</th>
                {book.tiers.map((t: Dict) => (
                  <td key={t.code}>{input(["layouts", l.code, "seats", t.code], `测算座席 ${l.name} ${t.name}`, 80, true)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {book.products.length > 0 && (
          <div className="row wrap">
            {book.products.map((p: Dict) => (
              <label key={p.id}>
                {p.name} 数量 {input(["products", p.id, "quota"], `测算数量 ${p.name}`, 70, true)}
              </label>
            ))}
          </div>
        )}
      </Section>

      <Section
        title="每场预计票房"
        actions={
          <button
            onClick={async () => {
              const path = await save({ filters: [{ name: "Excel", extensions: ["xlsx"] }], defaultPath: "票房测算.xlsx" });
              if (typeof path === "string") await run("export_forecast", { path });
            }}
          >
            导出当前测算（Excel）
          </button>
        }
      >
        {after && before && (
          <table className="grid numbers">
            <thead>
              <tr>
                <th>场次</th>
                <th>日期</th>
                <th>比赛阶段</th>
                <th>上座率</th>
                <th>现在</th>
                <th>修改后</th>
                <th>差额</th>
              </tr>
            </thead>
            <tbody>
              {after.sessions.map((s: Dict, i: number) => {
                const old = before.sessions[i];
                const diff = Number(s.expected) - Number(old?.expected || 0);
                return (
                  <tr key={s.code}>
                    <th scope="row">{s.code}</th>
                    <td>{s.date}</td>
                    <td>
                      {bandName(book, s.band)}
                      {s.china ? " · 中国队" : ""}
                    </td>
                    <td>{s.fill}%</td>
                    <td>{yuan(old?.expected)}</td>
                    <td>{yuan(s.expected)}</td>
                    <td className={diff < 0 ? "neg" : diff > 0 ? "pos" : undefined}>{diff ? yuan(diff.toFixed(2)) : "—"}</td>
                  </tr>
                );
              })}
              {after.products.map((p: Dict, i: number) => (
                <tr key={p.id}>
                  <th scope="row" colSpan={4}>
                    {p.name}
                  </th>
                  <td>{yuan(before.products[i]?.expected)}</td>
                  <td>{yuan(p.expected)}</td>
                  <td>{Number(p.expected) - Number(before.products[i]?.expected || 0) ? yuan((Number(p.expected) - Number(before.products[i]?.expected || 0)).toFixed(2)) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      <Section title="测算方案" hint="把当前这组修改存成方案（例如“预算第8版”），以后可以再载入比较。保存方案不会改动票务总表。">
        <div className="row">
          <input aria-label="方案名称" placeholder="方案名称" value={scenarioName} onChange={(e) => setScenarioName(e.target.value)} />
          <button disabled={!scenarioName.trim()} onClick={() => run("forecast_save_scenario", { name: scenarioName.trim(), changes: list }).then(() => setScenarioName(""))}>
            保存为方案
          </button>
        </div>
        <ul className="plain">
          {(fc.scenarios || []).map((s: Dict) => (
            <li key={s.name}>
              <strong>{s.name}</strong> <span className="muted">{s.changes.length} 项修改</span>{" "}
              <button className="link" onClick={() => setChanges(Object.fromEntries(s.changes.map((c: Change) => [key(c.path), c])))}>
                载入
              </button>
              <button className="link danger" onClick={() => run("forecast_delete_scenario", { name: s.name })}>
                删除
              </button>
            </li>
          ))}
        </ul>
      </Section>

      {confirming && preview && (
        <Confirm
          title="确认写回票务总表"
          confirmText="确认写回"
          onCancel={() => setConfirming(false)}
          onConfirm={async () => {
            const result = await run("forecast_apply", { changes: list, confirm: true });
            setConfirming(false);
            if (result) setChanges({});
          }}
        >
          <p>以下数值将被修改（写回前会自动保存一个版本，可随时恢复）：</p>
          <table className="grid">
            <thead>
              <tr>
                <th>项目</th>
                <th>原来</th>
                <th>改为</th>
              </tr>
            </thead>
            <tbody>
              {preview.changes.map((c: Dict) => (
                <tr key={key(c.path)}>
                  <td>{describe(book, c.path)}</td>
                  <td>{c.old ?? "—"}</td>
                  <td>{c.new ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>
            预计总票房：{yuan(before?.gross)} → <strong>{yuan(after?.gross)}</strong>
          </p>
        </Confirm>
      )}
    </div>
  );
}

function Total({ label, before, after }: { label: string; before?: string; after?: string }) {
  const diff = Number(after || 0) - Number(before || 0);
  return (
    <div className="total-tile">
      <span>{label}</span>
      <strong>{yuan(after)}</strong>
      {diff !== 0 && <small className={diff < 0 ? "neg" : "pos"}>{(diff > 0 ? "+" : "") + yuan(diff.toFixed(2))}</small>}
    </div>
  );
}

const NAMES: Record<string, string> = { prices: "票价", layouts: "座席", products: "数量", event: "", forecast: "上座率" };
const FIELD: Record<string, string> = { agent_fee_pct: "代理费 %", china_fill: "有中国队场次 %", other_fill: "其他场次 %", product_fill: "通票售出率 %", method: "测算方式" };

export function describe(book: Dict, path: (string | number)[]): string {
  const [head, ...rest] = path.map(String);
  const nameOf = (list: string, code: string) => book[list]?.find((i: Dict) => (i.code ?? i.id) === code)?.name || code;
  if (head === "prices") return `票价 ${nameOf("bands", rest[0])} ${nameOf("tiers", rest[1])}`;
  if (head === "layouts") return `座席 ${nameOf("layouts", rest[0])} ${nameOf("tiers", rest[2])}`;
  if (head === "products") return `${nameOf("products", rest[0])} 数量`;
  if (head === "forecast" && rest[0] === "band_fill") return `上座率 ${nameOf("bands", rest[1])}`;
  if (head === "forecast" && rest[0] === "session_fill") return `上座率 ${rest[1]}`;
  return FIELD[rest[rest.length - 1]] || [NAMES[head] ?? head, ...rest].join(" ");
}
