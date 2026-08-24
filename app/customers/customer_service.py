from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

from app.config import DB_DSN


class CustomerService:
    """Small PostgreSQL repository with workspace isolation in every query."""

    CREATE_TABLES_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_customers (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        company_name TEXT NOT NULL,
        customer_reference TEXT NOT NULL,
        industry TEXT,
        contact_name TEXT,
        email TEXT,
        status TEXT NOT NULL DEFAULT 'Active',
        notes TEXT,
        contract_summary TEXT,
        latest_invoice_summary TEXT,
        consumption_summary TEXT,
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL,
        UNIQUE(workspace_id, customer_reference)
    );

    CREATE TABLE IF NOT EXISTS tbl_customer_sites (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        customer_id TEXT NOT NULL REFERENCES tbl_customers(id) ON DELETE CASCADE,
        site_name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT,
        annual_consumption_mwh NUMERIC,
        created_at TIMESTAMPTZ NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_customers_workspace
    ON tbl_customers(workspace_id);

    CREATE INDEX IF NOT EXISTS idx_customer_sites_customer
    ON tbl_customer_sites(workspace_id, customer_id);
    """

    def __init__(self, workspace_id: str, dsn: Optional[str] = None):
        if not workspace_id.strip():
            raise ValueError("workspace_id cannot be empty.")
        self.workspace_id = workspace_id
        self.dsn = dsn or DB_DSN
        self._ensure_tables()

    def _get_conn(self):
        return psycopg2.connect(self.dsn)

    def _ensure_tables(self) -> None:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(self.CREATE_TABLES_SQL)

    @staticmethod
    def _format_datetime(value) -> str | None:
        return value.isoformat() if value else None

    def _customer_to_dict(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "workspace_id": row["workspace_id"],
            "company_name": row["company_name"],
            "customer_reference": row["customer_reference"],
            "industry": row.get("industry"),
            "contact_name": row.get("contact_name"),
            "email": row.get("email"),
            "status": row.get("status") or "Active",
            "notes": row.get("notes"),
            "contract_summary": row.get("contract_summary"),
            "latest_invoice_summary": row.get("latest_invoice_summary"),
            "consumption_summary": row.get("consumption_summary"),
            "created_at": self._format_datetime(row.get("created_at")),
            "updated_at": self._format_datetime(row.get("updated_at")),
        }

    @staticmethod
    def _site_to_dict(row: dict) -> dict:
        consumption = row.get("annual_consumption_mwh")
        return {
            "id": row["id"],
            "customer_id": row["customer_id"],
            "site_name": row["site_name"],
            "city": row["city"],
            "address": row.get("address"),
            "annual_consumption_mwh": float(consumption) if consumption is not None else None,
        }

    def create_customer(
        self,
        *,
        company_name: str,
        customer_reference: str,
        industry: str | None = None,
        contact_name: str | None = None,
        email: str | None = None,
        status: str = "Active",
        notes: str | None = None,
        contract_summary: str | None = None,
        latest_invoice_summary: str | None = None,
        consumption_summary: str | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        try:
            with self._get_conn() as connection:
                with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO tbl_customers (
                            id, workspace_id, company_name, customer_reference,
                            industry, contact_name, email, status, notes,
                            contract_summary, latest_invoice_summary,
                            consumption_summary, created_at, updated_at
                        ) VALUES (
                            gen_random_uuid()::text, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING *
                        """,
                        (
                            self.workspace_id, company_name.strip(), customer_reference.strip(),
                            industry, contact_name, email, status, notes, contract_summary,
                            latest_invoice_summary, consumption_summary, now, now,
                        ),
                    )
                    row = cursor.fetchone()
        except psycopg2.errors.UniqueViolation as error:
            raise ValueError("Customer reference already exists in this workspace.") from error
        return self._customer_to_dict(row)

    def list_customers(self) -> list[dict]:
        with self._get_conn() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT c.*, COUNT(s.id)::int AS site_count
                    FROM tbl_customers c
                    LEFT JOIN tbl_customer_sites s
                      ON s.customer_id = c.id AND s.workspace_id = c.workspace_id
                    WHERE c.workspace_id = %s
                    GROUP BY c.id
                    ORDER BY c.company_name
                    """,
                    (self.workspace_id,),
                )
                rows = cursor.fetchall()
        customers = []
        for row in rows:
            customer = self._customer_to_dict(row)
            customer["site_count"] = row["site_count"]
            customers.append(customer)
        return customers

    def get_customer(self, customer_id: str) -> dict | None:
        with self._get_conn() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM tbl_customers WHERE id = %s AND workspace_id = %s",
                    (customer_id, self.workspace_id),
                )
                row = cursor.fetchone()
        return self._customer_to_dict(row) if row else None

    def get_customer_by_reference(self, customer_reference: str) -> dict | None:
        with self._get_conn() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """SELECT * FROM tbl_customers
                    WHERE workspace_id = %s AND customer_reference = %s""",
                    (self.workspace_id, customer_reference),
                )
                row = cursor.fetchone()
        return self._customer_to_dict(row) if row else None

    def add_site(
        self,
        *,
        customer_id: str,
        site_name: str,
        city: str,
        address: str | None = None,
        annual_consumption_mwh: float | None = None,
    ) -> dict:
        if self.get_customer(customer_id) is None:
            raise ValueError("Customer not found in this workspace.")
        with self._get_conn() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tbl_customer_sites (
                        id, workspace_id, customer_id, site_name, city,
                        address, annual_consumption_mwh, created_at
                    ) VALUES (gen_random_uuid()::text, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        self.workspace_id, customer_id, site_name.strip(), city.strip(),
                        address, annual_consumption_mwh, datetime.now(timezone.utc),
                    ),
                )
                row = cursor.fetchone()
        return self._site_to_dict(row)

    def list_sites(self, customer_id: str) -> list[dict]:
        with self._get_conn() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM tbl_customer_sites
                    WHERE workspace_id = %s AND customer_id = %s
                    ORDER BY site_name
                    """,
                    (self.workspace_id, customer_id),
                )
                rows = cursor.fetchall()
        return [self._site_to_dict(row) for row in rows]

    def build_assistant_context(self, customer_id: str) -> str | None:
        customer = self.get_customer(customer_id)
        if customer is None:
            return None
        sites = self.list_sites(customer_id)
        lines = [
            f"Company: {customer['company_name']}",
            f"Customer reference: {customer['customer_reference']}",
            f"Industry: {customer['industry'] or 'Not provided'}",
            f"Status: {customer['status']}",
            f"Primary contact: {customer['contact_name'] or 'Not provided'} ({customer['email'] or 'no email'})",
            f"Contract summary: {customer['contract_summary'] or 'Not provided'}",
            f"Latest invoice summary: {customer['latest_invoice_summary'] or 'Not provided'}",
            f"Consumption summary: {customer['consumption_summary'] or 'Not provided'}",
            f"Notes: {customer['notes'] or 'None'}",
            "Sites:",
        ]
        for site in sites:
            consumption = site["annual_consumption_mwh"]
            suffix = f", {consumption:,.0f} MWh/year" if consumption is not None else ""
            lines.append(f"- {site['site_name']}, {site['city']}{suffix}")
        return "\n".join(lines)

    def seed_demo_customer(self) -> tuple[dict, bool]:
        reference = "DEMO-FR-2026-001"
        existing = self.get_customer_by_reference(reference)
        if existing:
            now = datetime.now(timezone.utc)
            with self._get_conn() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE tbl_customers
                        SET contract_summary = %s,
                            latest_invoice_summary = %s,
                            consumption_summary = %s,
                            updated_at = %s
                        WHERE id = %s AND workspace_id = %s
                        """,
                        (
                            "36-month multi-site electricity agreement, January 2026 to December 2028, with an illustrative fixed energy rate of €80/MWh.",
                            "February 2026: €12,900 for 130 MWh, up €2,900 (29%) from January at €10,000 for 100 MWh. The energy rate remained €80/MWh.",
                            "January usage was 100 MWh. February usage was 130 MWh (+30%) after an additional production shift at Lille. Illustrative annual consumption is 1,440 MWh across three sites.",
                            now,
                            existing["id"],
                            self.workspace_id,
                        ),
                    )
                    cursor.execute(
                        """
                        UPDATE tbl_customer_sites
                        SET annual_consumption_mwh = CASE site_name
                            WHEN 'Paris Operations' THEN 480
                            WHEN 'Lyon Production' THEN 600
                            WHEN 'Lille Distribution' THEN 360
                            ELSE annual_consumption_mwh
                        END
                        WHERE customer_id = %s AND workspace_id = %s
                        """,
                        (existing["id"], self.workspace_id),
                    )
            return self.get_customer(existing["id"]), False
        customer = self.create_customer(
            company_name="Demo Industrie SAS",
            customer_reference=reference,
            industry="Manufacturing",
            contact_name="Camille Martin",
            email="camille.martin@example.com",
            status="Active",
            notes="Fictional demonstration account. All figures are illustrative.",
            contract_summary="36-month multi-site electricity agreement, January 2026 to December 2028, with an illustrative fixed energy rate of €80/MWh.",
            latest_invoice_summary="February 2026: €12,900 for 130 MWh, up €2,900 (29%) from January at €10,000 for 100 MWh. The energy rate remained €80/MWh.",
            consumption_summary="January usage was 100 MWh. February usage was 130 MWh (+30%) after an additional production shift at Lille. Illustrative annual consumption is 1,440 MWh across three sites.",
        )
        for site in (
            ("Paris Operations", "Paris", "12 avenue de la Démonstration", 480),
            ("Lyon Production", "Lyon", "8 rue de l'Exemple", 600),
            ("Lille Distribution", "Lille", "4 boulevard du Prototype", 360),
        ):
            self.add_site(
                customer_id=customer["id"], site_name=site[0], city=site[1],
                address=site[2], annual_consumption_mwh=site[3],
            )
        return customer, True
