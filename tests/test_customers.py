import io
from unittest.mock import patch


def _create_customer(client, workspace_id, headers, reference="CUSTOMER-001"):
    return client.post(
        f"/workspaces/{workspace_id}/customers",
        headers=headers,
        json={
            "company_name": "Example Manufacturing SAS",
            "customer_reference": reference,
            "industry": "Manufacturing",
            "contact_name": "Demo Contact",
            "email": "demo.contact@example.com",
        },
    )


def test_customer_creation_and_retrieval(client, make_user, make_workspace):
    user = make_user("customer-create")
    workspace = make_workspace(user)

    created = _create_customer(client, workspace["id"], user["headers"])
    assert created.status_code == 201, created.text

    customer_id = created.json()["id"]
    response = client.get(
        f"/workspaces/{workspace['id']}/customers/{customer_id}",
        headers=user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["company_name"] == "Example Manufacturing SAS"
    assert response.json()["sites"] == []
    assert response.json()["documents"] == []


def test_customer_lists_are_workspace_isolated(client, make_user, make_workspace):
    owner = make_user("customer-owner")
    outsider = make_user("customer-outsider")
    workspace = make_workspace(owner)
    created = _create_customer(client, workspace["id"], owner["headers"])
    customer_id = created.json()["id"]

    list_response = client.get(
        f"/workspaces/{workspace['id']}/customers", headers=outsider["headers"]
    )
    detail_response = client.get(
        f"/workspaces/{workspace['id']}/customers/{customer_id}",
        headers=outsider["headers"],
    )

    assert list_response.status_code == 403
    assert detail_response.status_code == 403


def test_customer_site_is_returned_on_profile(client, make_user, make_workspace):
    user = make_user("customer-site")
    workspace = make_workspace(user)
    customer = _create_customer(client, workspace["id"], user["headers"]).json()

    site_response = client.post(
        f"/workspaces/{workspace['id']}/customers/{customer['id']}/sites",
        headers=user["headers"],
        json={
            "site_name": "Lyon Production",
            "city": "Lyon",
            "annual_consumption_mwh": 1250,
        },
    )
    assert site_response.status_code == 201, site_response.text

    profile = client.get(
        f"/workspaces/{workspace['id']}/customers/{customer['id']}",
        headers=user["headers"],
    ).json()
    assert profile["site_count"] == 1
    assert profile["sites"][0]["city"] == "Lyon"


def test_document_can_be_associated_with_customer(client, make_user, make_workspace):
    user = make_user("customer-document")
    workspace = make_workspace(user)
    customer = _create_customer(client, workspace["id"], user["headers"]).json()

    upload = client.post(
        f"/workspaces/{workspace['id']}/documents",
        headers=user["headers"],
        data={"customer_id": customer["id"], "category": "Invoice"},
        files={
            "file": (
                "customer-invoice.txt",
                io.BytesIO(b"Illustrative invoice total: EUR 1,250."),
                "text/plain",
            )
        },
    )

    assert upload.status_code == 201, upload.text
    assert upload.json()["customer_id"] == customer["id"]
    assert upload.json()["category"] == "Invoice"

    profile = client.get(
        f"/workspaces/{workspace['id']}/customers/{customer['id']}",
        headers=user["headers"],
    ).json()
    assert [document["name"] for document in profile["documents"]] == [
        "customer-invoice.txt"
    ]


def test_assistant_receives_selected_customer_context(
    client, make_user, make_workspace
):
    user = make_user("customer-assistant")
    workspace = make_workspace(user)
    customer = client.post(
        f"/workspaces/{workspace['id']}/customers",
        headers=user["headers"],
        json={
            "company_name": "Context Customer SAS",
            "customer_reference": "CONTEXT-001",
            "industry": "Manufacturing",
            "contract_summary": "Illustrative fixed rate of EUR 80/MWh.",
            "consumption_summary": "February consumption increased by 30 MWh.",
        },
    ).json()

    with patch(
        "app.services.rag_service.ask_llm",
        return_value="February cost more because consumption increased [Customer profile].",
    ) as mocked_llm:
        response = client.post(
            "/assistant/chat",
            headers=user["headers"],
            json={
                "workspace_id": workspace["id"],
                "customer_id": customer["id"],
                "question": "Why did February cost more?",
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["sources"][0]["document_name"] == "Customer profile"
    prompt = mocked_llm.call_args.kwargs["prompt"]
    assert "Context Customer SAS" in prompt
    assert "February consumption increased by 30 MWh" in prompt
