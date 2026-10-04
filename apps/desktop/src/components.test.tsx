import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GateView, Modal } from "./components";
import { ModuleEditor, SchemaField, blank } from "./Editor";
import { sportsOS } from "./api";
vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }));
import { invoke } from "@tauri-apps/api/core";

describe("authoritative boundary and controls", () => {
  for (const status of ["PASS", "WARNING", "BLOCK"])
    it("quality " + status, () => {
      render(
        <GateView
          gate={{
            status,
            findings:
              status === "PASS"
                ? []
                : [
                    {
                      rule_id: "SYNTHETIC",
                      severity: status,
                      message: "合成错误",
                      source: "core.schedule/rows/0",
                      expected: 100,
                      actual: 200,
                      suggested_action: "检查输入",
                    },
                  ],
          }}
        />,
      );
      expect(screen.getAllByText(status).length).toBeGreaterThan(0);
    });
  it("schema scaffold supports nested/null/boolean/enum", () =>
    expect(
      blank({
        type: "object",
        required: ["x", "y", "z"],
        properties: {
          x: { type: ["string", "null"] },
          y: { type: "boolean" },
          z: { enum: ["A", "B"] },
        },
      }),
    ).toEqual({ x: null, y: false, z: "A" }));
  it("numeric invalid state", () => {
    render(
      <SchemaField
        schema={{ type: "number" }}
        value="bad"
        onChange={() => {}}
        path="price"
      />,
    );
    expect(screen.getByLabelText("price")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
  });
  it("draft stays local, Escape reverts, Tab advances", async () => {
    const submit = vi.fn(),
      u = userEvent.setup();
    render(
      <ModuleEditor
        id="synthetic.module"
        schema={{
          type: "object",
          properties: { price: { type: "number" } },
          required: ["price"],
        }}
        data={{ price: 100 }}
        readOnly={false}
        onDirty={() => {}}
        onSubmit={submit}
      />,
    );
    const field = screen.getByLabelText("synthetic.module/price");
    await u.click(field);
    await u.clear(field);
    await u.type(field, "120");
    expect(submit).not.toHaveBeenCalled();
    expect(screen.getByText("未提交")).toBeVisible();
    await u.keyboard("{Escape}");
    expect(field).toHaveValue("100");
    await u.tab();
    expect(field).not.toHaveFocus();
  });
  it("snapshot editor exposes no write inputs", () => {
    render(
      <ModuleEditor
        id="synthetic.module"
        schema={{ type: "object", properties: { price: { type: "number" } } }}
        data={{ price: 100 }}
        readOnly
        onDirty={() => {}}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByText("提交工作数据")).toBeNull();
    expect(screen.getByText("100")).toBeVisible();
  });
  it("modal Escape closes and is named", async () => {
    const close = vi.fn();
    render(
      <Modal open title="确认" onClose={close}>
        <button>继续</button>
      </Modal>,
    );
    expect(screen.getByRole("dialog", { name: "确认" })).toBeVisible();
    fireEvent.keyDown(screen.getByText("继续"), { key: "Escape" });
    expect(close).toHaveBeenCalled();
  });
  it("transport preserves backend errors", async () => {
    vi.mocked(invoke).mockResolvedValue({
      ok: false,
      error: { code: "APPROVAL", message: "stale", details: {} },
    });
    await expect(sportsOS.call("approve_project")).rejects.toMatchObject({
      code: "APPROVAL",
      message: "stale",
    });
  });
  it("transport disconnect classifies SIDECAR", async () => {
    vi.mocked(invoke).mockRejectedValue(new Error("offline"));
    await expect(sportsOS.call("health")).rejects.toMatchObject({
      code: "SIDECAR",
    });
  });
});
