import { apiFetch } from './http'

export const gameApi = {
  get(id) {
    return apiFetch(`/game/${id}`, { auth: true })
  },
}