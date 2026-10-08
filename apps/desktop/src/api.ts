import { invoke } from "@tauri-apps/api/core";

export type Dict = Record<string, any>;

/** What the sidecar returns after every change: the whole book plus everything worked out from it. */
export type State = {
  path: string;
  book: Dict;
  ledger: Dict;
  forecast: Dict;
  live: Dict;
  damai: Dict;
  versions: { id: string; label: string; created_at: string }[];
  snapshots: { id: string; label: string; created_at: string; totals: Record<string, number> }[];
  log: { at: string; action: string; detail: string }[];
};

export type Change = { path: (string | number)[]; value: any };

export class BackendError extends Error {
  constructor(
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export async function call<T = any>(method: string, params: Dict = {}): Promise<T> {
  let response: Dict;
  try {
    response = await invoke<Dict>("sports_call", { method, params });
  } catch (e) {
    throw new BackendError("SIDECAR", "后台程序没有响应，请重新打开文件。" + (e ? ` (${String(e)})` : ""));
  }
  if (!response.ok) throw new BackendError(response.error.code, response.error.message);
  return response.result as T;
}

export const KIND_NAMES: Record<string, string> = {
  hold: "功能占用",
  comp: "权益/赠票",
  priority: "优先购",
  reserve: "预留",
};

export const PRODUCT_NAMES: Record<string, string> = {
  day: "一日通票",
  full: "全程通票",
  package: "旅行套票",
};

export const LINE_NAMES: Record<string, string> = {
  seats: "总座席",
  hold: "功能占用",
  sellable: "可售座席",
  comp: "权益/赠票",
  priority: "优先购",
  reserve: "预留",
  product: "通票/套票",
  public: "公开销售",
  sold: "公开已售",
  left: "剩余",
};

/** 1234567.5 → "1,234,567.5"; keeps exact decimal strings from the backend. */
export function yuan(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const [whole, frac] = String(v).split(".");
  const sign = whole.startsWith("-") ? "-" : "";
  const digits = whole.replace("-", "").replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const cents = frac ? frac.replace(/0+$/, "").slice(0, 2) : "";
  return sign + digits + (cents ? "." + cents : "");
}

export function num(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

export function bandName(book: Dict, code: string): string {
  return book.bands.find((b: Dict) => b.code === code)?.name || code;
}
