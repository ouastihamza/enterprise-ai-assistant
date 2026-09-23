from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.auth.user_service import UserService
from app.customers.customer_service import CustomerService
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_registry import DocumentRegistry
from app.workspaces.workspace_service import WorkspaceService


router = APIRouter(
    prefix="/workspaces/{workspace_id}/customers",
    tags=["Customers"],
)

user_service = UserService()
workspace_service = WorkspaceService()


class CustomerCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    customer_reference: str = Field(min_length=1, max_length=100)
    industry: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    status: str = Field(default="Active", min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)
    contract_summary: str | None = Field(default=None, max_length=5000)
    latest_invoice_summary: str | None = Field(default=None, max_length=5000)
    consumption_summary: str | None = Field(default=None, max_length=5000)


class CustomerSiteCreate(BaseModel):
    site_name: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=500)
    annual_consumption_mwh: float | None = Field(default=None, ge=0)


class CustomerSiteResponse(BaseModel):
    id: str
    customer_id: str
    site_name: str
    city: str
    address: str | None
    annual_consumption_mwh: float | None


class CustomerResponse(BaseModel):
    id: str
    workspace_id: str
    company_name: str
    customer_reference: str
    industry: str | None
    contact_name: str | None
    email: str | None
    status: str
    notes: str | None
    contract_summary: str | None
    latest_invoice_summary: str | None
    consumption_summary: str | None
    created_at: str | None
    updated_at: str | None
    site_count: int = 0


class CustomerDetailResponse(CustomerResponse):
    sites: list[CustomerSiteResponse]
    documents: list[dict]


class DemoSeedResponse(BaseModel):
    customer: CustomerDetailResponse
    created: bool
    documents_created: int


class _SeedDocument:
    def __init__(self, name: str, text: str):
        self.name = name
        self._contents = text.encode("utf-8")
        self.size = len(self._contents)

    def getbuffer(self) -> memoryview:
        return memoryview(self._contents)


DEMO_DOCUMENTS = (
    (
        "demo-contract.txt",
        "Contract",
        "FICTIONAL DEMO DOCUMENT — Demo Industrie SAS\n"
        "Customer reference: DEMO-FR-2026-001. Electricity supply agreement "
        "covering Paris Operations, Lyon Production and Lille Distribution. "
        "Term: January 2026 to December 2028. Illustrative fixed energy rate: "
        "EUR 80 per MWh. This document contains no real customer data.",
    ),
    (
        "demo-invoice-january-2026.txt",
        "Invoice",
        "FICTIONAL DEMO INVOICE — January 2026\n"
        "Demo Industrie SAS used 100 MWh. Energy charges were EUR 8,000 at "
        "EUR 80/MWh. Illustrative network, tax and standing charges were "
        "EUR 2,000. Total invoice: EUR 10,000.",
    ),
    (
        "demo-invoice-february-2026.txt",
        "Invoice",
        "FICTIONAL DEMO INVOICE — February 2026\n"
        "Demo Industrie SAS used 130 MWh. Energy charges were EUR 10,400 at "
        "the unchanged EUR 80/MWh rate. Illustrative network, tax and standing "
        "charges were EUR 2,500. Total invoice: EUR 12,900. The higher usage "
        "was driven by an additional production shift at Lille Distribution.",
    ),
    (
        "demo-consumption-summary.txt",
        "Consumption",
        "FICTIONAL DEMO CONSUMPTION SUMMARY\n"
        "January 2026 consumption was 100 MWh. February 2026 consumption was "
        "130 MWh, an increase of 30 MWh or 30 percent. Operations reported "
        "that the Lille site added a production shift in February.",
    ),
)


def ensure_workspace_access(current_user: User, workspace_id: str) -> None:
    if workspace_service.get_workspace(workspace_id) is None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    if not current_user.is_superuser and not user_service.user_has_workspace(
        user_id=current_user.id, workspace_id=workspace_id
    ):
        raise HTTPException(status_code=403, detail="You do not have access to this workspace.")


def _detail(service: CustomerService, customer: dict) -> dict:
    documents = DocumentRegistry(service.workspace_id).get_all_documents(
        customer_id=customer["id"]
    )
    return {
        **customer,
        "site_count": len(service.list_sites(customer["id"])),
        "sites": service.list_sites(customer["id"]),
        "documents": documents,
    }


@router.get("", response_model=list[CustomerResponse])
def list_customers(workspace_id: str, current_user: User = Depends(get_current_user)):
    ensure_workspace_access(current_user, workspace_id)
    return CustomerService(workspace_id).list_customers()


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    workspace_id: str,
    request: CustomerCreate,
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(current_user, workspace_id)
    try:
        return CustomerService(workspace_id).create_customer(**request.model_dump())
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/seed-demo", response_model=DemoSeedResponse)
def seed_demo_data(workspace_id: str, current_user: User = Depends(get_current_user)):
    ensure_workspace_access(current_user, workspace_id)
    service = CustomerService(workspace_id)
    customer, created = service.seed_demo_customer()
    registry = DocumentRegistry(workspace_id)
    processing = DocumentProcessingService(workspace_id)
    documents_created = 0

    for filename, category, content in DEMO_DOCUMENTS:
        if registry.document_exists(filename):
            continue
        processing.upload_document(
            _SeedDocument(filename, content),
            customer_id=customer["id"],
            category=category,
        )
        documents_created += 1

    return {
        "customer": _detail(service, customer),
        "created": created,
        "documents_created": documents_created,
    }


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    workspace_id: str,
    customer_id: str,
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(current_user, workspace_id)
    service = CustomerService(workspace_id)
    customer = service.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found.")
    return _detail(service, customer)


@router.post(
    "/{customer_id}/sites",
    response_model=CustomerSiteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_customer_site(
    workspace_id: str,
    customer_id: str,
    request: CustomerSiteCreate,
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(current_user, workspace_id)
    try:
        return CustomerService(workspace_id).add_site(
            customer_id=customer_id, **request.model_dump()
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
