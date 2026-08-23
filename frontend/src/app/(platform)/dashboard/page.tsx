"use client";

import Link from "next/link";

import {
  ArrowUpRight,
  BookOpen,
  Bot,
  Database,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import {
  ParticleSphere,
} from "../../../components/effects/particle-sphere";

import {
  PageTransition,
} from "../../../components/layout/page-transition";

import {
  useAuth,
} from "../../../hooks/use-auth";

import {
  useWorkspace,
} from "../../../hooks/use-workspace";

export default function DashboardPage() {
  const {
    user,
  } = useAuth();

  const {
    activeWorkspace,
    settings,
    isSettingsLoading,
  } = useWorkspace();

  const firstName =
    user?.full_name
      ?.trim()
      .split(" ")[0] ||
    "there";

  const assistantName =
    isSettingsLoading
      ? "Loading assistant"
      : settings?.assistant_name ||
        "AI Knowledge Assistant";

  const knowledgeEnabled =
    activeWorkspace
      ?.enabled_modules
      .includes(
        "ai_knowledge_assistant"
      ) ?? false;

  return (
    <PageTransition className="platform-page dashboard-page">
      <section className="dashboard-intro">
        <div>
          <span className="platform-eyebrow">
            <Sparkles size={14} />

            Workspace intelligence
          </span>

          <h1>
            Welcome back,
            <span>
              {" "}
              {firstName}.
            </span>
          </h1>
        </div>

        <p>
          Your secure company workspace
          is connected and ready.
        </p>
      </section>

      <section className="dashboard-hero">
        <div className="dashboard-hero__grid" />

        <div className="dashboard-hero__ambient dashboard-hero__ambient--one" />

        <div className="dashboard-hero__ambient dashboard-hero__ambient--two" />

        <div className="dashboard-hero__content">
          <span className="dashboard-hero__company">
            {activeWorkspace
              ?.company_name ||
              "Company workspace"}
          </span>

          <h2>
            Company knowledge,
            <span>
              {" "}
              alive and in motion.
            </span>
          </h2>

          <p>
            AI Agency transforms documents,
            internal information and
            company context into trusted
            answers inside one secure,
            isolated workspace.
          </p>

          <div className="dashboard-hero__actions">
            <Link
              href="/assistant"
              className="dashboard-primary-action"
            >
              Open assistant

              <ArrowUpRight size={17} />
            </Link>

            <Link
              href="/knowledge"
              className="dashboard-secondary-action"
            >
              Explore knowledge
            </Link>
          </div>

          <div className="dashboard-hero__status">
            <span>
              <span className="dashboard-status-dot" />

              System active
            </span>

            <span>
              <ShieldCheck size={14} />

              Workspace isolated
            </span>
          </div>
        </div>

        <div className="dashboard-hero__visual">
          <div className="dashboard-sphere-aura" />

          <ParticleSphere />

          <div className="dashboard-interface-line dashboard-interface-line--one" />

          <div className="dashboard-interface-line dashboard-interface-line--two" />

          <div className="dashboard-sphere-label dashboard-sphere-label--top">
            <span>
              System state
            </span>

            <strong>
              Responsive
            </strong>
          </div>

          <div className="dashboard-sphere-label dashboard-sphere-label--bottom">
            <span>
              Intelligence engine
            </span>

            <strong>
              Connected
            </strong>
          </div>
        </div>
      </section>

      <section className="dashboard-metrics">
        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <Database size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Workspace
            </span>

            <strong>
              {activeWorkspace?.name ||
                "Company workspace"}
            </strong>
          </div>

          <small className="dashboard-metric-card__state">
            Active
          </small>
        </article>

        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <Bot size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Assistant
            </span>

            <strong>
              {assistantName}
            </strong>
          </div>

          <small className="dashboard-metric-card__state">
            Ready
          </small>
        </article>

        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <BookOpen size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Knowledge module
            </span>

            <strong>
              AI Knowledge Assistant
            </strong>
          </div>

          <small
            className={[
              "dashboard-metric-card__state",
              !knowledgeEnabled
                ? "dashboard-metric-card__state--disabled"
                : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {knowledgeEnabled
              ? "Enabled"
              : "Unavailable"}
          </small>
        </article>
      </section>
    </PageTransition>
  );
}
