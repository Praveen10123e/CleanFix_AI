import type { User } from '@/types'

export interface IAuthService {
  /**
   * GET /auth/me
   * Fetches the currently authenticated user from backend session/token
   */
  getCurrentUser(): Promise<User | null>

  /**
   * POST /auth/google
   * Authenticates with Google Workspace OAuth credential token
   */
  loginWithGoogle(credential: string): Promise<User>

  /**
   * POST /auth/logout or session clearing
   */
  logout(): Promise<void>
}
