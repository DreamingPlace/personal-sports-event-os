/**
 * End-to-end through the real Python sidecar (invented example data only):
 * the UI calls `invoke`, which is wired to a `python -m ticketbook.desktop` child process.
 */
import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { execFileSync, spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { createInterface } from "node:readline";

let child: ChildProcessWithoutNullStreams;
let dir: string;
let seq = 0;
const pending = new Map<string, (v: any) => void>();

vi.mock("@tauri-apps/api/core", () => ({
  invoke: (_cmd: string, args: any) =>
    new Promise((res) => {
      const id = String(++seq);
      pending.set(id, res);
      child.stdin.write(JSON.stringify({ id, method: args.method, params: args.params }) + "\n");
    }),
}));
const { picks } = vi.hoisted(() => ({ picks: [] as string[] }));
vi.mock("@tauri-apps/plugin-dialog", () => ({
  save: async ({ defaultPath }: { defaultPath?: string }) => join(dir, defaultPath || "out"),
  open: async () => picks.shift() ?? join(dir, "示例.ticketbook"),
}));

import App from "./App";

beforeAll(() => {
  dir = mkdtempSync(join(tmpdir(), "ticketbook-ui-"));
  child = spawn(process.env.PYTHON || "python3", ["-m", "ticketbook.desktop"], {
    env: { ...process.env, PYTHONPATH: resolve(__dirname, "../../../src") },
  });
  createInterface({ input: child.stdout }).on("line", (line) => {
    const r = JSON.parse(line);
    pending.get(r.id)?.(r);
    pending.delete(r.id);
  });
  child.stderr.on("data", () => {});
});
afterAll(() => {
  child.kill();
  rmSync(dir, { recursive: true, force: true });
});

describe("ticket book desktop", () => {
  it("creates an example book, edits, previews a forecast without changing data, then confirms", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "用示例数据试用" }));
    await user.click(screen.getByRole("button", { name: "选择保存位置" }));
    await user.type(screen.getByLabelText("密码"), "pw");
    await user.type(screen.getByLabelText("再输入一次密码"), "pw");
    await user.click(screen.getByRole("button", { name: "创建" }));
    await screen.findByRole("navigation", { name: "页面" }, { timeout: 15000 });
    expect(screen.getByText("没有问题")).toBeInTheDocument();

    // Prices: change one price; the value is saved to the file.
    await user.click(screen.getByRole("button", { name: "票价与座席" }));
    const price = screen.getByLabelText("票价 预赛 VIP");
    await user.clear(price);
    await user.type(price, "550{Enter}");
    await waitFor(() => expect(screen.getByLabelText("票价 预赛 VIP")).toHaveValue("550"));

    // Over-allocate one bucket: the sidebar shows the error.
    await user.click(screen.getByRole("button", { name: "座位分配" }));
    const reserve = screen.getByLabelText("海外平台 VIP 每场");
    await user.clear(reserve);
    await user.type(reserve, "5000{Enter}");
    await screen.findByText(/个错误/);
    await user.click(screen.getByRole("button", { name: "库存" }));
    expect(screen.getAllByText(/分配超出可售座席/).length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: "座位分配" }));
    const reserve2 = screen.getByLabelText("海外平台 VIP 每场");
    await user.clear(reserve2);
    await user.type(reserve2, "20{Enter}");
    await screen.findByText("没有问题");

    // Forecast: preview only, then confirm writes back and saves a version first.
    await user.click(screen.getByRole("button", { name: "票房测算" }));
    const fill = await screen.findByLabelText("其他场次上座率");
    await user.clear(fill);
    await user.type(fill, "80{Enter}");
    await screen.findByText("1 项修改（未写回）");
    await user.click(screen.getByRole("button", { name: "版本" }));
    expect(screen.getByText("还没有保存过版本。")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "票房测算" }));
    // Leaving the page drops the draft: the book still has 65.
    expect(await screen.findByLabelText("其他场次上座率")).toHaveValue("65");
    const fill2 = screen.getByLabelText("其他场次上座率");
    await user.clear(fill2);
    await user.type(fill2, "80{Enter}");
    await screen.findByText("1 项修改（未写回）");
    await waitFor(() => expect(screen.getByRole("button", { name: "确认写回…" })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "确认写回…" }));
    const dialog = await screen.findByRole("dialog", { name: "确认写回票务总表" });
    expect(within(dialog).getByText("其他场次 %")).toBeInTheDocument();
    await user.click(within(dialog).getByRole("button", { name: "确认写回" }));
    await screen.findByText("没有修改");
    await user.click(screen.getByRole("button", { name: "版本" }));
    expect(screen.getByText("测算写回前自动保存")).toBeInTheDocument();
    await user.type(screen.getByLabelText("原密码"), "wrong");
    await user.type(screen.getByLabelText("新密码"), "pw2");
    await user.type(screen.getByLabelText("再输一次新密码"), "pw2");
    await user.click(screen.getByRole("button", { name: "修改密码" }));
    expect(await screen.findByText("原密码不正确")).toBeInTheDocument();
    await user.clear(screen.getByLabelText("原密码"));
    await user.type(screen.getByLabelText("原密码"), "pw");
    await user.click(screen.getByRole("button", { name: "修改密码" }));
    expect(await screen.findByText("密码已修改")).toBeInTheDocument();

    // Inventory snapshot: save, change an allocation, compare, restore.
    await user.click(screen.getByRole("button", { name: "库存" }));
    await user.type(screen.getByLabelText("快照名称"), "开售前");
    await user.click(screen.getByRole("button", { name: "保存库存快照" }));
    expect(await screen.findByRole("rowheader", { name: "开售前" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "和现在比较" }));
    expect(await screen.findByText("没有变化")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "恢复" }));
    await user.click(within(await screen.findByRole("dialog", { name: "恢复库存快照" })).getByRole("button", { name: "恢复" }));
    expect(await screen.findByRole("rowheader", { name: "恢复前自动保存" })).toBeInTheDocument();

    // Damai sales: paste a copied table, check what was read, then save it.
    await user.click(screen.getByRole("button", { name: "大麦销售" }));
    await user.click(screen.getByLabelText("粘贴大麦表格"));
    await user.paste("\t100000001\t示例杯\t数量（张）\t2000\t500\t20\t1500\t25%\n\t金额（元）\t200000\t50000\t2000\t150000\n");
    await user.click(screen.getByRole("button", { name: "读取" }));
    await user.click(await screen.findByRole("button", { name: "保存这次记录" }));
    expect((await screen.findAllByText("25.00%")).length).toBeGreaterThan(0);

    // Live entry: type one session's figures; the day total and attendance rate follow.
    await user.click(screen.getByRole("button", { name: "现场入场" }));
    const checked = screen.getByLabelText("已验票数 S1");
    await user.type(checked, "900{Enter}");
    await user.type(screen.getByLabelText("总票数 S1"), "1000{Enter}");
    await waitFor(() => expect(screen.getAllByText("90.00%").length).toBeGreaterThan(0));

    // Reading a screenshot that cannot be opened: the check dialog says so and saves nothing.
    await user.click(screen.getByRole("button", { name: "读取截图…" }));
    const check = await screen.findByRole("dialog", { name: "核对截图读到的数字" }, { timeout: 30000 });
    expect(within(check).getByRole("button", { name: "保存 0 场" })).toBeInTheDocument();
    await user.click(within(check).getByRole("button", { name: "取消" }));

    // Seat map: read an invented seat sheet, give its zone a tier, save it as a new layout.
    const sheet = join(dir, "seats.xlsx");
    execFileSync(process.env.PYTHON || "python3", [
      "-c",
      "import sys\nfrom openpyxl import Workbook\nwb=Workbook(); ws=wb.active; ws.cell(row=1,column=2,value='东A区')\nfor r in range(2,5):\n    for c in range(2,8): ws.cell(row=r,column=c,value=c-1)\nwb.save(sys.argv[1])",
      sheet,
    ]);
    await user.click(screen.getByRole("button", { name: "票价与座席" }));
    await user.click(screen.getByRole("button", { name: "导入座位图…" }));
    picks.push(sheet);
    await user.click(screen.getByRole("button", { name: "选择座位表…" }));
    await screen.findByText("seats.xlsx");
    await user.click(screen.getByRole("button", { name: "读取" }));
    const seatDialog = await screen.findByRole("dialog", { name: "核对座位图" });
    await user.selectOptions(within(seatDialog).getByLabelText("票档 东A区"), "A");
    expect(within(seatDialog).getByText(/A档 18/)).toBeInTheDocument();
    await user.click(within(seatDialog).getByRole("button", { name: "保存 1 个区域" }));
    await user.click(await screen.findByRole("button", { name: "1 个区域" }));
    expect(screen.getByLabelText("区域座位数 东A区")).toHaveValue("18");

    // Setup from a planning sheet: an invented price table is recognised and imported.
    const plan = join(dir, "plan.xlsx");
    execFileSync(process.env.PYTHON || "python3", [
      "-c",
      "import sys\nfrom openpyxl import Workbook\nwb=Workbook(); ws=wb.active\nws.append(['票品','预赛','决赛'])\nws.append(['VIP',555,999])\nws.append(['A档',444,888])\nwb.save(sys.argv[1])",
      plan,
    ]);
    await user.click(screen.getByRole("button", { name: "赛事与场次" }));
    picks.push(plan);
    await user.click(screen.getByRole("button", { name: "从文件导入…" }));
    const importDialog = await screen.findByRole("dialog", { name: "从文件导入设置" });
    expect(within(importDialog).getByText("999")).toBeInTheDocument();
    await user.click(within(importDialog).getByRole("button", { name: "导入所选内容" }));
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "从文件导入设置" })).toBeNull());
    await user.click(screen.getByRole("button", { name: "票价与座席" }));
    expect(screen.getByLabelText("票价 预赛 VIP")).toHaveValue("555");

    // Reports: the field list shows numbers from the book.
    await user.click(screen.getByRole("button", { name: "报告", exact: true }));
    expect(await screen.findByRole("button", { name: "{{场次数}}" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("查找字段"), "开始日期");
    expect(await screen.findByText("12月1日")).toBeInTheDocument();
  }, 60000);
});
