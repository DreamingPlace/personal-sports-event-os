import { useState } from "react";
import { Dict } from "../api";
import { ModuleList } from "../pages/ModulesPage";

const PROFILE_LABELS: Dict = {
  "": "Blank · 空项目",
  "non-ticketed-event": "Non-ticketed Event · 非票务赛事",
  "ticketed-indoor-event": "Ticketed Indoor Event · 室内票务",
  "multi-session-tournament": "Multi-session Tournament · 多场次",
};

/** New-project wizard: identity → optional preset → module selection. */
export function Wizard({
  modules,
  profiles,
  busy,
  onCreate,
}: {
  modules: Dict[];
  profiles: Dict;
  busy: boolean;
  onCreate: (p: Dict) => void;
}) {
  const [step, setStep] = useState(1),
    [identity, setIdentity] = useState({
      id: "",
      name: "",
      timezone: "Asia/Singapore",
    }),
    [profile, setProfile] = useState(""),
    [selected, setSelected] = useState<string[]>([]);
  return (
    <div className="wizard">
      <p className="step-label">
        {step} / 3 · {["项目身份", "选择预设", "能力模块"][step - 1]}
      </p>
      {step === 1 ? (
        <>
          {(["name", "id", "timezone"] as const).map((k) => (
            <label className="field" key={k}>
              {
                { name: "项目名称", id: "项目 ID", timezone: "时区 Timezone" }[
                  k
                ]
              }
              <input
                value={identity[k]}
                onChange={(e) =>
                  setIdentity({ ...identity, [k]: e.target.value })
                }
              />
            </label>
          ))}
          <p className="muted">仅合成项目，不录入真实公司或个人数据。</p>
        </>
      ) : step === 2 ? (
        <fieldset>
          <legend>预设仅填写模块清单，可以继续调整</legend>
          {["", ...Object.keys(profiles)].map((k) => (
            <label className="profile-choice" key={k}>
              <input
                type="radio"
                name="profile"
                checked={profile === k}
                onChange={() => {
                  setProfile(k);
                  setSelected(profiles[k] || []);
                }}
              />
              {PROFILE_LABELS[k] || k}
            </label>
          ))}
        </fieldset>
      ) : (
        <div className="wizard-modules">
          <ModuleList
            modules={modules}
            selected={selected}
            busy={busy}
            onToggle={(id) =>
              setSelected(
                selected.includes(id)
                  ? selected.filter((k) => k !== id)
                  : [...selected, id],
              )
            }
          />
        </div>
      )}
      <div className="dialog-actions">
        {step > 1 && <button onClick={() => setStep(step - 1)}>上一步</button>}
        {step < 3 ? (
          <button
            className="primary"
            disabled={Object.values(identity).some((v) => !v.trim())}
            onClick={() => setStep(step + 1)}
          >
            下一步
          </button>
        ) : (
          <button
            className="primary"
            disabled={busy}
            onClick={() => onCreate({ identity, modules: selected })}
          >
            选择文件夹并创建
          </button>
        )}
      </div>
    </div>
  );
}
