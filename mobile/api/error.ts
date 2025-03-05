import { ZodError } from "zod"

export class APIError extends Error {
  constructor(response: Response, responseText?: string) {
    const errorDetails = {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      body: responseText ?? "Not provided",
    }
    super(`API Error on ${response.url} status: ${response.status}`, { cause: errorDetails })
  }
}

export class SchemaError extends Error {
  constructor(response: Response, responseJson: any, zodError: ZodError) {
    const requestDetails = {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      json: responseJson,
    }
    super(`Schema Error on ${response.url}: ${zodError.message}`, { cause: { error: zodError, requestDetails } })
  }
}
