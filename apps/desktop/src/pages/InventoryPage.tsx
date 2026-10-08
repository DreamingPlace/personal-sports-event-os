import { useState } from "react";
import { save } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import { LINE_NAMES, bandName, num, yuan } from "../api";
import type { PageProps } from "../App";
import { Cell, Problems, Section } from "../ui";

const SUMMARY_LINES = ["seats", "hold", "comp", "priority", "reserve", "product", "public", "sold", "left"];

export function InventoryPage({ state, edit, run }: PageProps) {
  const { book, ledger } = state;
  const [open, setOpen] = useState<string | null>(null);
  const [round, setRound] = useState<string>(book.rounds[0]?.code || "");
  const [counted, setCounted] = useState<string[] | null>(null);
  const [exported, setExported] = useState("");
  const bucketName = (id: string) => book.buckets.find((b: Dict) => b.id === id)?.name || id;
  const roundName = (code: string) => book.rounds.find((r: Dict) => r.code === code)?.name || code;

  const exportCount = async () => {
    const path = await save({ filters: [{ name: "Excel", extensions: ["xlsx"] }], defaultPath: `库存盘点-${new Date().toISOString().slice(0, 10)}.xlsx` });
    if (typeof path !== "string") return;
    const result = await run("export_inventory", { path, rounds: counted });
    if (result) setExported(result.path);
  };

  return (
    <div className="page">
      <Section title="问题">
        <Problems problems={ledger.problems} />
      </Section>

      <Section
        title="库存（每场）"
        hint="点场次看每个票档的明细。公开销售 = 可售座席 − 权益 − 优先购 − 预留 − 通票；剩余 = 公开销售 − 已售。"
        actions={
          <>
            <details className="band-filter">
              <summary>计入的销售轮次：{counted ? counted.map(roundName).join("、") || "无" : "全部"}</summary>
              <label className="check">
                <input type="checkbox" checked={counted === null} onChange={(e) => setCounted(e.target.checked ? null : [])} />
                全部
              </label>
              {book.rounds.map((r: Dict) => (
                <label key={r.code} className="check">
                  <input
                    type="checkbox"
                    disabled={counted === null}
                    checked={counted === null || counted.includes(r.code)}
                    onChange={(e) => setCounted((c) => (e.target.checked ? [...(c || []), r.code] : (c || []).filter((x) => x !== r.code)))}
                  />
                  {r.name}
                </label>
              ))}
            </details>
            <button className="primary" onClick={exportCount}>
              导出库存盘点（Excel）
            </button>
          </>
        }
      >
        {exported && <p className="ok-line">已导出：{exported}</p>}
        <div className="scroll">
          <table className="grid numbers">
            <thead>
              <tr>
                <th>场次</th>
                <th>日期</th>
                <th>比赛阶段</th>
                {SUMMARY_LINES.map((l) => (
                  <th key={l}>{LINE_NAMES[l]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ledger.sessions.map((s: Dict) => (
                <SessionRows key={s.code} s={s} book={book} open={open === s.code} toggle={() => setOpen(open === s.code ? null : s.code)} bucketName={bucketName} roundName={roundName} />
              ))}
              <tr className="total">
                <th colSpan={3}>合计</th>
                {SUMMARY_LINES.map((l) => (
                  <td key={l} className={l === "left" && ledger.totals[l] < 0 ? "neg" : undefined}>
                    {num(ledger.totals[l])}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <Section
        title="录入公开销售"
        hint="按轮次录入每场每档已售张数（以后会从大麦自动读取）。"
        actions={
          <select aria-label="选择轮次" value={round} onChange={(e) => setRound(e.target.value)}>
            {book.rounds.map((r: Dict) => (
              <option key={r.code} value={r.code}>
                {r.name}
              </option>
            ))}
          </select>
        }
      >
        {!book.rounds.length ? (
          <p className="hint">先在“座位分配”里添加放票轮次。</p>
        ) : (
          <table className="grid">
            <thead>
              <tr>
                <th>场次</th>
                {book.tiers.map((t: Dict) => (
                  <th key={t.code}>{t.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {book.sessions.map((s: Dict) => (
                <tr key={s.code}>
                  <th scope="row">{s.code}</th>
                  {book.tiers.map((t: Dict) => (
                    <td key={t.code}>
                      <Cell
                        label={`已售 ${roundName(round)} ${s.code} ${t.name}`}
                        type="number"
                        value={book.sales?.[round]?.[s.code]?.[t.code]}
                        onCommit={(v) => edit([{ op: "set", path: ["sales", round, s.code, t.code], value: v === "" ? null : v.trim() }], "录入销售")}
                        width={70}
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>
    </div>
  );
}

function SessionRows({ s, book, open, toggle, bucketName, roundName }: { s: Dict; book: Dict; open: boolean; toggle: () => void; bucketName: (id: string) => string; roundName: (c: string) => string }) {
  const tiers = book.tiers as Dict[];
  return (
    <>
      <tr className="clickable" onClick={toggle} aria-expanded={open}>
        <th scope="row">
          <button className="link" aria-label={`${open ? "收起" : "展开"} ${s.code}`}>
            {open ? "▾" : "▸"} {s.code}
          </button>
        </th>
        <td>{s.date}</td>
        <td>
          {bandName(book, s.band)}
          {s.china ? " · 中国队" : ""}
        </td>
        {SUMMARY_LINES.map((l) => (
          <td key={l} className={l === "left" && s.total[l] < 0 ? "neg" : undefined}>
            {num(s.total[l])}
          </td>
        ))}
      </tr>
      {open && (
        <tr className="detail">
          <td colSpan={SUMMARY_LINES.length + 3}>
            <table className="grid numbers inner">
              <thead>
                <tr>
                  <th>票档</th>
                  <th>票价</th>
                  {SUMMARY_LINES.map((l) => (
                    <th key={l}>{LINE_NAMES[l]}</th>
                  ))}
                  <th>分配明细</th>
                  <th>放票计划</th>
                </tr>
              </thead>
              <tbody>
                {tiers.map((t) => {
                  const r = s.tiers[t.code];
                  return (
                    <tr key={t.code}>
                      <th scope="row">{t.name}</th>
                      <td>{yuan(r.price)}</td>
                      {SUMMARY_LINES.map((l) => (
                        <td key={l} className={(l === "left" || l === "public") && r[l] < 0 ? "neg" : undefined}>
                          {num(r[l])}
                        </td>
                      ))}
                      <td className="text">
                        {Object.entries(r.by_bucket)
                          .map(([id, q]) => `${bucketName(id)} ${q}`)
                          .join("，") || "—"}
                      </td>
                      <td className="text">
                        {Object.entries(s.release_plan[t.code] || {})
                          .filter(([, q]) => (q as number) > 0)
                          .map(([c, q]) => `${roundName(c)} ${q}`)
                          .join("，") || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}
