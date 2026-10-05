import { Dict, moduleName } from "../api";
import { Empty, Status } from "../components";

/** Project identity and the approval state of every enabled module. */
export function OverviewPage({
  meta,
  workspace,
  enabled,
  modules,
  onOpenModule,
}: {
  meta: Dict | undefined;
  workspace: string;
  enabled: string[];
  modules: Record<string, Dict> | undefined;
  onOpenModule: (id: string) => void;
}) {
  return (
    <>
      <section className="overview-meta">
        <h2>{meta?.name}</h2>
        <dl>
          <dt>项目 ID</dt>
          <dd>
            <code>{meta?.id}</code>
          </dd>
          <dt>版本</dt>
          <dd>
            <code>{meta?.version}</code>
          </dd>
          <dt>状态</dt>
          <dd>
            <Status value={meta?.status} />
          </dd>
          <dt>时区</dt>
          <dd>{meta?.timezone}</dd>
          <dt>项目目录</dt>
          <dd>{workspace}</dd>
        </dl>
      </section>
      <div className="section-line">
        <h2>项目能力</h2>
        <span>{enabled.length} 个启用模块</span>
      </div>
      <table>
        <caption className="sr-only">启用模块状态</caption>
        <thead>
          <tr>
            <th>模块</th>
            <th>工作版本</th>
            <th>批准状态</th>
            <th>批准引用</th>
          </tr>
        </thead>
        <tbody>
          {enabled.map((id) => (
            <tr key={id}>
              <td>
                <button className="text-button" onClick={() => onOpenModule(id)}>
                  {moduleName(id)}
                </button>
                <small>{id}</small>
              </td>
              <td>
                <code>{modules?.[id]?.data_version}</code>
              </td>
              <td>
                <Status value={modules?.[id]?.status || "DRAFT"} />
              </td>
              <td>{modules?.[id]?.approval_ref || "尚未批准"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!enabled.length && (
        <Empty title="尚未选择能力模块">
          前往“能力模块”启用所需功能，不需要票务能力的赛事也可独立运行。
        </Empty>
      )}
    </>
  );
}
