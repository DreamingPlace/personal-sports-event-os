import { useEffect, useState, type ReactNode } from "react";

/** A text or number box that saves when you leave it or press Enter, and only if the value changed. */
export function Cell({
  value,
  onCommit,
  label,
  type = "text",
  placeholder,
  width,
}: {
  value: any;
  onCommit: (v: string) => void;
  label: string;
  type?: "text" | "number" | "date" | "time" | "datetime-local";
  placeholder?: string;
  width?: number;
}) {
  const shown = value === null || value === undefined ? "" : String(value);
  const [text, setText] = useState(shown);
  useEffect(() => setText(shown), [shown]);
  const commit = () => {
    if (text !== shown) onCommit(text);
  };
  return (
    <input
      className="cell"
      aria-label={label}
      type={type === "number" ? "text" : type}
      inputMode={type === "number" ? "decimal" : undefined}
      value={text}
      placeholder={placeholder}
      style={width ? { width } : undefined}
      onChange={(e) => setText(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        if (e.key === "Escape") setText(shown);
      }}
    />
  );
}

export function Section({ title, hint, actions, children }: { title: string; hint?: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="section">
      <header>
        <div>
          <h2>{title}</h2>
          {hint && <p className="hint">{hint}</p>}
        </div>
        {actions && <div className="actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

export function Problems({ problems }: { problems: { level: string; where: string; message: string }[] }) {
  if (!problems.length) return <p className="ok-line">✓ 没有发现问题</p>;
  return (
    <ul className="problems" aria-label="问题列表">
      {problems.map((p, i) => (
        <li key={i} className={p.level}>
          <strong>{p.level === "error" ? "错误" : "提醒"}</strong> {p.message}
        </li>
      ))}
    </ul>
  );
}

export function Confirm({
  title,
  children,
  onConfirm,
  onCancel,
  confirmText = "确认",
}: {
  title: string;
  children: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
  confirmText?: string;
}) {
  return (
    <div className="overlay" role="presentation" onClick={onCancel}>
      <div className="dialog" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <div className="dialog-body">{children}</div>
        <div className="dialog-actions">
          <button onClick={onCancel}>取消</button>
          <button className="primary" onClick={onConfirm}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

let counter = 0;
/** A short unique id for new buckets/products. */
export function newId(prefix: string): string {
  counter += 1;
  return `${prefix}${Date.now().toString(36)}${counter}`;
}
