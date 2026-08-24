"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Building2,
  FileText,
  MessagesSquare,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { PageTransition } from "../../../components/layout/page-transition";
import { useAuth } from "../../../hooks/use-auth";
import { useWorkspace } from "../../../hooks/use-workspace";
import { listCustomers } from "../../../services/customers.service";
import { listDocuments } from "../../../services/documents.service";
import { listConversations } from "../../../services/conversation.service";
import type { Customer } from "../../../types/customer.types";
import type { KnowledgeDocument } from "../../../types/document.types";

export default function DashboardPage() {
  const { user } = useAuth();
  const { activeWorkspace } = useWorkspace();
  const firstName = user?.full_name?.trim().split(" ")[0] || "there";
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [documentCount, setDocumentCount] = useState(0);
  const [conversationCount, setConversationCount] = useState(0);
  const [recentDocuments, setRecentDocuments] = useState<KnowledgeDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const workspaceId = activeWorkspace?.id;
    if (!workspaceId) return;
    let current = true;
    void Promise.all([
      listCustomers(workspaceId),
      listDocuments(workspaceId),
      listConversations(workspaceId, 50),
    ])
      .then(([customerItems, documents, conversations]) => {
        if (!current) return;
        setCustomers(customerItems);
        setDocumentCount(documents.length);
        setConversationCount(conversations.length);
        setRecentDocuments(documents.slice(0, 4));
      })
      .finally(() => {
        if (current) setIsLoading(false);
      });
    return () => {
      current = false;
    };
  }, [activeWorkspace?.id]);

  const featuredCustomer =
    customers.find((customer) => customer.company_name === "Demo Industrie SAS") ||
    customers[0];

  return (
    <PageTransition className="platform-page dashboard-page atlas-dashboard">
      <section className="dashboard-intro atlas-dashboard__intro">
        <div>
          <span className="platform-eyebrow"><Sparkles size={14} /> Workspace overview</span>
          <h1>Good to see you, {firstName}.</h1>
          <p>Customer information, documents and grounded answers in one secure workspace.</p>
        </div>
        <Link href="/assistant" className="dashboard-primary-action">
          Ask Atlas <ArrowUpRight size={17} />
        </Link>
      </section>

      <section className="atlas-metrics" aria-label="Workspace metrics">
        <article><span>Customers</span><strong>{isLoading ? "—" : customers.length}</strong><Building2 size={18} /></article>
        <article><span>Documents</span><strong>{isLoading ? "—" : documentCount}</strong><FileText size={18} /></article>
        <article><span>Conversations</span><strong>{isLoading ? "—" : conversationCount}</strong><MessagesSquare size={18} /></article>
      </section>

      <section className="atlas-dashboard__grid">
        <article className="atlas-panel atlas-customer-focus">
          <div className="atlas-panel__heading">
            <div><span>Customer focus</span><h2>{featuredCustomer?.company_name || "No customer selected"}</h2></div>
            <Building2 size={20} />
          </div>
          {featuredCustomer ? (
            <>
              <dl>
                <div><dt>Reference</dt><dd>{featuredCustomer.customer_reference}</dd></div>
                <div><dt>Industry</dt><dd>{featuredCustomer.industry || "Not specified"}</dd></div>
                <div><dt>Sites</dt><dd>{featuredCustomer.site_count}</dd></div>
                <div><dt>Status</dt><dd>{featuredCustomer.status}</dd></div>
              </dl>
              <div className="atlas-panel__actions">
                <Link href={`/customers/${featuredCustomer.id}`}>Open customer</Link>
                <Link href={`/assistant?customer=${featuredCustomer.id}`}>Ask Atlas</Link>
              </div>
            </>
          ) : (
            <p className="atlas-panel__empty">Add a customer to bring company details and documents together.</p>
          )}
        </article>

        <article className="atlas-panel atlas-recent-documents">
          <div className="atlas-panel__heading">
            <div><span>Knowledge base</span><h2>Recent documents</h2></div>
            <ShieldCheck size={20} />
          </div>
          {recentDocuments.length > 0 ? (
            <div className="atlas-document-list">
              {recentDocuments.map((document) => (
                <div key={document.id}>
                  <FileText size={16} />
                  <span><strong>{document.name}</strong><small>{document.category} · {document.status}</small></span>
                </div>
              ))}
            </div>
          ) : (
            <p className="atlas-panel__empty">Uploaded and indexed documents will appear here.</p>
          )}
          <Link href="/knowledge" className="atlas-panel__link">View all documents <ArrowUpRight size={15} /></Link>
        </article>
      </section>
    </PageTransition>
  );
}
