"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import {
  ArrowUpRight,
  BookOpen,
  Building2,
  Database,
  FileClock,
  MessagesSquare,
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

import { listCustomers } from "../../../services/customers.service";
import { listDocuments } from "../../../services/documents.service";
import { listConversations } from "../../../services/conversation.service";
import type { KnowledgeDocument } from "../../../types/document.types";

export default function DashboardPage() {
  const {
    user,
  } = useAuth();

  const {
    activeWorkspace,
  } = useWorkspace();

  const firstName =
    user?.full_name
      ?.trim()
      .split(" ")[0] ||
    "there";

  const knowledgeEnabled =
    activeWorkspace
      ?.enabled_modules
      .includes(
        "ai_knowledge_assistant"
      ) ?? false;

  const [customerCount, setCustomerCount] = useState(0);
  const [documentCount, setDocumentCount] = useState(0);
  const [conversationCount, setConversationCount] = useState(0);
  const [recentDocuments, setRecentDocuments] = useState<KnowledgeDocument[]>([]);

  useEffect(() => {
    const workspaceId = activeWorkspace?.id;
    if (!workspaceId) return;
    let current = true;
    void Promise.all([
      listCustomers(workspaceId),
      listDocuments(workspaceId),
      listConversations(workspaceId, 50),
    ]).then(([customers, documents, conversations]) => {
      if (!current) return;
      setCustomerCount(customers.length);
      setDocumentCount(documents.length);
      setConversationCount(conversations.length);
      setRecentDocuments(documents.slice(0, 4));
    }).catch(() => {
      // The dashboard remains usable if one summary request fails.
    });
    return () => { current = false; };
  }, [activeWorkspace?.id]);

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
            answers inside one secure
            company workspace.
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

              Ready for questions
            </span>

            <span>
              <ShieldCheck size={14} />

              Customer data protected
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
              Customer information
            </span>

            <strong>
              Ready to explore
            </strong>
          </div>

          <div className="dashboard-sphere-label dashboard-sphere-label--bottom">
            <span>
              AI assistant
            </span>

            <strong>
              Ready
            </strong>
          </div>
        </div>
      </section>

      <section className="dashboard-metrics">
        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <Building2 size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Customers
            </span>

            <strong>
              {customerCount}
            </strong>
          </div>

          <small className="dashboard-metric-card__state">
            Profiles
          </small>
        </article>

        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <Database size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Documents
            </span>

            <strong>
              {documentCount}
            </strong>
          </div>

          <small className="dashboard-metric-card__state">
            Indexed
          </small>
        </article>

        <article className="dashboard-metric-card">
          <div className="dashboard-metric-card__icon">
            <MessagesSquare size={19} />
          </div>

          <div className="dashboard-metric-card__content">
            <span>
              Conversations
            </span>

            <strong>
              {conversationCount}
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
            {knowledgeEnabled ? "Available" : "Unavailable"}
          </small>
        </article>
      </section>

      <section className="dashboard-recent">
        <div className="dashboard-recent__heading">
          <div><span className="platform-eyebrow"><FileClock size={14} /> Documents</span><h2>Recent uploads</h2></div>
          <Link href="/knowledge">View all <ArrowUpRight size={15} /></Link>
        </div>
        <div className="dashboard-recent__list">
          {recentDocuments.length === 0 ? (
            <p>No documents uploaded yet.</p>
          ) : recentDocuments.map((document) => (
            <article key={document.id}>
              <BookOpen size={17} />
              <div><strong>{document.name}</strong><span>{document.category} · Ready for the assistant</span></div>
              <small>{document.status}</small>
            </article>
          ))}
        </div>
      </section>
    </PageTransition>
  );
}
