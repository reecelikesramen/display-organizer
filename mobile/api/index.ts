import { API_BASE_URL, AUTH_TOKEN } from "./auth";
import { APIError, SchemaError } from "./error";
import {
  base64Image,
  Base64Image,
  ConnectionState,
  getConnectionStateResponse,
  SendImageDirective,
  sendImageResponse,
} from "./model";
import { ZodError } from "zod";

const HEADERS = new Headers();
HEADERS.append("Accept", "application/json");
HEADERS.append("Authorization", `bearer ${AUTH_TOKEN}`);

export async function joinConnection(connection_id: string): Promise<void> {
  const requestOptions = {
    method: "POST",
    headers: HEADERS,
    redirect: "follow",
  } satisfies RequestInit;

  const response = await fetch(
    `${API_BASE_URL}/join_connection/${connection_id}`,
    requestOptions,
  );

  if (!response.ok) {
    throw new APIError(response, await response.text());
  }
}

export async function getConnectionState(
  connection_id: string,
): Promise<ConnectionState> {
  const requestOptions = {
    method: "GET",
    headers: HEADERS,
    redirect: "follow",
  } satisfies RequestInit;

  const response = await fetch(
    `${API_BASE_URL}/connection_state/${connection_id}`,
    requestOptions,
  );

  if (!response.ok) {
    throw new APIError(response, await response.text());
  }

  const json = await response.json();
  const result = getConnectionStateResponse.safeParse(json);

  if (!result.success) {
    throw new SchemaError(response, json, result.error);
  }

  return result.data.state;
}

export async function endConnection(connection_id: string): Promise<void> {
  const requestOptions = {
    method: "POST",
    headers: HEADERS,
    redirect: "follow",
  } satisfies RequestInit;

  const response = await fetch(
    `${API_BASE_URL}/end_connection/${connection_id}`,
    requestOptions,
  );

  if (!response.ok) {
    throw new APIError(response, await response.text());
  }
}

export async function sendImage(
  connection_id: string,
  state: ConnectionState,
  image: Base64Image,
): Promise<SendImageDirective> {
  base64Image.parse(image);

  const formData = new FormData();
  formData.append("image_base64", image);

  const requestOptions = {
    method: "POST",
    headers: HEADERS,
    redirect: "follow",
    body: formData,
  } satisfies RequestInit;

  const response = await fetch(
    `${API_BASE_URL}/image_queue/${connection_id}?state=${state}`,
    requestOptions,
  );

  if (!response.ok) {
    throw new APIError(response, await response.text());
  }

  const json = await response.json();
  const result = sendImageResponse.safeParse(json);

  if (!result.success) {
    throw new SchemaError(response, json, result.error);
  }

  return result.data.directive;
}
