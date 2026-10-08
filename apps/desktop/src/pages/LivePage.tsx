import { useState } from "react";
import type { Dict } from "../api";
import { num } from "../api";
import type { PageProps } from "../App";
import { Cell, Section } from "../ui";
import { LiveRead } from "./LiveRead";

const AGES = ["u18", "18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"];
const ORIGIN_ROWS = 8;
const pctText = (v: string | null | undefined) => (v === null || v === undefined || v === "" ? "—" : `${v}%`);

export function LivePage({ state, edit, run }: PageProps) {
  const { book, live } = state;
  const [open, setOpen] = useState<string | null>(null);
  const ageNames = live.age_names as Record<string, string>;
  // Sent as typed; the backend refuses anything that is not a number, so typos show an error instead of vanishing.
  const set = (code: string, key: (string | number)[], v: string) =>
    edit([{ op: "set", path: ["live", code, ...key], value: v.trim() === "" ? null : v.trim() }], "录入入场数据");

  return (
    <div className="page">
      <Section
        title="入场汇总"
        hint="把大麦现场监控平台的截图读进来（可一次选多张），或在下面手动填写。每天和全程的女性、本地、年龄比例按各场已验票人数加权。"
        actions={<LiveRead state={state} edit={edit} run={run} />}
      >
        <div className="forecast-totals">
          <Tile label="已录入场次" value={`${live.overall.sessions} / ${book.sessions.length}`} />
          <Tile label="已验票" value={num(live.overall.checked)} />
          <Tile label="总票数" value={num(live.overall.total)} />
          <Tile label="到场率" value={pctText(live.overall.rate)} />
          <Tile label="女性观众" value={pctText(live.overall.female_pct)} />
        </div>
        <table className="grid numbers">
          <thead>
            <tr>
              <th>日期</th>
              <th>场次数</th>
              <th>已验票</th>
              <th>已实名</th>
              <th>总票数</th>
              <th>到场率</th>
              <th>女性</th>
              <th>本地</th>
              {AGES.map((a) => (
                <th key={a}>{ageNames[a]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {live.days.map((d: Dict) => (
              <SumRow key={d.date} label={d.date} row={d} />
            ))}
            {live.days.length > 0 && <SumRow label="全程" row={live.overall} total />}
          </tbody>
        </table>
        {!live.days.length && <p className="hint">还没有录入任何场次。</p>}
      </Section>

      <Section
        title="每场入场"
        hint="“票务总表已出票” = 权益 + 优先购 + 预留 + 通票 + 公开已售；和大麦“总票数”相差较多时值得核对。点“年龄/来源”录入下半屏的分布。"
      >
        <div className="scroll">
          <table className="grid numbers">
            <thead>
              <tr>
                <th>场次</th>
                <th>读取时间</th>
                <th>已验票数</th>
                <th>已实名数</th>
                <th>总票数</th>
                <th>到场率</th>
                <th>未到</th>
                <th>票务总表已出票</th>
                <th>差异</th>
                <th>女性 %</th>
                <th>本地 %</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {live.sessions.map((s: Dict) => {
                const e = book.live[s.code] || {};
                return (
                  <tr key={s.code} className={open === s.code ? "selected-row" : undefined}>
                    <th scope="row">
                      {s.code} <span className="muted">{s.date}</span>
                    </th>
                    <td>
                      <Cell label={`读取时间 ${s.code}`} type="datetime-local" value={e.at} onCommit={(v) => set(s.code, ["at"], v)} />
                    </td>
                    {(["checked", "realname", "total"] as const).map((k) => (
                      <td key={k}>
                        <Cell label={`${LABELS[k]} ${s.code}`} type="number" value={e[k]} onCommit={(v) => set(s.code, [k], v)} width={80} />
                      </td>
                    ))}
                    <td>{pctText(s.rate)}</td>
                    <td>{s.entered ? num(s.no_show) : "—"}</td>
                    <td>{num(s.issued)}</td>
                    <td className={s.diff ? "neg" : undefined}>{s.entered ? num(s.diff) : "—"}</td>
                    <td>
                      <Cell label={`女性 ${s.code}`} type="number" value={e.female_pct} onCommit={(v) => set(s.code, ["female_pct"], v)} width={60} />
                    </td>
                    <td>
                      <Cell label={`本地 ${s.code}`} type="number" value={e.local_pct} onCommit={(v) => set(s.code, ["local_pct"], v)} width={60} />
                    </td>
                    <td className="nowrap">
                      <button className="link" onClick={() => setOpen(open === s.code ? null : s.code)}>
                        年龄/来源
                      </button>
                      {s.entered && (
                        <button className="link danger" onClick={() => edit([{ op: "set", path: ["live", s.code], value: null }], "清除入场数据")}>
                          清除
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>

      {open && <Detail code={open} entry={book.live[open] || {}} ageNames={ageNames} set={set} edit={edit} />}
    </div>
  );
}

const LABELS: Record<string, string> = { checked: "已验票数", realname: "已实名数", total: "总票数" };

function Detail({ code, entry, ageNames, set, edit }: { code: string; entry: Dict; ageNames: Record<string, string>; set: (c: string, k: (string | number)[], v: string) => void; edit: PageProps["edit"] }) {
  const origins: Dict[] = entry.origins || [];
  const setOrigin = (i: number, key: "name" | "pct", v: string) => {
    const next = Array.from({ length: Math.max(origins.length, i + 1) }, (_, j) => ({ ...(origins[j] || { name: "", pct: "" }) }));
    next[i][key] = v.trim();
    const kept = next.filter((o) => o.name || o.pct);
    edit([{ op: "set", path: ["live", code, "origins"], value: kept.length ? kept : null }], "录入观众来源");
  };
  return (
    <Section title={`${code} 年龄与来源`} hint="照大麦屏幕下半部分的百分比填写（只填数字）。">
      <div className="row wrap">
        <table className="grid" style={{ width: "auto" }}>
          <thead>
            <tr>
              <th>年龄</th>
              <th>%</th>
            </tr>
          </thead>
          <tbody>
            {AGES.map((a) => (
              <tr key={a}>
                <th scope="row">{ageNames[a]}</th>
                <td>
                  <Cell label={`${code} ${ageNames[a]}`} type="number" value={entry.age?.[a]} onCommit={(v) => set(code, ["age", a], v)} width={60} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <table className="grid" style={{ width: "auto" }}>
          <thead>
            <tr>
              <th>#</th>
              <th>来源地</th>
              <th>%</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">本地</th>
              <td>
                <Cell label={`${code} 本地城市`} value={entry.local_name} placeholder="如：某某市" onCommit={(v) => set(code, ["local_name"], v)} />
              </td>
              <td>{pctText(entry.local_pct)}</td>
            </tr>
            {Array.from({ length: ORIGIN_ROWS }, (_, i) => (
              <tr key={i}>
                <th scope="row">{i + 1}</th>
                <td>
                  <Cell label={`${code} 来源 ${i + 1}`} value={origins[i]?.name} onCommit={(v) => setOrigin(i, "name", v)} />
                </td>
                <td>
                  <Cell label={`${code} 来源 ${i + 1} %`} type="number" value={origins[i]?.pct} onCommit={(v) => setOrigin(i, "pct", v)} width={60} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Section>
  );
}

function SumRow({ label, row, total }: { label: string; row: Dict; total?: boolean }) {
  return (
    <tr className={total ? "total" : undefined}>
      <th scope="row">{label}</th>
      <td>{row.sessions}</td>
      <td>{num(row.checked)}</td>
      <td>{num(row.realname)}</td>
      <td>{num(row.total)}</td>
      <td>{pctText(row.rate)}</td>
      <td>{pctText(row.female_pct)}</td>
      <td>{pctText(row.local_pct)}</td>
      {AGES.map((a) => (
        <td key={a}>{pctText(row.age[a])}</td>
      ))}
    </tr>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="total-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
