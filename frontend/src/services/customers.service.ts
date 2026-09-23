import { api, getApiErrorMessage } from "../lib/api";
import type {
  Customer,
  CustomerCreate,
  CustomerDetail,
  DemoSeedResult,
} from "../types/customer.types";

export async function listCustomers(workspaceId: string): Promise<Customer[]> {
  try {
    const response = await api.get<Customer[]>(
      `/workspaces/${workspaceId}/customers`
    );
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Couldn't load customers."));
  }
}

export async function getCustomer(
  workspaceId: string,
  customerId: string
): Promise<CustomerDetail> {
  try {
    const response = await api.get<CustomerDetail>(
      `/workspaces/${workspaceId}/customers/${customerId}`
    );
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Couldn't load this customer."));
  }
}

export async function createCustomer(
  workspaceId: string,
  customer: CustomerCreate
): Promise<Customer> {
  try {
    const response = await api.post<Customer>(
      `/workspaces/${workspaceId}/customers`,
      customer
    );
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Couldn't create this customer."));
  }
}

export async function seedDemoCustomer(workspaceId: string): Promise<DemoSeedResult> {
  try {
    const response = await api.post<DemoSeedResult>(
      `/workspaces/${workspaceId}/customers/seed-demo`,
      {},
      { timeout: 180_000 }
    );
    return response.data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error, "Couldn't prepare the demo customer."));
  }
}
