"use client";

import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Bot,
  Building2,
  CalendarRange,
  FileText,
  Gauge,
  Loader2,
  MapPin,
  ReceiptText,
  UploadCloud,
  Zap,
} from "lucide-react";

import { PageTransition } from "../../../../components/layout/page-transition";
import { useWorkspace } from "../../../../hooks/use-workspace";
import { getCustomer } from "../../../../services/customers.service";
import { uploadDocument } from "../../../../services/documents.service";
import type { CustomerDetail } from "../../../../types/customer.types";
import type { KnowledgeDocument } from "../../../../types/document.types";

const categories: KnowledgeDocument["category"][] = [
  "Contract", "Invoice", "Consumption", "Procedure", "Other",
];

export default function CustomerProfilePage() {
  const params = useParams<{ customerId: string }>();
  const customerId = params.customerId;
  const { activeWorkspace } = useWorkspace();
  const workspaceId = activeWorkspace?.id;
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [category, setCategory] = useState<KnowledgeDocument["category"]>("Other");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadCustomer = useCallback(async () => {
    if (!workspaceId || !customerId) return;
    setIsLoading(true);
    setError(null);
    try {
      setCustomer(await getCustomer(workspaceId, customerId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Couldn't load this customer.");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, customerId]);

  useEffect(() => { void loadCustomer(); }, [loadCustomer]);

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !workspaceId) return;
    setIsUploading(true);
    setError(null);
    try {
      await uploadDocument(workspaceId, file, { customerId, category });
      await loadCustomer();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  };

  if (isLoading) {
    return <PageTransition className="platform-page"><div className="customer-empty"><Loader2 className="assistant-spin" /> Loading customer profile…</div></PageTransition>;
  }

  if (!customer) {
    return <PageTransition className="platform-page"><div className="customer-empty"><h2>Customer unavailable</h2><p>{error}</p><Link href="/customers">Back to customers</Link></div></PageTransition>;
  }

  return (
    <PageTransition className="platform-page customer-profile">
      <Link href="/customers" className="customer-back"><ArrowLeft size={15} /> All customers</Link>
      <section className="customer-profile__hero">
        <div className="customer-profile__identity">
          <div className="customer-profile__logo"><Building2 size={26} /></div>
          <div><div className="customer-profile__kicker"><span className="customer-status">{customer.status}</span> {customer.customer_reference}</div><h1>{customer.company_name}</h1><p>{customer.industry || "Industry not specified"} · {customer.contact_name || "No primary contact"} · {customer.email || "No email"}</p></div>
        </div>
        <Link href={`/assistant?customer=${customer.id}`} className="customer-button"><Bot size={16} /> Ask Atlas</Link>
      </section>

      {error && <div className="customer-alert">{error}</div>}

      <section className="customer-profile__facts">
        <article><MapPin size={18} /><span>Sites</span><strong>{customer.sites.length}</strong><small>{customer.sites.map((site) => site.city).join(" · ") || "No sites"}</small></article>
        <article><Gauge size={18} /><span>Annual consumption</span><strong>{customer.sites.reduce((sum, site) => sum + (site.annual_consumption_mwh || 0), 0).toLocaleString()} MWh</strong><small>Across associated sites</small></article>
        <article><ReceiptText size={18} /><span>Latest invoice</span><strong>{customer.latest_invoice_summary?.match(/€[\d,]+/)?.[0] || "—"}</strong><small>February 2026</small></article>
        <article><CalendarRange size={18} /><span>Contract</span><strong>Current</strong><small>Through December 2028</small></article>
      </section>

      <section className="customer-summary-grid">
        <article className="customer-summary-card"><div><CalendarRange size={18} /><span>Contract</span></div><p>{customer.contract_summary || "No contract summary has been added."}</p></article>
        <article className="customer-summary-card"><div><ReceiptText size={18} /><span>Latest invoice</span></div><p>{customer.latest_invoice_summary || "No invoice summary has been added."}</p></article>
        <article className="customer-summary-card"><div><Zap size={18} /><span>Consumption</span></div><p>{customer.consumption_summary || "No consumption summary has been added."}</p></article>
      </section>

      <section className="customer-section">
        <div className="customer-section__heading"><div><span className="platform-eyebrow"><MapPin size={14} /> Portfolio</span><h2>Customer sites</h2></div></div>
        <div className="customer-sites">
          {customer.sites.length === 0 ? <div className="customer-empty">No sites have been added for this customer.</div> : customer.sites.map((site) => <article key={site.id}><div className="customer-site__icon"><Building2 size={18} /></div><div><strong>{site.site_name}</strong><span>{site.address || site.city}</span></div><small>{site.annual_consumption_mwh?.toLocaleString() || "—"} MWh/year</small></article>)}
        </div>
      </section>

      <section className="customer-section">
        <div className="customer-section__heading">
          <div><span className="platform-eyebrow"><FileText size={14} /> Documents</span><h2>Customer documents</h2></div>
          <div className="customer-upload-controls">
            <span className="customer-upload-controls__label">Document type</span>
            <select value={category} onChange={(event) => setCategory(event.target.value as KnowledgeDocument["category"])} aria-label="Document category">
              {categories.map((item) => <option key={item}>{item}</option>)}
            </select>
            <input ref={fileInputRef} type="file" hidden onChange={handleUpload} />
            <button className="customer-button customer-button--secondary" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
              {isUploading ? <Loader2 size={16} className="assistant-spin" /> : <UploadCloud size={16} />} Upload document
            </button>
          </div>
        </div>
        <div className="customer-documents">
          {customer.documents.length === 0 ? <div className="customer-empty">No documents have been added for this customer.</div> : customer.documents.map((document) => (
            <article key={document.id}><div className="customer-document__icon"><FileText size={18} /></div><div><strong>{document.name}</strong><span>Document type: {document.category}</span></div><span className="customer-status">{document.status}</span></article>
          ))}
        </div>
      </section>
    </PageTransition>
  );
}
