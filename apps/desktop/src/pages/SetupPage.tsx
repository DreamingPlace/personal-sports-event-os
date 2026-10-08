import { useState } from "react";
import { save } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import type { PageProps } from "../App";
import { Cell, Confirm, Section } from "../ui";

export function SetupPage({ state, edit, run, go }: PageProps) {
  const { book } = state;
  const ev = book.event;
  const [copying, setCopying] = useState(false);
  const set = (path: (string | number)[], value: any) => edit([{ op: "set", path, value }]);
  const nextCode = (prefix: string, items: Dict[]) => {
    let i = items.length + 1;
    while (items.some((x) => x.code === prefix + i)) i += 1;
    return prefix + i;
  };

  return (
    <div className="page">
      <Section title="赛事" actions={<button onClick={() => setCopying(true)}>复制为下一届</button>}>
        <div className="form-grid">
          <label>
            名称 <Cell label="赛事名称" value={ev.name} onCommit={(v) => set(["event", "name"], v)} />
          </label>
          <label>
            年份 <Cell label="年份" type="number" value={ev.year} onCommit={(v) => set(["event", "year"], v ? Number(v) : null)} width={90} />
          </label>
          <label>
            场馆 <Cell label="场馆" value={ev.venue} onCommit={(v) => set(["event", "venue"], v)} />
          </label>
          <label>
            票务代理费 % <Cell label="代理费百分比" type="number" value={ev.agent_fee_pct} onCommit={(v) => set(["event", "agent_fee_pct"], v || "0")} width={80} />
          </label>
        </div>
      </Section>

      <Section title="票档" hint="遮挡票档可以只填“原票档”和“减价”，票价自动等于原票档减去这个金额。">
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th>原票档（遮挡）</th>
              <th>减价</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.tiers.map((t: Dict) => (
              <tr key={t.code}>
                <td>
                  <Cell label={`票档名称 ${t.code}`} value={t.name} onCommit={(v) => set(["tiers", t.code, "name"], v)} />
                </td>
                <td>
                  <select aria-label={`原票档 ${t.code}`} value={t.blocked_of || ""} onChange={(e) => set(["tiers", t.code, "blocked_of"], e.target.value || null)}>
                    <option value="">（不是遮挡票档）</option>
                    {book.tiers
                      .filter((o: Dict) => o.code !== t.code && !o.blocked_of)
                      .map((o: Dict) => (
                        <option key={o.code} value={o.code}>
                          {o.name}
                        </option>
                      ))}
                  </select>
                </td>
                <td>{t.blocked_of && <Cell label={`减价 ${t.code}`} type="number" value={t.blocked_discount} onCommit={(v) => set(["tiers", t.code, "blocked_discount"], v || "0")} width={80} />}</td>
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "tiers", key: t.code }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={() => edit([{ op: "add", list: "tiers", item: { code: nextCode("T", book.tiers), name: "新票档" } }])}>添加票档</button>
      </Section>

      <Section
        title="比赛阶段"
        hint="同一阶段的场次票价相同，例如预赛、循环赛、半决赛、决赛；周末票价不同就再加一个“循环赛周末”。这里只填阶段名称，每个场次在下方选它属于哪个阶段。"
        actions={
          go && (
            <button className="primary" onClick={() => go("prices")}>
              填票价 →
            </button>
          )
        }
      >
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.bands.map((b: Dict) => (
              <tr key={b.code}>
                <td>
                  <Cell label={`比赛阶段名称 ${b.code}`} value={b.name} onCommit={(v) => set(["bands", b.code, "name"], v)} />
                </td>
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "bands", key: b.code }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={() => edit([{ op: "add", list: "bands", item: { code: nextCode("band", book.bands), name: "新比赛阶段" } }])}>添加比赛阶段</button>
      </Section>

      <Section title="场次" hint="一个比赛日可以有多个场次；一个场次可以包含多场比赛（写在备注里）。">
        <table>
          <thead>
            <tr>
              <th>场次</th>
              <th>日期</th>
              <th>开始</th>
              <th>比赛阶段</th>
              <th>座席布局</th>
              <th>中国队</th>
              <th>备注（比赛）</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.sessions.map((s: Dict) => (
              <tr key={s.code}>
                <td>
                  <Cell label={`场次代码 ${s.code}`} value={s.code} onCommit={(v) => edit([{ op: "rename", list: "sessions", key: s.code, to: v }])} width={70} />
                </td>
                <td>
                  <Cell label={`日期 ${s.code}`} type="date" value={s.date} onCommit={(v) => set(["sessions", s.code, "date"], v)} />
                </td>
                <td>
                  <Cell label={`开始时间 ${s.code}`} type="time" value={s.start} onCommit={(v) => set(["sessions", s.code, "start"], v)} />
                </td>
                <td>
                  <select aria-label={`比赛阶段 ${s.code}`} value={s.band} onChange={(e) => set(["sessions", s.code, "band"], e.target.value)}>
                    {!book.bands.some((b: Dict) => b.code === s.band) && <option value={s.band}>{s.band || "（请选择）"}</option>}
                    {book.bands.map((b: Dict) => (
                      <option key={b.code} value={b.code}>
                        {b.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <select aria-label={`座席布局 ${s.code}`} value={s.layout} onChange={(e) => set(["sessions", s.code, "layout"], e.target.value)}>
                    {!book.layouts.some((l: Dict) => l.code === s.layout) && <option value={s.layout}>{s.layout || "（请选择）"}</option>}
                    {book.layouts.map((l: Dict) => (
                      <option key={l.code} value={l.code}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="center">
                  <input type="checkbox" aria-label={`中国队出场 ${s.code}`} checked={!!s.china} onChange={(e) => set(["sessions", s.code, "china"], e.target.checked)} />
                </td>
                <td>
                  <Cell label={`备注 ${s.code}`} value={s.note} onCommit={(v) => set(["sessions", s.code, "note"], v)} />
                </td>
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "sessions", key: s.code }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button
          onClick={() => {
            const last = book.sessions[book.sessions.length - 1];
            edit([
              {
                op: "add",
                list: "sessions",
                item: { code: nextCode("S", book.sessions), date: last?.date || "", start: "", band: last?.band || book.bands[0]?.code || "", layout: last?.layout || book.layouts[0]?.code || "", china: false, note: "" },
              },
            ]);
          }}
        >
          添加场次
        </button>
      </Section>
      {copying && <CopyDialog name={ev.name} year={ev.year} run={run} onClose={() => setCopying(false)} />}
    </div>
  );
}

function CopyDialog({ name, year, run, onClose }: { name: string; year: number | null; run: PageProps["run"]; onClose: () => void }) {
  const [newName, setNewName] = useState(name);
  const [newYear, setNewYear] = useState(String((year || new Date().getFullYear()) + 1));
  const [days, setDays] = useState("364");
  const [pw, setPw] = useState("");
  return (
    <Confirm
      title="复制为下一届"
      confirmText="选择保存位置并复制"
      onCancel={onClose}
      onConfirm={async () => {
        const path = await save({ filters: [{ name: "票务总表", extensions: ["ticketbook"] }], defaultPath: `${newName}-${newYear}.ticketbook` });
        if (typeof path !== "string") return;
        await run("copy_event", { path, password: pw, name: newName, year: Number(newYear) || null, shift_days: Number(days) || 0 });
        onClose();
      }}
    >
      <p className="hint">复制场次、票档、价格、座席和分配规则；不复制销售数据。新文件单独加密。</p>
      <label>
        名称 <input value={newName} onChange={(e) => setNewName(e.target.value)} />
      </label>
      <label>
        年份 <input value={newYear} onChange={(e) => setNewYear(e.target.value)} />
      </label>
      <label>
        日期顺延天数 <input value={days} onChange={(e) => setDays(e.target.value)} />
      </label>
      <label>
        新文件密码 <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} />
      </label>
    </Confirm>
  );
}
