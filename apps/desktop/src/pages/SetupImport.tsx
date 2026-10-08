import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import type { PageProps } from "../App";
import { Confirm } from "../ui";

type Scan = {
  event: { name?: string; year?: number; dates?: string };
  prices: { source: string; kind: string; tiers: string[]; options: { label: string; prices: Record<string, Record<string, string>> }[] }[];
  seats: { source: string; seats: Record<string, number> }[];
  sessions: { source: string; sessions: { code: string; date: string }[] }[];
};

const fileName = (p: string) => p.split(/[\\/]/).pop();

/** "从文件导入…": read the user's Word plan and Excel sheets, show what was recognised, and add only what they tick. */
export function SetupImport({ state, run }: PageProps) {
  const { book } = state;
  const [scan, setScan] = useState<Scan | null>(null);
  const [files, setFiles] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [useEvent, setUseEvent] = useState(true);
  const [priceAt, setPriceAt] = useState("");
  const [seatsAt, setSeatsAt] = useState("");
  const [sessionsAt, setSessionsAt] = useState("");
  const [layout, setLayout] = useState("NEW");

  const pick = async () => {
    const picked = await open({ multiple: true, filters: [{ name: "方案和表格", extensions: ["docx", "xlsx", "xlsm"] }] });
    const paths = Array.isArray(picked) ? picked : typeof picked === "string" ? [picked] : [];
    if (!paths.length) return;
    setBusy(true);
    const result: Scan | undefined = await run("setup_scan", { paths });
    setBusy(false);
    if (!result) return;
    setFiles(paths);
    setScan(result);
    setUseEvent(!!result.event.name);
    // Default to the last table found in each kind: later sheets are usually the newer plan.
    setPriceAt(result.prices.length ? `${result.prices.length - 1}:${result.prices[result.prices.length - 1].options.length - 1}` : "");
    setSeatsAt(result.seats.length ? String(result.seats.length - 1) : "");
    setSessionsAt(result.sessions.length ? "0" : "");
    setLayout(book.layouts[0]?.code || "NEW");
  };

  const chosenPrices = () => {
    if (!scan || !priceAt) return null;
    const [f, o] = priceAt.split(":").map(Number);
    return scan.prices[f]?.options[o]?.prices || null;
  };

  const apply = async () => {
    if (!scan) return;
    const choice: Dict = {};
    if (useEvent && scan.event.name) choice.event = { name: scan.event.name, year: scan.event.year };
    const prices = chosenPrices();
    if (prices) choice.prices = prices;
    if (seatsAt !== "") {
      choice.seats = scan.seats[Number(seatsAt)].seats;
      choice.layout = layout === "NEW" ? "" : layout;
    } else if (layout !== "NEW") choice.layout = layout;
    if (sessionsAt !== "") choice.sessions = scan.sessions[Number(sessionsAt)].sessions;
    const result = await run("setup_apply", { choice });
    if (result) setScan(null);
  };

  const prices = chosenPrices();
  const stages = prices ? Object.keys(prices) : [];
  const tiers = prices ? [...new Set(stages.flatMap((s) => Object.keys(prices[s])))] : [];
  const nothing = !scan || (!(useEvent && scan.event.name) && !prices && seatsAt === "" && sessionsAt === "");

  return (
    <>
      <button onClick={pick} disabled={busy}>
        {busy ? "读取中…" : "从文件导入…"}
      </button>
      {scan && (
        <Confirm title="从文件导入设置" confirmText="导入所选内容" onCancel={() => setScan(null)} onConfirm={() => !nothing && apply()}>
          <p className="hint">
            读取了：{files.map(fileName).join("、")}。下面是认出来的内容，请核对后勾选要导入的部分。票档、比赛阶段按名称对应，没有的会新建；已有的场次只更新日期。
          </p>

          <h3>赛事</h3>
          {scan.event.name ? (
            <label className="check">
              <input type="checkbox" checked={useEvent} onChange={(e) => setUseEvent(e.target.checked)} />
              {scan.event.year} 年 · {scan.event.name}
              {scan.event.dates && <span className="muted"> · {scan.event.dates}</span>}
            </label>
          ) : (
            <p className="muted">没有认出赛事名称。</p>
          )}

          <h3>票价</h3>
          {scan.prices.length ? (
            <>
              <select aria-label="选择票价表" value={priceAt} onChange={(e) => setPriceAt(e.target.value)}>
                <option value="">（不导入票价）</option>
                {scan.prices.map((f, i) =>
                  f.options.map((o, j) => (
                    <option key={`${i}:${j}`} value={`${i}:${j}`}>
                      {f.source} · {o.label}
                    </option>
                  )),
                )}
              </select>
              {prices && (
                <table className="grid">
                  <thead>
                    <tr>
                      <th>比赛阶段</th>
                      {tiers.map((t) => (
                        <th key={t}>{t}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {stages.map((s) => (
                      <tr key={s}>
                        <th scope="row">{s}</th>
                        {tiers.map((t) => (
                          <td key={t}>{prices[s][t] ?? "—"}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          ) : (
            <p className="muted">没有认出票价表。</p>
          )}

          <h3>座席</h3>
          {scan.seats.length ? (
            <div className="row">
              <select aria-label="选择座席数" value={seatsAt} onChange={(e) => setSeatsAt(e.target.value)}>
                <option value="">（不导入座席）</option>
                {scan.seats.map((s, i) => (
                  <option key={i} value={String(i)}>
                    {s.source} · {Object.entries(s.seats)
                      .map(([t, n]) => `${t} ${n}`)
                      .join("，")}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <p className="muted">没有认出各票档总座席。</p>
          )}
          <label>
            座席和新场次用的布局{" "}
            <select aria-label="导入到布局" value={layout} onChange={(e) => setLayout(e.target.value)}>
              <option value="NEW">新建“导入布局”</option>
              {book.layouts.map((l: Dict) => (
                <option key={l.code} value={l.code}>
                  {l.name}
                </option>
              ))}
            </select>
          </label>

          <h3>场次</h3>
          {scan.sessions.length ? (
            <>
              <select aria-label="选择场次" value={sessionsAt} onChange={(e) => setSessionsAt(e.target.value)}>
                <option value="">（不导入场次）</option>
                {scan.sessions.map((s, i) => (
                  <option key={i} value={String(i)}>
                    {s.source} · {s.sessions.length} 场
                  </option>
                ))}
              </select>
              {sessionsAt !== "" && (
                <p className="muted">
                  {scan.sessions[Number(sessionsAt)].sessions.map((s) => `${s.code} ${s.date.slice(5)}`).join("，")}
                  。新场次的比赛阶段先用第一个，导入后在场次表里改。
                </p>
              )}
            </>
          ) : (
            <p className="muted">没有认出场次表（S1、S2… 和日期）。</p>
          )}
        </Confirm>
      )}
    </>
  );
}
