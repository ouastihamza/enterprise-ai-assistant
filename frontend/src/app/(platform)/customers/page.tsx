"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Building2,
  Factory,
  Loader2,
  Mail,
  MapPin,
  Plus,
  Sparkles,
  UserRound,
  X,
} from "lucide-react";

import { PageTransition } from "../../../components/layout/page-transition";
import { useWorkspace } from "../../../hooks/use-workspace";
import {
  createCustomer,
  listCustomers,
  seedDemoCustomer,
} from "../../../services/customers.service";
import type { Customer } from "../../../types/customer.types";

export default function CustomersPage() {
  const { activeWorkspace } = useWorkspace();
  const workspaceId = activeWorkspace?.id;
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasDemoCustomer = customers.some(
    (customer) => customer.company_name === "Demo Industrie SAS"
  );

  const loadCustomers = useCallback(async () => {
    if (!workspaceId) return;
    setIsLoading(true);
    setError(null);
    try {
      setCustomers(await listCustomers(workspaceId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Couldn't load customers.");
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    void loadCustomers();
  }, [loadCustomers]);

  const seedDemo = async () => {
    if (!workspaceId || isSeeding) return;
    setIsSeeding(true);
    setError(null);
    try {
      await seedDemoCustomer(workspaceId);
      await loadCustomers();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Couldn't prepare demo data.");
    } finally {
      setIsSeeding(false);
    }
  };

  const submitCustomer = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!workspaceId || isCreating) return;
    const form = new FormData(event.currentTarget);
    setIsCreating(true);
    setError(null);
    try {
      await createCustomer(workspaceId, {
        company_name: String(form.get("company_name") || ""),
        customer_reference: String(form.get("customer_reference") || ""),
        industry: String(form.get("industry") || "") || undefined,
        contact_name: String(form.get("contact_name") || "") || undefined,
        email: String(form.get("email") || "") || undefined,
      });
      setShowForm(false);
      await loadCustomers();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Couldn't create customer.");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <PageTransition className="platform-page customer-page">
      <section className="customer-page__heading">
        <div>
          <span className="platform-eyebrow"><Building2 size={14} /> Customer overview</span>
          <h1>Customers</h1>
          <p>Company details, sites, documents and AI answers in one place.</p>
        </div>
        <div className="customer-page__actions">
          {!hasDemoCustomer && (
            <button className="customer-button customer-button--secondary" onClick={() => void seedDemo()} disabled={isSeeding || !workspaceId}>
              {isSeeding ? <Loader2 size={16} className="assistant-spin" /> : <Sparkles size={16} />}
              {isSeeding ? "Creating demo…" : "Create fictional demo"}
            </button>
          )}
          <button className="customer-button" onClick={() => setShowForm(true)}>
            <Plus size={16} /> Add customer
          </button>
        </div>
      </section>

      {error && <div className="customer-alert">{error}</div>}

      {showForm && (
        <form className="customer-form-card" onSubmit={submitCustomer}>
          <div className="customer-form-card__header">
            <div><strong>New customer</strong><span>Add the essential details now; documents can be added from the customer profile.</span></div>
            <button type="button" onClick={() => setShowForm(false)} aria-label="Close"><X size={18} /></button>
          </div>
          <div className="customer-form-grid">
            <label>Company name<input name="company_name" required /></label>
            <label>Customer reference<input name="customer_reference" required /></label>
            <label>Industry<input name="industry" /></label>
            <label>Primary contact<input name="contact_name" /></label>
            <label>Email<input name="email" type="email" /></label>
          </div>
          <button className="customer-button" disabled={isCreating}>
            {isCreating && <Loader2 size={16} className="assistant-spin" />} Create customer
          </button>
        </form>
      )}

      {isLoading ? (
        <div className="customer-empty"><Loader2 className="assistant-spin" /> Loading customers…</div>
      ) : customers.length === 0 ? (
        <div className="customer-empty customer-empty--large">
          <div className="customer-empty__icon"><Building2 size={25} /></div>
          <h2>No customers yet</h2>
          <p>Create the fictional Demo Industrie SAS profile to explore the complete customer experience.</p>
          <button className="customer-button" onClick={() => void seedDemo()} disabled={isSeeding}>
            <Sparkles size={16} /> Create Demo Industrie SAS
          </button>
        </div>
      ) : (
        <section className="customer-grid">
          {customers.map((customer) => (
            <Link key={customer.id} href={`/customers/${customer.id}`} className="customer-card">
              <div className="customer-card__top">
                <div className="customer-logo"><Factory size={21} /></div>
                <span className="customer-status">{customer.status}</span>
              </div>
              <div><h2>{customer.company_name}</h2><span className="customer-reference">{customer.customer_reference}</span></div>
              <div className="customer-card__details">
                <span><Building2 size={15} /> {customer.industry || "Industry not set"}</span>
                <span><MapPin size={15} /> {customer.site_count} {customer.site_count === 1 ? "site" : "sites"}</span>
                <span><UserRound size={15} /> {customer.contact_name || "No primary contact"}</span>
                {customer.email && <span><Mail size={15} /> {customer.email}</span>}
              </div>
              <div className="customer-card__footer">Open customer profile <ArrowRight size={16} /></div>
            </Link>
          ))}
        </section>
      )}
    </PageTransition>
  );
}
