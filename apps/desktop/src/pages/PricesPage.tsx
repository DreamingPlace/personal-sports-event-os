import type { Dict } from "../api";
import { yuan } from "../api";
import type { PageProps } from "../App";
import { Fragment, useState } from "react";
import { Cell, Section } from "../ui";
import { SeatMapImport } from "./SeatMapImport";

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

export function PricesPage(props: PageProps) {
  const { state, edit } = props;
  const { book } = state;
  const [zonesOf, setZonesOf] = useState<string | null>(null);
  const set = (path: (string | number)[], value: any) => edit([{ op: "set", path, value }]);
  const nextLayout = () => {
    let i = book.layouts.length + 1;
    while (book.layouts.some((l: Dict) => l.code === "L" + i)) i += 1;
    return "L" + i;
  };
  const totalSeats = (l: Dict) => book.tiers.reduce((sum: number, t: Dict) => sum + (Number(l.seats[t.code]) || 0), 0);

  return (
    <div className="page">
      <Section title="票价" hint="每个比赛阶段 × 票档一个价格（元）。遮挡票档留空时自动按原票档减价（灰色数字）。">
        <table className="grid">
          <thead>
            <tr>
              <th>比赛阶段</th>
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
        {!book.bands.length && <p className="hint">先在“赛事与场次”里添加比赛阶段和票档。</p>}
      </Section>

      <Section
        title="座席布局"
        hint="每种场地布局下，每个票档有多少座位（还没扣除转播、安保等占用，占用在“座位分配”里设）。导入座位图后按区域记座位，各票档座位数自动合计。"
        actions={<SeatMapImport {...props} />}
      >
        <table className="grid">
          <thead>
            <tr>
              <th>名称</th>
              {book.tiers.map((t: Dict) => (
                <th key={t.code}>{t.name}</th>
              ))}
              <th>合计</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {book.layouts.map((l: Dict) => {
              const zoned = (l.zones || []).length > 0;
              return (
                <Fragment key={l.code}>
                  <tr>
                    <td>
                      <Cell label={`布局名称 ${l.code}`} value={l.name} onCommit={(v) => set(["layouts", l.code, "name"], v)} />
                    </td>
                    {book.tiers.map((t: Dict) => (
                      <td key={t.code}>
                        {zoned ? (
                          <span className="num">{(Number(l.seats[t.code]) || 0).toLocaleString()}</span>
                        ) : (
                          <Cell label={`座席 ${l.name} ${t.name}`} type="number" value={l.seats[t.code]} onCommit={(v) => set(["layouts", l.code, "seats", t.code], v === "" ? null : v.trim())} width={80} />
                        )}
                      </td>
                    ))}
                    <td className="num">{totalSeats(l).toLocaleString()}</td>
                    <td className="nowrap">
                      {zoned && (
                        <button className="link" onClick={() => setZonesOf(zonesOf === l.code ? null : l.code)}>
                          {zonesOf === l.code ? "收起" : `${l.zones.length} 个区域`}
                        </button>
                      )}{" "}
                      <button className="link danger" onClick={() => edit([{ op: "remove", list: "layouts", key: l.code }])}>
                        删除
                      </button>
                    </td>
                  </tr>
                  {zoned && zonesOf === l.code && (
                    <tr>
                      <td colSpan={book.tiers.length + 3}>
                        <ZoneTable layout={l} book={book} onChange={(zones) => set(["layouts", l.code, "zones"], zones)} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
        <button onClick={() => edit([{ op: "add", list: "layouts", item: { code: nextLayout(), name: "新布局", seats: {} } }])}>添加布局</button>
      </Section>
    </div>
  );
}

/** A layout's zones: name, tier and seats, each editable; the layout's seats per tier follow from them. */
function ZoneTable({ layout, book, onChange }: { layout: Dict; book: Dict; onChange: (zones: Dict[]) => void }) {
  const zones: Dict[] = layout.zones;
  const change = (i: number, patch: Dict) => onChange(zones.map((z, j) => (j === i ? { ...z, ...patch } : z)));
  return (
    <table className="grid">
      <thead>
        <tr>
          <th>区域</th>
          <th>票档</th>
          <th>座位数</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {zones.map((z, i) => (
          <tr key={`${z.name}-${i}`}>
            <td>
              <Cell label={`区域名称 ${z.name}`} value={z.name} onCommit={(v) => v.trim() && change(i, { name: v.trim() })} />
            </td>
            <td>
              <select aria-label={`区域票档 ${z.name}`} value={z.tier || ""} onChange={(e) => change(i, { tier: e.target.value })}>
                <option value="">（不计入）</option>
                {book.tiers.map((t: Dict) => (
                  <option key={t.code} value={t.code}>
                    {t.name}
                  </option>
                ))}
              </select>
            </td>
            <td>
              <Cell label={`区域座位数 ${z.name}`} type="number" value={z.seats} onCommit={(v) => change(i, { seats: Number(v) || 0 })} width={80} />
            </td>
            <td>
              <button className="link danger" onClick={() => onChange(zones.filter((_, j) => j !== i))}>
                删除
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
