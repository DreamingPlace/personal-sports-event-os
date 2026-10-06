import type { Dict } from "../api";
import { yuan } from "../api";
import type { PageProps } from "../App";
import { Cell, Section } from "../ui";

/** Price for display: own price, or base price minus discount for a view-blocked tier. */
export function shownPrice(book: Dict, band: string, tier: Dict): { value: string; derived: boolean } {
  const own = book.prices?.[band]?.[tier.code];
  if (own !== undefined && own !== null && own !== "") return { value: String(own), derived: false };
  if (tier.blocked_of) {
    const base = book.prices?.[band]?.[tier.blocked_of];
    if (base !== undefined && base !== null && base !== "") return { value: String(Number(base) - Number(tier.blocked_discount || 0)), derived: true };
  }
  return { value: "", derived: false };
}

export function PricesPage({ state, edit }: PageProps) {
  const { book } = state;
  const set = (path: (string | number)[], value: any) => edit([{ op: "set", path, value }]);
  const nextLayout = () => {
    let i = book.layouts.length + 1;
    while (book.layouts.some((l: Dict) => l.code === "L" + i)) i += 1;
    return "L" + i;
  };
  const totalSeats = (l: Dict) => book.tiers.reduce((sum: number, t: Dict) => sum + (Number(l.seats[t.code]) || 0), 0);

  return (
    <div className="page">
      <Section title="票价" hint="每个价格段 × 票档一个价格（元）。遮挡票档留空时自动按原票档减价（灰色数字）。">
        <table className="grid">
          <thead>
            <tr>
              <th>价格段</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {book.bands.map((b: Dict) => (
              <tr key={b.code}>
                <th scope="row">{b.name}</th>
                {book.tiers.map((t: Dict) => {
                  const p = shownPrice(book, b.code, t);
                  return (
                    <td key={t.code}>
                      <Cell
                        label={`票价 ${b.name} ${t.name}`}
                        type="number"
                        value={p.derived ? "" : p.value}
                        placeholder={p.derived ? yuan(p.value) : ""}
                        onCommit={(v) => set(["prices", b.code, t.code], v === "" ? null : v)}
                        width={90}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {!book.bands.length && <p className="hint">先在“赛事与场次”里添加价格段和票档。</p>}
      </Section>

      <Section title="座席布局" hint="每种场地布局下，每个票档有多少座位（还没扣除转播、安保等占用，占用在“座位分配”里设）。">
        <table className="grid">
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
              <th>合计</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.layouts.map((l: Dict) => (
              <tr key={l.code}>
                <td>
                  <Cell label={`布局代码 ${l.code}`} value={l.code} onCommit={(v) => edit([{ op: "rename", list: "layouts", key: l.code, to: v }])} width={80} />
                </td>
                <td>
                  <Cell label={`布局名称 ${l.code}`} value={l.name} onCommit={(v) => set(["layouts", l.code, "name"], v)} />
                </td>
                {book.tiers.map((t: Dict) => (
                  <td key={t.code}>
                    <Cell label={`座席 ${l.name} ${t.name}`} type="number" value={l.seats[t.code]} onCommit={(v) => set(["layouts", l.code, "seats", t.code], v === "" ? null : v.trim())} width={80} />
                  </td>
                ))}
                <td className="num">{totalSeats(l).toLocaleString()}</td>
                <td>
                  <button className="link danger" onClick={() => edit([{ op: "remove", list: "layouts", key: l.code }])}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={() => edit([{ op: "add", list: "layouts", item: { code: nextLayout(), name: "新布局", seats: {} } }])}>添加布局</button>
      </Section>
    </div>
  );
}
