import { useState } from "react";
import type { Dict } from "../api";
import { call } from "../api";
import type { PageProps } from "../App";
import { Confirm, Section } from "../ui";

export function VersionsPage({ state, run }: PageProps) {
  const [label, setLabel] = useState("");
  const [diff, setDiff] = useState<{ title: string; rows: Dict[] } | null>(null);
  const [restoring, setRestoring] = useState<Dict | null>(null);
  const [error, setError] = useState("");
  const versions = [...state.versions].reverse();

  const compareWith = async (v: Dict) => {
    setError("");
    try {
      const rows = await call<Dict[]>("compare", { old: v.id, new: "CURRENT" });
      setDiff({ title: `“${v.label}” → 现在`, rows });
    } catch (e: any) {
      setError(e?.message || String(e));
    }
  };

  return (
    <div className="page">
      <Section title="保存版本" hint="每次修改都会自动保存到文件里。“版本”是你想留下的一个时间点，例如“1128开售版本”。">
        <div className="row">
          <input aria-label="版本名称" placeholder="版本名称，例如 1128开售版本" value={label} onChange={(e) => setLabel(e.target.value)} />
          <button className="primary" disabled={!label.trim()} onClick={() => run("save_version", { label: label.trim() }).then(() => setLabel(""))}>
            保存版本
          </button>
        </div>
      </Section>

      <Section title="已保存的版本">
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {!versions.length && <p className="hint">还没有保存过版本。</p>}
        <ul className="plain">
          {versions.map((v) => (
            <li key={v.id}>
              <strong>{v.label}</strong> <span className="muted">{new Date(v.created_at).toLocaleString()}</span>{" "}
              <button className="link" onClick={() => compareWith(v)}>
                和现在比较
              </button>
              <button className="link" onClick={() => setRestoring(v)}>
                恢复到这个版本
              </button>
            </li>
          ))}
        </ul>
      </Section>

      {diff && (
        <Section title={`变化：${diff.title}`} actions={<button onClick={() => setDiff(null)}>关闭</button>}>
          {!diff.rows.length ? (
            <p className="ok-line">没有变化</p>
          ) : (
            <table className="grid">
              <thead>
                <tr>
                  <th>位置</th>
                  <th>原来</th>
                  <th>现在</th>
                </tr>
              </thead>
              <tbody>
                {diff.rows.map((r, i) => (
                  <tr key={i}>
                    <td>{r.path.join(" / ")}</td>
                    <td>{r.old === undefined || r.old === null ? "—" : String(r.old)}</td>
                    <td>{r.new === undefined || r.new === null ? "—" : String(r.new)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Section>
      )}

      <Section title="修改记录" hint="最近 50 条。">
        <ul className="plain log">
          {[...state.log].reverse().map((e, i) => (
            <li key={i}>
              <span className="muted">{new Date(e.at).toLocaleString()}</span> {e.action} {e.detail && <span className="muted">· {e.detail}</span>}
            </li>
          ))}
        </ul>
      </Section>

      {restoring && (
        <Confirm
          title="恢复版本"
          confirmText="恢复"
          onCancel={() => setRestoring(null)}
          onConfirm={async () => {
            await run("restore", { id: restoring.id });
            setRestoring(null);
          }}
        >
          <p>把票务总表恢复到“{restoring.label}”。恢复前会自动把现在的内容保存为一个版本。</p>
        </Confirm>
      )}
    </div>
  );
}
