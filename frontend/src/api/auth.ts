import request from './request'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '@/types'

export const authApi = {
  login(data: LoginRequest): Promise<AuthResponse> {
    return request.post('/auth/login', data)
  },

  register(data: RegisterRequest): Promise<any> {
    return request.post('/auth/register', data)
  },

  getCurrentUser(): Promise<User> {
    return request.get('/auth/me')
  },
}
