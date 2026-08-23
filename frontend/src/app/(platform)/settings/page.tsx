"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertCircle,
  Check,
  ChevronDown,
  Loader2,
  RotateCcw,
  Save,
  Sparkles,
} from "lucide-react";

import {
  PageTransition,
} from "../../../components/layout/page-transition";

import {
  useWorkspace,
} from "../../../hooks/use-workspace";

import {
  updateWorkspaceSettings,
} from "../../../services/workspace.service";

import type {
  WorkspaceSettings,
} from "../../../types/workspace.types";

const ALL_FILE_TYPES = [
  "pdf",
  "docx",
  "txt",
  "md",
  "csv",
  "xlsx",
  "html",
  "htm",
  "json",
  "xml",
  "pptx",
];

const MODEL_PRESETS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o mini" },
  { value: "gpt-4.1", label: "GPT-4.1" },
  { value: "o3-mini", label: "o3-mini (reasoning)" },
  { value: "custom", label: "Custom model..." },
];

const THEME_OPTIONS = ["light", "dark", "system"];

function settingsEqual(
  a: WorkspaceSettings,
  b: WorkspaceSettings
): boolean {
  return (
    a.assistant_name === b.assistant_name &&
    a.company_logo === b.company_logo &&
    a.primary_color === b.primary_color &&
    a.theme === b.theme &&
    a.welcome_message === b.welcome_message &&
    a.system_prompt === b.system_prompt &&
    a.llm_model === b.llm_model &&
    a.temperature === b.temperature &&
    a.chunk_size === b.chunk_size &&
    a.chunk_overlap === b.chunk_overlap &&
    a.top_k === b.top_k &&
    a.max_upload_size_mb === b.max_upload_size_mb &&
    a.allowed_file_types.length ===
      b.allowed_file_types.length &&
    a.allowed_file_types
      .slice()
      .sort()
      .every(
        (type, index) =>
          type ===
          b.allowed_file_types.slice().sort()[index]
      )
  );
}

const HEX_COLOR_PATTERN = /^#[0-9A-Fa-f]{6}$/;

