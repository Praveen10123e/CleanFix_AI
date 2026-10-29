/**
 * Central API Configuration
 * Manages base URLs and client environment.
 * Never stores client secrets or tokens in code or client env vars.
 */

export interface ApiConfig {
  baseUrl: string
  appEnv: 'development' | 'staging' | 'production'
  googleClientId?: string
}

const env: Partial<ImportMetaEnv> =
  typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : {}

export const API_CONFIG: ApiConfig = {
  baseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  appEnv: (env.VITE_APP_ENV as ApiConfig['appEnv']) || 'development',
  googleClientId: env.VITE_GOOGLE_CLIENT_ID,
}
