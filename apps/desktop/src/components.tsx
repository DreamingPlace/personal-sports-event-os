import { Dialog } from "@base-ui/react/dialog";
import type { ReactNode } from "react";
import { display, Gate } from "./api";
export function Status({ value }: { value: string }) {
  return <span className={`status ${value.toLowerCase()}`}>{value}</span>;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <section className="empty">
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}
export function Modal({
  title,
  open,
  onClose,
  children,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <Dialog.Root
      open={open}
      onOpenChange={(v) => {
        if (!v) onClose();
      }}
    >
      <Dialog.Portal>
        <Dialog.Backdrop className="backdrop" />
        <Dialog.Popup className="dialog">
          <Dialog.Title>{title}</Dialog.Title>
          <Dialog.Description className="sr-only">
            完成此对话框，或按 Escape 取消并返回。
          </Dialog.Description>
          {children}
          <Dialog.Close className="dialog-close" aria-label="关闭对话框">
            关闭
          </Dialog.Close>
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
export function GateView({
  gate,
  onLocate,
}: {
  gate: Gate;
  onLocate?: (source: string) => void;
}) {
  return (
    <section aria-label="质量检查结果">
      <div className="section-line">
        <Status value={gate.status} />
        <span>所有结果来自后端 Quality Gate</span>
      </div>
      {["BLOCK", "WARNING", "PASS"].map((severity) => (
        <section key={severity} className="gate-section">
          <h2>
            {
              {
                BLOCK: "阻断 Blocking",
                WARNING: "警告 Warnings",
                PASS: "通过 Passed",
              }[severity]
            }
          </h2>
          {severity === "PASS" ? (
            <p className="muted">
              {gate.findings.length === 0
                ? "当前检查未报告问题。不代表未提供的数据已获验证。"
                : "仅列出实际 Findings；不虚构逐条通过记录。"}
            </p>
          ) : gate.findings.filter((f) => f.severity === severity).length ===
            0 ? (
            <p className="muted">
              无{severity === "BLOCK" ? "阻断" : "警告"}项。
            </p>
          ) : (
            gate.findings
              .filter((f) => f.severity === severity)
              .map((f, i) => (
                <article className="finding" key={i}>
                  <div className="section-line">
                    <Status value={f.severity} />
                    <strong>{f.rule_id}</strong>
                    <span>{f.message}</span>
                  </div>
                  <dl>
                    <dt>Module</dt>
                    <dd>{f.source.split("/")[0]}</dd>
                    <dt>Source</dt>
                    <dd>
                      <code>{f.source}</code>
                    </dd>
                    <dt>Expected</dt>
                    <dd>{display(f.expected)}</dd>
                    <dt>Actual</dt>
                    <dd>{display(f.actual)}</dd>
                    <dt>建议操作</dt>
                    <dd>{f.suggested_action}</dd>
                  </dl>
                  {onLocate && (
                    <button onClick={() => onLocate(f.source)}>
                      定位模块 / 字段
                    </button>
                  )}
                </article>
              ))
          )}
        </section>
      ))}
    </section>
  );
}
