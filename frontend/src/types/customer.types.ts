import type { KnowledgeDocument } from "./document.types";

export interface CustomerSite {
  id: string;
  customer_id: string;
  site_name: string;
  city: string;
  address: string | null;
  annual_consumption_mwh: number | null;
}

export interface Customer {
  id: string;
  workspace_id: string;
  company_name: string;
  customer_reference: string;
  industry: string | null;
  contact_name: string | null;
  email: string | null;
  status: string;
  notes: string | null;
  contract_summary: string | null;
  latest_invoice_summary: string | null;
  consumption_summary: string | null;
  created_at: string | null;
  updated_at: string | null;
  site_count: number;
}

export interface CustomerDetail extends Customer {
  sites: CustomerSite[];
  documents: KnowledgeDocument[];
}

export interface CustomerCreate {
  company_name: string;
  customer_reference: string;
  industry?: string;
  contact_name?: string;
  email?: string;
  status?: string;
  notes?: string;
}

export interface DemoSeedResult {
  customer: CustomerDetail;
  created: boolean;
  documents_created: number;
}
