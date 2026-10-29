import { API_CONFIG } from './config'

/**
 * Standard API error class reflecting the backend error envelope:
 * { "error": { "code": "...", "message": "...", "details": {} } }
 */
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    message: string,
    public code?: string,
    public details?: unknown,
    public rawResponse?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Centralized HTTP Client
 * Dispatches standard JSON & multipart HTTP requests to VITE_API_BASE_URL.
 * Normalizes error responses (401, 403, 404, 409, 422, 500) and unwraps
 * the documented response envelopes ({ data: ... }).
 */
class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  private getAuthHeader(): Record<string, string> {
    // Only send Authorization header if a valid session token exists in sessionStorage
    // Never stores Google OAuth secrets or client secrets in local storage
    if (typeof window === 'undefined') return {}
    const token = sessionStorage.getItem('classfix_auth_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...this.getAuthHeader(),
      ...((options.headers as Record<string, string>) || {}),
    }

    // Only set Content-Type to application/json if not FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      })

      if (!response.ok) {
        // If 401 Unauthorized, invalidate local session token
        if (response.status === 401 && typeof window !== 'undefined') {
          sessionStorage.removeItem('classfix_auth_token')
        }

        let errorMessage = `HTTP ${response.status} ${response.statusText}`
        let errorCode = 'API_ERROR'
        let errorDetails: unknown
        let rawResponse: unknown

        try {
          rawResponse = await response.json()
          if (typeof rawResponse === 'object' && rawResponse !== null) {
            const raw = rawResponse as Record<string, unknown>
            // Parse documented envelope: { "error": { "code": "...", "message": "...", "details": {} } }
            if (raw.error && typeof raw.error === 'object') {
              const errObj = raw.error as Record<string, unknown>
              if (errObj.message) errorMessage = String(errObj.message)
              if (errObj.code) errorCode = String(errObj.code)
              if (errObj.details) errorDetails = errObj.details
            } else if (raw.detail) {
              if (Array.isArray(raw.detail)) {
                // FastAPI 422 validation array
                errorMessage = raw.detail
                  .map((err: unknown) => {
                    if (typeof err === 'object' && err !== null && 'msg' in err) {
                      return String((err as { msg: unknown }).msg)
                    }
                    return JSON.stringify(err)
                  })
                  .join('; ')
              } else {
                errorMessage = String(raw.detail)
              }
            } else if (raw.message) {
              errorMessage = String(raw.message)
            }
          }
        } catch {
          // Response body is not JSON
        }
        throw new ApiError(response.status, errorMessage, errorCode, errorDetails, rawResponse)
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T
      }

      const json = await response.json()

      // If backend wrapped response in envelope { data: ... }, unwrap data
      if (json && typeof json === 'object' && 'data' in json) {
        return (json as { data: T }).data
      }

      return json as T
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        throw err
      }
      const message =
        err instanceof Error
          ? err.message === 'Failed to fetch' || err.message.includes('fetch')
            ? `Unable to connect to the server at ${this.baseUrl}. Please ensure the backend is running.`
            : err.message
          : 'Unable to connect to the server. Please try again.'

      throw new ApiError(0, message)
    }
  }

  async get<T>(
    endpoint: string,
    params?: Record<string, string | number | boolean | undefined>
  ): Promise<T> {
    let query = ''
    if (params) {
      const searchParams = new URLSearchParams()
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      }
      const qs = searchParams.toString()
      if (qs) {
        query = `?${qs}`
      }
    }
    return this.request<T>(`${endpoint}${query}`, { method: 'GET' })
  }

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  async postFormData<T>(endpoint: string, formData: FormData): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData,
    })
  }

  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  async patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const apiClient = new ApiClient(API_CONFIG.baseUrl)
