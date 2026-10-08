import { useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import type { Dict } from "../api";
import type { PageProps } from "../App";
import { Confirm } from "../ui";

type Zone = { name: string; seats: number; colour: number | null; sure: boolean; tier: string | null };
type Read = { zones: Zone[]; colours: { rgb: number[]; seats: number; legend: string }[]; total: number; ignored: number };

const rgb = (c: number[]) => `rgb(${c.join(",")})`;
const fileName = (p: string) => p.split(/[\\/]/).pop();

/** "导入座位图…": zones and seats from a seat sheet (Excel/PDF), tiers from a coloured picture, or either one alone. */
export function SeatMapImport({ state, edit, run }: PageProps) {
  const { book } = state;
  const [picking, setPicking] = useState(false);
  const [sheet, setSheet] = useState("");
  const [picture, setPicture] = useState("");
  const [reading, setReading] = useState(false);
  const [read, setRead] = useState<Read | null>(null);
  const [colourTier, setColourTier] = useState<Record<number, string>>({});
  const [target, setTarget] = useState("NEW");
  const [newName, setNewName] = useState("");

  const choose = async (kind: "sheet" | "picture") => {
    const filters = kind === "sheet" ? [{ name: "座位表", extensions: ["xlsx", "xlsm", "pdf"] }] : [{ name: "座位图片", extensions: ["png", "jpg", "jpeg", "webp"] }];
    const picked = await open({ multiple: false, filters });
    if (typeof picked === "string") (kind === "sheet" ? setSheet : setPicture)(picked);
  };

  const start = async () => {
    setReading(true);
    const result = await run("seatmap_read", { sheet, picture });
    setReading(false);
    if (!result) return;
    setRead({ ...result, zones: result.zones.map((z: Dict) => ({ ...z, tier: null })) });
    setColourTier({});
    setNewName(picture || sheet ? String(fileName(sheet || picture)).replace(/\.[^.]+$/, "") : "新布局");
    setPicking(false);
  };

  const tierOf = (z: Zone) => (z.tier !== null ? z.tier : z.colour !== null ? colourTier[z.colour] || "" : "");
  const updateZone = (i: number, change: Partial<Zone>) => setRead((r) => r && { ...r, zones: r.zones.map((z, j) => (j === i ? { ...z, ...change } : z)) });

  const byTier: Record<string, number> = {};
  for (const z of read?.zones || []) {
    const t = tierOf(z);
    byTier[t] = (byTier[t] || 0) + (Number(z.seats) || 0);
  }

  const save = async () => {
    if (!read) return;
    const zones = read.zones.map((z) => ({ name: z.name.trim(), tier: tierOf(z), seats: Number(z.seats) || 0 }));
    if (target === "NEW") {
      let i = book.layouts.length + 1;
      while (book.layouts.some((l: Dict) => l.code === "L" + i)) i += 1;
      await edit([{ op: "add", list: "layouts", item: { code: "L" + i, name: newName.trim() || "新布局", seats: {}, zones } }], "导入座位图");
    } else {
      await edit([{ op: "set", path: ["layouts", target, "zones"], value: zones }], "导入座位图");
    }
    setRead(null);
  };

  const tierSelect = (value: string, onChange: (v: string) => void, label: string) => (
    <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">（不计入）</option>
      {book.tiers.map((t: Dict) => (
        <option key={t.code} value={t.code}>
          {t.name}
        </option>
      ))}
    </select>
  );

  return (
    <>
      <button onClick={() => setPicking(true)}>导入座位图…</button>
      {picking && (
        <Confirm title="导入座位图" confirmText={reading ? "读取中…" : "读取"} onCancel={() => setPicking(false)} onConfirm={() => !reading && (sheet || picture) && start()}>
          <p className="hint">座位表（Excel 或 Excel 导出的 PDF，每个座位一个格子）给出区域名称和准确座位数；彩色座位图给出每个区域的票档颜色。两个都给最好，只给一个也可以。读取在本机进行。</p>
          <div className="row">
            <button onClick={() => choose("sheet")}>选择座位表…</button>
            <span className="muted">{sheet ? fileName(sheet) : "未选择"}</span>
            {sheet && (
              <button className="link" onClick={() => setSheet("")}>
                清除
              </button>
            )}
          </div>
          <div className="row">
            <button onClick={() => choose("picture")}>选择彩色座位图…</button>
            <span className="muted">{picture ? fileName(picture) : "未选择"}</span>
            {picture && (
              <button className="link" onClick={() => setPicture("")}>
                清除
              </button>
            )}
          </div>
        </Confirm>
      )}
      {read && (
        <Confirm title="核对座位图" confirmText={`保存 ${read.zones.length} 个区域`} onCancel={() => setRead(null)} onConfirm={save}>
          <p className="hint">
            共读到 {read.zones.length} 个区域、{read.total.toLocaleString()} 个座位{read.ignored ? `（另有 ${read.ignored} 个零散数字不像座位，已忽略）` : ""}。先给每种颜色选票档，个别区域可以单独改。黄色行是自动对不准的，请对照图片看一眼。
          </p>
          <div className="row">
            <label>
              保存到
              <select aria-label="保存到布局" value={target} onChange={(e) => setTarget(e.target.value)}>
                <option value="NEW">新布局</option>
                {book.layouts.map((l: Dict) => (
                  <option key={l.code} value={l.code}>
                    替换“{l.name}”的区域
                  </option>
                ))}
              </select>
            </label>
            {target === "NEW" && <input aria-label="新布局名称" value={newName} onChange={(e) => setNewName(e.target.value)} />}
          </div>
          {read.colours.length > 0 && (
            <table className="grid">
              <thead>
                <tr>
                  <th>颜色</th>
                  <th>图例</th>
                  <th>图上座位</th>
                  <th>票档</th>
                </tr>
              </thead>
              <tbody>
                {read.colours.map((c, i) => (
                  <tr key={i}>
                    <td>
                      <span className="swatch" style={{ background: rgb(c.rgb) }} />
                    </td>
                    <td className="text">{c.legend || "—"}</td>
                    <td>{c.seats.toLocaleString()}</td>
                    <td>{tierSelect(colourTier[i] || "", (v) => setColourTier({ ...colourTier, [i]: v }), `颜色 ${i + 1} 的票档`)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="hint">
            按票档合计：
            {Object.entries(byTier)
              .map(([t, n]) => `${book.tiers.find((x: Dict) => x.code === t)?.name || "不计入"} ${n.toLocaleString()}`)
              .join("，")}
          </p>
          <div className="scroll tall">
            <table className="grid">
              <thead>
                <tr>
                  <th>区域</th>
                  <th>座位数</th>
                  <th>颜色</th>
                  <th>票档</th>
                </tr>
              </thead>
              <tbody>
                {read.zones.map((z, i) => (
                  <tr key={i} className={z.colour !== null && !z.sure ? "missing" : undefined}>
                    <td>
                      <input aria-label={`区域名称 ${i + 1}`} value={z.name} onChange={(e) => updateZone(i, { name: e.target.value })} />
                    </td>
                    <td>
                      <input aria-label={`座位数 ${z.name}`} type="number" value={z.seats} onChange={(e) => updateZone(i, { seats: Number(e.target.value) })} style={{ width: 80 }} />
                    </td>
                    <td>{z.colour !== null && read.colours[z.colour] ? <span className="swatch" style={{ background: rgb(read.colours[z.colour].rgb) }} /> : "—"}</td>
                    <td>{tierSelect(tierOf(z), (v) => updateZone(i, { tier: v }), `票档 ${z.name}`)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Confirm>
      )}
    </>
  );
}
