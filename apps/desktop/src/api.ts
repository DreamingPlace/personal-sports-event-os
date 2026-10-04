import { invoke } from "@tauri-apps/api/core";
export type Dict = Record<string, any>;
export type Finding = {
  rule_id: string;
  severity: string;
  message: string;
  source: string;
  expected: unknown;
  actual: unknown;
  suggested_action: string;
};
export type Gate = { status: string; findings: Finding[] };
export type Workspace = {
  workspace: string;
  modified_at: string;
  project: {
    manifest: { project: Dict; modules: Record<string, boolean> };
    modules: Record<string, Dict>;
  };
  quality: Gate;
  release_quality: Gate;
  modules: Dict[];
};
export class BackendError extends Error {
  constructor(
    public code: string,
    message: string,
    public details: Dict = {},
  ) {
    super(message);
  }
}
export const sportsOS = {
  async call<T = any>(method: string, params: Dict = {}): Promise<T> {
    let response;
    try {
      response = await invoke<Dict>("sports_call", { method, params });
    } catch (e) {
      throw new BackendError(
        "SIDECAR",
        "后端连接不可用。请重新连接后打开项目。",
        { technical: String(e) },
      );
    }
    if (!response.ok)
      throw new BackendError(
        response.error.code,
        response.error.message,
        response.error.details,
      );
    return response.result as T;
  },
};
export const moduleName = (id: string) =>
  ({
    "core.schedule": "赛程 Schedule",
    "core.venue": "场馆 Venue",
    "ticketing.pricing": "票价 Pricing",
    "ticketing.seating": "座席 Seating",
    "ticketing.inventory": "库存 Inventory",
    "ticketing.rights": "付费权益 Rights",
    "finance.revenue": "收入 Revenue",
    "product.travel": "旅行包 Travel",
    "product.pass": "票务产品 Pass",
    "project.tasks": "任务 Tasks",
    "project.decisions": "决策 Decisions",
    "demand.multiplicative": "需求 Multiplicative",
    "demand.direct": "需求 Direct",
    "quality.declarations": "质量声明",
    "ticketing.refund": "退票规则",
    "ticketing.identity": "实名规则",
    "ticketing.transfer": "转票规则",
    "ticketing.launch": "开票规则",
    "ticketing.rights_return": "权益回流规则",
  })[id] || id;
export const display = (v: unknown) =>
  v === null || v === undefined
    ? "—"
    : typeof v === "object"
      ? JSON.stringify(v)
      : String(v);
