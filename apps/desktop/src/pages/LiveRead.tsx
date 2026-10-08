import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import type { PageProps } from "../App";
import { Confirm } from "../ui";

const AGES = ["u18", "18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"];
const FIELDS: [string, string][] = [
  ["at", "读取时间"],
  ["checked", "已验票数"],
  ["realname", "已实名数"],
  ["total", "总票数"],
  ["female_pct", "女性 %"],
  ["local_name", "本地"],
  ["local_pct", "本地 %"],
];

type Draft = { path: string; session: string; values: Record<string, string>; read: Set<string>; warnings: string[]; error?: string };

/** "读取截图…": OCR screenshots of Damai's on-site screen, show what was read for checking, then save. */
export function LiveRead({ state, edit, run }: PageProps) {
  const { book, live } = state;
  const ageNames = live.age_names as Record<string, string>;
  const [drafts, setDrafts] = useState<Draft[] | null>(null);
  const [reading, setReading] = useState(false);

  const pick = async () => {
    const picked = await open({ multiple: true, filters: [{ name: "截图", extensions: ["png", "jpg", "jpeg", "webp"] }] });
    const paths = Array.isArray(picked) ? picked : typeof picked === "string" ? [picked] : [];
    if (!paths.length) return;
    setReading(true);
    const result = await run("live_read", { paths });
    setReading(false);
    if (!result) return;
    setDrafts(
      result.results.map((r: Dict) => {
        const values: Record<string, string> = {};
        for (const [k, v] of Object.entries(r.entry || {})) {
          if (k === "age") for (const [a, p] of Object.entries(v as Dict)) values["age:" + a] = String(p);
          else values[k] = String(v);
        }
        return { path: r.path, session: r.known ? r.session : "", values, read: new Set(Object.keys(values)), warnings: r.warnings || [], error: r.error };
      }),
    );
  };

  const update = (i: number, change: Partial<Draft>) => setDrafts((d) => d!.map((x, j) => (j === i ? { ...x, ...change } : x)));
  const setValue = (i: number, key: string, v: string) => update(i, { values: { ...drafts![i].values, [key]: v } });

  const save = async () => {
    const ops: Dict[] = [];
    for (const d of drafts || []) {
      if (d.error || !d.session) continue;
      for (const [key, v] of Object.entries(d.values)) {
        if (v.trim() === "") continue;
        const path = key.startsWith("age:") ? ["live", d.session, "age", key.slice(4)] : ["live", d.session, key];
        ops.push({ op: "set", path, value: v.trim() });
      }
    }
    if (ops.length) await edit(ops, "读取入场截图");
    setDrafts(null);
  };

  const usable = (drafts || []).filter((d) => !d.error && d.session).length;
  const name = (p: string) => p.split(/[\\/]/).pop();

  return (
    <>
      <button className="primary" onClick={pick} disabled={reading}>
        {reading ? "识别中…" : "读取截图…"}
      </button>
      {drafts && (
        <Confirm title="核对截图读到的数字" confirmText={`保存 ${usable} 场`} onCancel={() => setDrafts(null)} onConfirm={save}>
          <p className="hint">文字识别在本机进行。黄色格子是没读到的，请照截图补上或留空；读到的也请扫一眼再保存。</p>
          {drafts.map((d, i) => (
            <div key={d.path} className="read-card">
              <div className="row">
                <strong>{name(d.path)}</strong>
                {d.error ? (
                  <span className="form-error">{d.error}</span>
                ) : (
                  <label>
                    场次
                    <select aria-label={`场次 ${name(d.path)}`} value={d.session} onChange={(e) => update(i, { session: e.target.value })}>
                      <option value="">（选择场次）</option>
                      {book.sessions.map((s: Dict) => (
                        <option key={s.code} value={s.code}>
                          {s.code} {s.date}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
              </div>
              {!d.error && (
                <>
                  {d.warnings.map((w) => (
                    <p key={w} className="form-error">
                      {w}
                    </p>
                  ))}
                  <div className="read-grid">
                    {[...FIELDS, ...AGES.map((a) => ["age:" + a, ageNames[a] + " %"] as [string, string])].map(([key, label]) => (
                      <label key={key} className={d.read.has(key) ? undefined : "missing"}>
                        {label}
                        <input aria-label={`${label} ${name(d.path)}`} value={d.values[key] ?? ""} onChange={(e) => setValue(i, key, e.target.value)} />
                      </label>
                    ))}
                  </div>
                </>
              )}
            </div>
          ))}
        </Confirm>
      )}
    </>
  );
}
