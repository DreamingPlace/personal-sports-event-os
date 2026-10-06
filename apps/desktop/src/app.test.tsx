/**
 * End-to-end through the real Python sidecar (invented example data only):
 * the UI calls `invoke`, which is wired to a `python -m ticketbook.desktop` child process.
 */
import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen, within, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
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
vi.mock("@tauri-apps/plugin-dialog", () => ({
  save: async ({ defaultPath }: { defaultPath?: string }) => join(dir, defaultPath || "out"),
  open: async () => join(dir, "示例.ticketbook"),
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
  }, 60000);
});
