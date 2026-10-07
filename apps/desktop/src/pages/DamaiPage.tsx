import { useState } from "react";
import type { Dict } from "../api";
import { num, yuan } from "../api";
import type { PageProps } from "../App";
import { Section } from "../ui";

const pctText = (v: string | null | undefined) => (v === null || v === undefined ? "—" : `${v}%`);
const nowLocal = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
};

export function DamaiPage({ state, edit, run }: PageProps) {
  const { damai, forecast } = state;
  const [text, setText] = useState("");
  const [at, setAt] = useState(nowLocal());
  const [note, setNote] = useState("");
  const [read, setRead] = useState<Dict[] | null>(null);

  const readText = async () => {
    const result = await run("damai_read", { text });
    if (result) setRead(result.projects);
  };
  const save = async () => {
    const result = await run("damai_add", { projects: read, at, note });
    if (result) {
      setRead(null);
      setText("");
      setNote("");
    }
  };
  const snaps: Dict[] = damai.snapshots;

  return (
    <div className="page">
      <Section
        title="读取大麦销售数据"
        hint="在浏览器打开大麦后台“数据中心 → 票房销售统计”，从第一行项目ID拖选到最后一行，复制，粘贴到下面，再按“读取”。数据只存在本机加密文件里。"
      >
        <textarea aria-label="粘贴大麦表格" className="paste" rows={6} value={text} onChange={(e) => setText(e.target.value)} placeholder="在这里粘贴…" />
        <div className="row">
          <button className="primary" disabled={!text.trim()} onClick={readText}>
            读取
          </button>
        </div>
        {read && (
          <>
            <ProjectTable rows={read} />
            <div className="row">
              <label>
                数据时间
                <input type="datetime-local" value={at} onChange={(e) => setAt(e.target.value)} aria-label="数据时间" />
              </label>
              <label>
                备注
                <input value={note} onChange={(e) => setNote(e.target.value)} aria-label="备注" />
              </label>
              <button onClick={() => setRead(null)}>放弃</button>
              <button className="primary" onClick={save}>
                保存这次记录
              </button>
            </div>
          </>
        )}
      </Section>

      <Section title="最新销售" hint={damai.latest ? `数据时间 ${damai.latest.at.replace("T", " ")}` : undefined}>
        {damai.latest ? (
          <>
            <div className="forecast-totals">
              <Tile label="已售张数" value={num(damai.latest.total.sold_qty)} />
              <Tile label="已售金额（元）" value={yuan(damai.latest.total.sold_amount)} />
              <Tile label="出票率" value={pctText(damai.latest.total.rate)} />
              <Tile label="占票房测算" value={pctText(damai.vs_forecast)} hint={`测算 ${yuan(forecast.gross)} 元`} />
            </div>
            <ProjectTable rows={damai.latest.projects} total={damai.latest.total} />
          </>
        ) : (
          <p className="hint">还没有记录。</p>
        )}
      </Section>

      {snaps.length > 0 && (
        <Section title="历次记录" hint="每次读取保存一条，用来看销售进度。">
          <table className="grid numbers">
            <thead>
              <tr>
                <th>数据时间</th>
                <th>已售张数</th>
                <th>比上次</th>
                <th>已售金额</th>
                <th>比上次</th>
                <th>出票率</th>
                <th>备注</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {[...snaps].reverse().map((s, i, list) => {
                const prev = list[i + 1];
                const dq = prev ? s.total.sold_qty - prev.total.sold_qty : null;
                const da = prev ? (Number(s.total.sold_amount) - Number(prev.total.sold_amount)).toFixed(2) : null;
                return (
                  <tr key={s.id}>
                    <th scope="row">{s.at.replace("T", " ")}</th>
                    <td>{num(s.total.sold_qty)}</td>
                    <td>{dq === null ? "—" : (dq > 0 ? "+" : "") + num(dq)}</td>
                    <td>{yuan(s.total.sold_amount)}</td>
                    <td>{da === null ? "—" : (Number(da) > 0 ? "+" : "") + yuan(da)}</td>
                    <td>{pctText(s.total.rate)}</td>
                    <td className="text">{s.note}</td>
                    <td>
                      <button className="link danger" onClick={() => edit([{ op: "remove", list: "damai", key: s.id }], "删除大麦记录")}>
                        删除
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Section>
      )}
    </div>
  );
}

function ProjectTable({ rows, total }: { rows: Dict[]; total?: Dict }) {
  return (
    <div className="scroll">
      <table className="grid numbers">
        <thead>
          <tr>
            <th>项目ID</th>
            <th>项目名称</th>
            <th>规划张数</th>
            <th>已售张数</th>
            <th>今日张数</th>
            <th>剩余张数</th>
            <th>规划金额</th>
            <th>已售金额</th>
            <th>今日金额</th>
            <th>剩余金额</th>
            {total && <th>出票率</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.id}>
              <td className="text">{p.id}</td>
              <td className="text">{p.name}</td>
              <td>{num(p.plan_qty)}</td>
              <td>{num(p.sold_qty)}</td>
              <td>{num(p.today_qty)}</td>
              <td>{num(p.left_qty)}</td>
              <td>{yuan(p.plan_amount)}</td>
              <td>{yuan(p.sold_amount)}</td>
              <td>{yuan(p.today_amount)}</td>
              <td>{yuan(p.left_amount)}</td>
              {total && <td>{pctText(p.rate)}</td>}
            </tr>
          ))}
          {total && (
            <tr className="total">
              <th colSpan={2}>合计</th>
              <td>{num(total.plan_qty)}</td>
              <td>{num(total.sold_qty)}</td>
              <td>{num(total.today_qty)}</td>
              <td>{num(total.left_qty)}</td>
              <td>{yuan(total.plan_amount)}</td>
              <td>{yuan(total.sold_amount)}</td>
              <td>{yuan(total.today_amount)}</td>
              <td>{yuan(total.left_amount)}</td>
              <td>{pctText(total.rate)}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="total-tile">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint && <small className="muted">{hint}</small>}
    </div>
  );
}
