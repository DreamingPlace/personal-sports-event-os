import { useState } from "react";
import type { Dict } from "../api";
import { KIND_NAMES, PRODUCT_NAMES, bandName } from "../api";
import type { PageProps } from "../App";
import { Cell, Section, newId } from "../ui";

export function SplitPage({ state, edit }: PageProps) {
  const { book } = state;
  const [selected, setSelected] = useState<string | null>(book.buckets[0]?.id ?? null);
  const set = (path: (string | number)[], value: any) => edit([{ op: "set", path, value }]);
  // Sent as typed; the backend refuses anything that is not a whole number, so typos show an error instead of vanishing.
  const qty = (v: string) => (v === "" ? null : v.trim());
  const bucket = book.buckets.find((b: Dict) => b.id === selected);

  return (
    <div className="page">
      <Section
        title="分配规则"
        hint="设一次“每场多少张”，所有场次自动套用；个别场次不同，在下面的“按场次调整”里改。"
        actions={
          <button onClick={() => edit([{ op: "add", list: "buckets", item: { id: newId("b"), name: "新分配", kind: "comp", default: {} } }])}>添加分配</button>
        }
      >
        <table className="grid">
          <thead>
            <tr>
              <th>名称</th>
              <th>类别</th>
              <th>只用于价格段</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {book.buckets.map((b: Dict) => (
              <tr key={b.id} className={b.id === selected ? "selected-row" : undefined}>
                <td>
                  <Cell label={`分配名称 ${b.name}`} value={b.name} onCommit={(v) => set(["buckets", b.id, "name"], v)} />
                </td>
                <td>
                  <select aria-label={`类别 ${b.name}`} value={b.kind} onChange={(e) => set(["buckets", b.id, "kind"], e.target.value)}>
                    {Object.entries(KIND_NAMES).map(([k, n]) => (
                      <option key={k} value={k}>
                        {n}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <BandFilter book={book} value={b.bands} onChange={(v) => set(["buckets", b.id, "bands"], v)} label={b.name} />
                </td>
                {book.tiers.map((t: Dict) => (
                  <td key={t.code}>
                    <Cell label={`${b.name} ${t.name} 每场`} type="number" value={b.default[t.code]} onCommit={(v) => set(["buckets", b.id, "default", t.code], qty(v))} width={64} />
                    {b.kind === "priority" && (
                      <Cell label={`${b.name} ${t.name} 上限`} type="number" value={b.cap[t.code]} placeholder="上限" onCommit={(v) => set(["buckets", b.id, "cap", t.code], qty(v))} width={64} />
                    )}
                  </td>
                ))}
                <td className="nowrap">
                  <button className="link" onClick={() => setSelected(b.id)}>
                    按场次调整
                  </button>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "buckets", key: b.id }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="hint">优先购下方的小框是“每场上限”，超出时会提醒。</p>
      </Section>

      {bucket && (
        <Section title={`按场次调整：${bucket.name}`} hint="空白 = 用上面的规则（灰色数字）；填了数字 = 这个场次单独用这个数。">
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
              {book.sessions.map((s: Dict) => {
                const inBand = !bucket.bands || bucket.bands.length === 0 || bucket.bands.includes(s.band);
                return (
                  <tr key={s.code}>
                    <th scope="row">
                      {s.code} <span className="muted">{s.date}</span>
                    </th>
                    {book.tiers.map((t: Dict) => (
                      <td key={t.code}>
                        <Cell
                          label={`${bucket.name} ${s.code} ${t.name}`}
                          type="number"
                          value={bucket.overrides?.[s.code]?.[t.code]}
                          placeholder={inBand ? String(bucket.default[t.code] ?? 0) : "0"}
                          onCommit={(v) => set(["buckets", bucket.id, "overrides", s.code, t.code], qty(v))}
                          width={64}
                        />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Section>
      )}

      <Section
        title="通票与套票"
        hint="一日通票/旅行套票的数量按“每天”算，全程通票按总数算。票价留空 = 自动按所含场次票价相加。"
        actions={
          <button onClick={() => edit([{ op: "add", list: "products", item: { id: newId("p"), name: "一日通票", kind: "day", tier: book.tiers[0]?.code || "", quota: 0 } }])}>添加产品</button>
        }
      >
        <table className="grid">
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>票档</th>
              <th>数量</th>
              <th>固定票价</th>
              <th>另加（酒店等）</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.products.map((p: Dict) => (
              <tr key={p.id}>
                <td>
                  <Cell label={`产品名称 ${p.name}`} value={p.name} onCommit={(v) => set(["products", p.id, "name"], v)} />
                </td>
                <td>
                  <select aria-label={`产品类型 ${p.name}`} value={p.kind} onChange={(e) => set(["products", p.id, "kind"], e.target.value)}>
                    {Object.entries(PRODUCT_NAMES).map(([k, n]) => (
                      <option key={k} value={k}>
                        {n}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <select aria-label={`产品票档 ${p.name}`} value={p.tier} onChange={(e) => set(["products", p.id, "tier"], e.target.value)}>
                    {book.tiers.map((t: Dict) => (
                      <option key={t.code} value={t.code}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <Cell label={`产品数量 ${p.name}`} type="number" value={p.quota} onCommit={(v) => set(["products", p.id, "quota"], v.trim() || 0)} width={70} />
                </td>
                <td>
                  <Cell label={`固定票价 ${p.name}`} type="number" value={p.price} placeholder="自动" onCommit={(v) => set(["products", p.id, "price"], v === "" ? null : v)} width={90} />
                </td>
                <td>
                  <Cell label={`另加 ${p.name}`} type="number" value={p.extra} onCommit={(v) => set(["products", p.id, "extra"], v || "0")} width={90} />
                </td>
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "products", key: p.id }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section
        title="放票轮次"
        hint="每轮放出各价格段“公开销售”座位的百分之几。"
        actions={
          <button
            onClick={() => {
              let i = book.rounds.length + 1;
              while (book.rounds.some((r: Dict) => r.code === "R" + i)) i += 1;
              edit([{ op: "add", list: "rounds", item: { code: "R" + i, name: `第${i}轮`, opens: "", share: {} } }]);
            }}
          >
            添加轮次
          </button>
        }
      >
        <table className="grid">
          <thead>
            <tr>
              <th>名称</th>
              <th>开售时间</th>
              {book.bands.map((b: Dict) => (
                <th key={b.code}>{b.name} %</th>
              ))}
              <th />
            </tr>
          </thead>
          <tbody>
            {book.rounds.map((r: Dict) => (
              <tr key={r.code}>
                <td>
                  <Cell label={`轮次名称 ${r.code}`} value={r.name} onCommit={(v) => set(["rounds", r.code, "name"], v)} />
                </td>
                <td>
                  <Cell label={`开售时间 ${r.code}`} type="datetime-local" value={r.opens} onCommit={(v) => set(["rounds", r.code, "opens"], v)} />
                </td>
                {book.bands.map((b: Dict) => (
                  <td key={b.code}>
                    <Cell label={`${r.name} ${bandName(book, b.code)} 比例`} type="number" value={r.share[b.code]} onCommit={(v) => set(["rounds", r.code, "share", b.code], v === "" ? null : v)} width={64} />
                  </td>
                ))}
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "rounds", key: r.code }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

function BandFilter({ book, value, onChange, label }: { book: Dict; value: string[] | null; onChange: (v: string[] | null) => void; label: string }) {
  const chosen = value || [];
  return (
    <details className="band-filter">
      <summary aria-label={`价格段范围 ${label}`}>{chosen.length ? chosen.map((c) => bandName(book, c)).join("、") : "全部"}</summary>
      {book.bands.map((b: Dict) => (
        <label key={b.code} className="check">
          <input
            type="checkbox"
            checked={chosen.includes(b.code)}
            onChange={(e) => {
              const next = e.target.checked ? [...chosen, b.code] : chosen.filter((c) => c !== b.code);
              onChange(next.length ? next : null);
            }}
          />
          {b.name}
        </label>
      ))}
    </details>
  );
}
