import { useEffect, useMemo, useState } from "react";
import { open, save } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import type { PageProps } from "../App";
import { Section } from "../ui";

const TABLES: [string, string][] = [
  ["票价表", "价格段 × 票档的票价表"],
  ["座席表", "每个票档的总座席、各项分配和可售"],
  ["场次表", "每场的日期、价格段、公开销售和预计票房"],
];

export function ReportsPage({ state, edit, run }: PageProps) {
  const { book } = state;
  const [fields, setFields] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState("");
  const [made, setMade] = useState<{ path: string; unknown: string[] } | null>(null);
  const [copied, setCopied] = useState("");

  // Values change with every edit, so ask again whenever the book changes.
  useEffect(() => {
    let live = true;
    run("report_fields").then((r) => live && r && setFields(r.fields));
    return () => {
      live = false;
    };
  }, [state]);

  const shown = useMemo(() => Object.entries(fields).filter(([k, v]) => !filter || k.includes(filter) || v.includes(filter)), [fields, filter]);

  const add = async () => {
    const picked = await open({ multiple: false, filters: [{ name: "Word", extensions: ["docx"] }] });
    if (typeof picked === "string") await run("template_add", { path: picked });
  };
  const make = async (t: Dict) => {
    const path = await save({ filters: [{ name: "Word", extensions: ["docx"] }], defaultPath: `${t.name}-${new Date().toISOString().slice(0, 10)}.docx` });
    if (typeof path !== "string") return;
    const result = await run("report_make", { id: t.id, path });
    if (result) setMade(result);
  };
  const copy = async (name: string) => {
    try {
      await navigator.clipboard.writeText(`{{${name}}}`);
      setCopied(name);
    } catch {
      setCopied("");
    }
  };
  // Markers with " + ", " - " or " * " are sums the app works out when the report is made.
  const unknownOf = (t: Dict) => (t.markers || []).filter((m: string) => !(m in fields) && !TABLES.some(([n]) => n === m) && !/\s[+\-*]\s/.test(m));

  return (
    <div className="page">
      <Section
        title="报告模板"
        hint="用你自己的 Word 文件做模板：在要填数字的地方写 {{字段名}}（字段名见下方），生成时自动填入票务总表里的最新数字。模板保存在加密文件里。"
        actions={
          <button className="primary" onClick={add}>
            添加 Word 模板…
          </button>
        }
      >
        {made && (
          <p className="ok-line">
            已生成：{made.path}
            {made.unknown.length > 0 && <span className="form-error"> · 以下字段不认识，原样保留：{made.unknown.join("、")}</span>}
          </p>
        )}
        {book.templates.length === 0 ? (
          <p className="hint">还没有模板。</p>
        ) : (
          <table className="grid">
            <thead>
              <tr>
                <th>模板</th>
                <th>文件</th>
                <th>字段数</th>
                <th>不认识的字段</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {book.templates.map((t: Dict) => {
                const unknown = unknownOf(t);
                return (
                  <tr key={t.id}>
                    <th scope="row">{t.name}</th>
                    <td className="text">
                      {t.file} <span className="muted">{Math.round(t.size / 1024)} KB</span>
                    </td>
                    <td>{(t.markers || []).length}</td>
                    <td className={unknown.length ? "neg" : undefined}>{unknown.join("、") || "—"}</td>
                    <td className="nowrap">
                      <button className="primary" onClick={() => make(t)}>
                        生成报告…
                      </button>{" "}
                      <button className="link danger" onClick={() => edit([{ op: "remove", list: "templates", key: t.id }], "删除报告模板")}>
                        删除
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </Section>

      <Section
        title="可用字段"
        hint="点字段名复制 {{字段名}}，粘贴到 Word 模板里。单独占一段的 {{票价表}}、{{座席表}}、{{场次表}} 会换成整张表。各场不同的数字显示为范围（如 6000–6100）。也可以写简单加减乘，如 {{每场可售 - 5345}}（符号两边留空格）。"
        actions={<input aria-label="查找字段" placeholder="查找…" value={filter} onChange={(e) => setFilter(e.target.value)} />}
      >
        <table className="grid">
          <thead>
            <tr>
              <th>字段</th>
              <th>现在的值</th>
            </tr>
          </thead>
          <tbody>
            {TABLES.filter(([n, d]) => !filter || n.includes(filter) || d.includes(filter)).map(([n, d]) => (
              <tr key={n}>
                <td>
                  <button className="link" onClick={() => copy(n)}>{`{{${n}}}`}</button>
                </td>
                <td className="text muted">{d}</td>
              </tr>
            ))}
            {shown.map(([k, v]) => (
              <tr key={k}>
                <td>
                  <button className="link" onClick={() => copy(k)}>
                    {`{{${k}}}`}
                  </button>
                  {copied === k && <span className="muted"> 已复制</span>}
                </td>
                <td className="text">{v || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}