export default function SettingsPage() {
  const {
    activeWorkspace,
    settings,
    refreshSettings,
  } = useWorkspace();

  const [form, setForm] =
    useState<WorkspaceSettings | null>(null);
  const [savedForm, setSavedForm] =
    useState<WorkspaceSettings | null>(null);
  const [isModelCustom, setIsModelCustom] =
    useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<
    string | null
  >(null);
  const [justSaved, setJustSaved] = useState(false);

  useEffect(() => {
    if (!settings) return;

    setForm(settings);
    setSavedForm(settings);
    setIsModelCustom(
      !MODEL_PRESETS.some(
        (preset) => preset.value === settings.llm_model
      )
    );
  }, [settings]);

  const isDirty = useMemo(() => {
    if (!form || !savedForm) return false;
    return !settingsEqual(form, savedForm);
  }, [form, savedForm]);

  const isValidColor =
    !form?.primary_color ||
    HEX_COLOR_PATTERN.test(form.primary_color);

  const isValidChunkConfig =
    !form ||
    form.chunk_overlap < form.chunk_size;

  const canSave =
    isDirty &&
    isValidColor &&
    isValidChunkConfig &&
    !isSaving;

  const toggleFileType = (type: string) => {
    setForm((current) => {
      if (!current) return current;

      const has =
        current.allowed_file_types.includes(type);

      return {
        ...current,
        allowed_file_types: has
          ? current.allowed_file_types.filter(
              (t) => t !== type
            )
          : [...current.allowed_file_types, type],
      };
    });
  };

  const updateField = <
    K extends keyof WorkspaceSettings
  >(
    key: K,
    value: WorkspaceSettings[K]
  ) => {
    setForm((current) =>
      current ? { ...current, [key]: value } : current
    );
  };

  const handleSave = async () => {
    if (!form || !canSave) return;

    setIsSaving(true);
    setSaveError(null);
    setJustSaved(false);

    try {
      const updated = await updateWorkspaceSettings(
        form
      );

      setForm(updated);
      setSavedForm(updated);
      await refreshSettings();

      setJustSaved(true);
      setTimeout(() => setJustSaved(false), 2500);
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : "Couldn't save your settings."
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (!savedForm) return;
    setForm(savedForm);
    setSaveError(null);
  };

  if (!form) {
    return (
      <PageTransition className="platform-page settings-page">
        <section className="dashboard-intro">
          <div>
            <span className="platform-eyebrow">
              <Sparkles size={14} />
              Workspace configuration
            </span>
            <h1>Settings</h1>
          </div>
        </section>

        <div className="settings-loading">
          <Loader2
            size={20}
            className="settings-spin"
          />
          Loading your settings...
        </div>

        <style jsx>{`
          .settings-loading {
            margin-top: 2rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            opacity: 0.6;
            font-size: 0.88rem;
          }

          .settings-spin {
            animation: settings-spin 0.8s linear infinite;
          }

          @keyframes settings-spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}</style>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="platform-page settings-page">
      <section className="dashboard-intro">
        <div>
          <span className="platform-eyebrow">
            <Sparkles size={14} />
            Workspace configuration
          </span>

          <h1>
            Settings
            <span>
              {" "}
              for{" "}
              {activeWorkspace?.company_name ||
                "your workspace"}
              .
            </span>
          </h1>
        </div>

        <p>
          Shape how your assistant introduces itself,
          what it can read, and how it reasons.
        </p>
      </section>

      <div className="settings-groups">
        <section className="settings-card">
          <div className="settings-card__header">
            <h2>Assistant identity</h2>
            <span>
              What people see when they open the
              assistant
            </span>
          </div>

          <label className="settings-field">
            <span>Assistant name</span>
            <input
              type="text"
              value={form.assistant_name}
              onChange={(event) =>
                updateField(
                  "assistant_name",
                  event.target.value
                )
              }
              placeholder="AI Knowledge Assistant"
            />
          </label>

          <label className="settings-field">
            <span>Welcome message</span>
            <textarea
              value={form.welcome_message}
              onChange={(event) =>
                updateField(
                  "welcome_message",
                  event.target.value
                )
              }
              rows={2}
              placeholder="Ask questions about your company's knowledge."
            />
          </label>

          <label className="settings-field">
            <span>Company logo URL</span>
            <input
              type="text"
              value={form.company_logo}
              onChange={(event) =>
                updateField(
                  "company_logo",
                  event.target.value
                )
              }
              placeholder="https://..."
            />
          </label>

          <div className="settings-field-row">
            <label className="settings-field">
              <span>Primary color</span>
              <div className="settings-color-field">
                <input
                  type="color"
                  value={
                    isValidColor
                      ? form.primary_color
                      : "#8d74d8"
                  }
                  onChange={(event) =>
                    updateField(
                      "primary_color",
                      event.target.value
                    )
                  }
                />
                <input
                  type="text"
                  value={form.primary_color}
                  onChange={(event) =>
                    updateField(
                      "primary_color",
                      event.target.value
                    )
                  }
                  placeholder="#8d74d8"
                  className={
                    !isValidColor
                      ? "settings-input--invalid"
                      : ""
                  }
                />
              </div>
              {!isValidColor && (
                <small className="settings-field__error">
                  Must be a hex color like #8d74d8.
                </small>
              )}
            </label>

            <label className="settings-field">
              <span>Theme</span>
              <div className="settings-select">
                <select
                  value={form.theme}
                  onChange={(event) =>
                    updateField(
                      "theme",
                      event.target.value
                    )
                  }
                >
                  {THEME_OPTIONS.map((theme) => (
                    <option key={theme} value={theme}>
                      {theme.charAt(0).toUpperCase() +
                        theme.slice(1)}
                    </option>
                  ))}
                </select>
                <ChevronDown size={15} />
              </div>
            </label>
          </div>
        </section>

        <section className="settings-card">
          <div className="settings-card__header">
            <h2>Knowledge behavior</h2>
            <span>
              How the assistant reasons over your
              documents
            </span>
          </div>

          <label className="settings-field">
            <span>System prompt</span>
            <textarea
              value={form.system_prompt}
              onChange={(event) =>
                updateField(
                  "system_prompt",
                  event.target.value
                )
              }
              rows={4}
              placeholder="You are a helpful assistant that only answers using the provided company context..."
            />
            <small>
              Leave blank to use the default assistant
              behavior.
            </small>
          </label>

          <label className="settings-field">
            <span>
              Retrieved chunks per question ·{" "}
              {form.top_k}
            </span>
            <input
              type="range"
              min={1}
              max={20}
              step={1}
              value={form.top_k}
              onChange={(event) =>
                updateField(
                  "top_k",
                  Number(event.target.value)
                )
              }
            />
            <small>
              More chunks give broader context but can
              dilute precision.
            </small>
          </label>

          <div className="settings-field-row">
            <label className="settings-field">
              <span>Chunk size · {form.chunk_size}</span>
              <input
                type="range"
                min={200}
                max={5000}
                step={100}
                value={form.chunk_size}
                onChange={(event) =>
                  updateField(
                    "chunk_size",
                    Number(event.target.value)
                  )
                }
              />
            </label>

            <label className="settings-field">
              <span>
                Chunk overlap · {form.chunk_overlap}
              </span>
              <input
                type="range"
                min={0}
                max={1000}
                step={50}
                value={form.chunk_overlap}
                onChange={(event) =>
                  updateField(
                    "chunk_overlap",
                    Number(event.target.value)
                  )
                }
              />
              {!isValidChunkConfig && (
                <small className="settings-field__error">
                  Chunk overlap must be smaller than
                  chunk size.
                </small>
              )}
            </label>
          </div>

          <label className="settings-field">
            <span>
              Max upload size (MB) ·{" "}
              {form.max_upload_size_mb}
            </span>
            <input
              type="number"
              min={1}
              max={10000}
              value={form.max_upload_size_mb}
              onChange={(event) =>
                updateField(
                  "max_upload_size_mb",
                  Number(event.target.value)
                )
              }
            />
          </label>

          <div className="settings-field">
            <span>Accepted file types</span>

            <div className="settings-file-types">
              {ALL_FILE_TYPES.map((type) => {
                const active =
                  form.allowed_file_types.includes(
                    type
                  );

                return (
                  <button
                    key={type}
                    type="button"
                    className={[
                      "settings-file-chip",
                      active
                        ? "settings-file-chip--active"
                        : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() =>
                      toggleFileType(type)
                    }
                  >
                    {active && <Check size={12} />}
                    .{type}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        <section className="settings-card">
          <div className="settings-card__header">
            <h2>Model configuration</h2>
            <span>
              Which model answers, and how it's tuned
            </span>
          </div>

          <label className="settings-field">
            <span>Model</span>

            <div className="settings-select">
              <select
                value={
                  isModelCustom
                    ? "custom"
                    : form.llm_model
                }
                onChange={(event) => {
                  const value = event.target.value;

                  if (value === "custom") {
                    setIsModelCustom(true);
                    return;
                  }

                  setIsModelCustom(false);
                  updateField("llm_model", value);
                }}
              >
                {MODEL_PRESETS.map((preset) => (
                  <option
                    key={preset.value}
                    value={preset.value}
                  >
                    {preset.label}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </div>

            {isModelCustom && (
              <input
                type="text"
                value={form.llm_model}
                onChange={(event) =>
                  updateField(
                    "llm_model",
                    event.target.value
                  )
                }
                placeholder="e.g. gpt-4.1-mini"
                className="settings-custom-model"
              />
            )}

            <small>
              Reasoning models (o-series) ignore
              temperature automatically.
            </small>
          </label>

          <label className="settings-field">
            <span>
              Temperature ·{" "}
              {form.temperature.toFixed(2)}
            </span>
            <input
              type="range"
              min={0}
              max={2}
              step={0.05}
              value={form.temperature}
              onChange={(event) =>
                updateField(
                  "temperature",
                  Number(event.target.value)
                )
              }
            />
            <small>
              Lower is more consistent, higher is more
              creative.
            </small>
          </label>
        </section>
      </div>

      <div className="settings-actionbar">
        {saveError && (
          <span className="settings-actionbar__error">
            <AlertCircle size={15} />
            {saveError}
          </span>
        )}

        {justSaved && !saveError && (
          <span className="settings-actionbar__success">
            <Check size={15} />
            Settings saved
          </span>
        )}

        <div className="settings-actionbar__buttons">
          <button
            type="button"
            className="settings-button settings-button--ghost"
            onClick={handleReset}
            disabled={!isDirty || isSaving}
          >
            <RotateCcw size={14} />
            Discard changes
          </button>

          <button
            type="button"
            className="settings-button settings-button--primary"
            onClick={handleSave}
            disabled={!canSave}
          >
            {isSaving ? (
              <Loader2
                size={14}
                className="settings-spin"
              />
            ) : (
              <Save size={14} />
            )}
            Save changes
          </button>
        </div>
      </div>

      <style jsx>{`
        .settings-groups {
          margin-top: 2rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .settings-card {
          border-radius: 16px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(148, 163, 184, 0.03);
          padding: 1.5rem 1.75rem;
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .settings-card__header {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
          margin-bottom: 0.25rem;
        }

        .settings-card__header h2 {
          font-size: 1rem;
          font-weight: 600;
        }

        .settings-card__header span {
          font-size: 0.8rem;
          opacity: 0.6;
        }

        .settings-field-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
        }

        .settings-field {
          display: flex;
          flex-direction: column;
          gap: 0.45rem;
        }

        .settings-field > span:first-child {
          font-size: 0.82rem;
          font-weight: 500;
          opacity: 0.85;
        }

        .settings-field input[type="text"],
        .settings-field input[type="number"],
        .settings-field textarea {
          background: rgba(148, 163, 184, 0.06);
          border: 1px solid rgba(148, 163, 184, 0.15);
          border-radius: 10px;
          padding: 0.6rem 0.75rem;
          font-size: 0.88rem;
          color: inherit;
          font-family: inherit;
          line-height: 1.5;
          resize: vertical;
        }

        .settings-field
          input[type="text"].settings-input--invalid {
          border-color: rgba(239, 68, 68, 0.6);
        }

        .settings-field input:focus,
        .settings-field textarea:focus,
        .settings-field select:focus {
          outline: none;
          border-color: rgba(129, 140, 248, 0.5);
        }

        .settings-field small {
          font-size: 0.75rem;
          opacity: 0.5;
        }

        .settings-field__error {
          color: rgb(248, 113, 113);
          opacity: 0.9 !important;
        }

        .settings-field input[type="range"] {
          width: 100%;
          accent-color: rgb(129, 140, 248);
        }

        .settings-color-field {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }

        .settings-color-field
          input[type="color"] {
          width: 42px;
          height: 38px;
          padding: 0;
          border-radius: 8px;
          border: 1px solid rgba(148, 163, 184, 0.15);
          background: none;
          cursor: pointer;
        }

        .settings-color-field
          input[type="text"] {
          flex: 1;
        }

        .settings-custom-model {
          margin-top: 0.4rem;
        }

        .settings-select {
          position: relative;
          display: flex;
          align-items: center;
        }

        .settings-select select {
          appearance: none;
          width: 100%;
          background: rgba(148, 163, 184, 0.06);
          border: 1px solid rgba(148, 163, 184, 0.15);
          border-radius: 10px;
          padding: 0.6rem 2.2rem 0.6rem 0.75rem;
          font-size: 0.88rem;
          color: inherit;
          font-family: inherit;
        }

        .settings-select :global(svg) {
          position: absolute;
          right: 0.75rem;
          pointer-events: none;
          opacity: 0.5;
        }

        .settings-file-types {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .settings-file-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          font-size: 0.78rem;
          padding: 0.4rem 0.7rem;
          border-radius: 8px;
          border: 1px solid rgba(148, 163, 184, 0.18);
          background: rgba(148, 163, 184, 0.04);
          color: inherit;
          opacity: 0.6;
          cursor: pointer;
          transition: opacity 0.15s ease,
            border-color 0.15s ease,
            background 0.15s ease;
        }

        .settings-file-chip--active {
          opacity: 1;
          border-color: rgba(129, 140, 248, 0.5);
          background: rgba(129, 140, 248, 0.1);
          color: rgb(129, 140, 248);
        }

        .settings-actionbar {
          position: sticky;
          bottom: 1rem;
          margin-top: 1.5rem;
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 1rem;
          padding: 0.85rem 1.25rem;
          border-radius: 14px;
          border: 1px solid rgba(148, 163, 184, 0.15);
          background: rgba(15, 15, 22, 0.75);
          backdrop-filter: blur(12px);
        }

        .settings-actionbar__error {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.82rem;
          color: rgb(248, 113, 113);
          margin-right: auto;
        }

        .settings-actionbar__success {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.82rem;
          color: rgb(74, 222, 128);
          margin-right: auto;
        }

        .settings-actionbar__buttons {
          display: flex;
          gap: 0.6rem;
        }

        .settings-button {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.82rem;
          font-weight: 500;
          padding: 0.55rem 1rem;
          border-radius: 9px;
          cursor: pointer;
          border: 1px solid transparent;
          transition: opacity 0.15s ease;
        }

        .settings-button:disabled {
          opacity: 0.35;
          cursor: default;
        }

        .settings-button--ghost {
          background: transparent;
          border-color: rgba(148, 163, 184, 0.2);
          color: inherit;
        }

        .settings-button--ghost:not(:disabled):hover {
          border-color: rgba(148, 163, 184, 0.4);
        }

        .settings-button--primary {
          background: rgb(129, 140, 248);
          color: #0b0b12;
        }

        .settings-button--primary:not(:disabled):hover {
          opacity: 0.9;
        }

        .settings-spin {
          animation: settings-spin 0.8s linear infinite;
        }

        @keyframes settings-spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .settings-spin {
            animation: none;
          }
        }

        @media (max-width: 640px) {
          .settings-field-row {
            grid-template-columns: 1fr;
          }

          .settings-actionbar {
            flex-direction: column;
            align-items: stretch;
          }

          .settings-actionbar__buttons {
            justify-content: flex-end;
          }
        }
      `}</style>
    </PageTransition>
  );
}