import { apiFetch } from './http'

export const lobbyApi = {
  list() {
    return apiFetch('/lobby/games', { auth: true })
  },

  create(timeControl, colorPreference) {
    return apiFetch('/lobby/create', {
      method: 'POST',
      auth: true,
      body: { time_control: timeControl, color_preference: colorPreference },
    })
  },

  accept(challengeId) {
    return apiFetch(`/lobby/accept/${challengeId}`, {
      method: 'POST',
      auth: true,
    })
  },

  cancel(challengeId) {
    return apiFetch(`/lobby/cancel/${challengeId}`, {
      method: 'DELETE',
      auth: true,
    })
  },
}