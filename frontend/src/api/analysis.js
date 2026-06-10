import { apiFetch } from './http'

export const analysisApi = {
  position(fen) 
  {
    return apiFetch('/analysis/position', {
      method: 'POST',
      auth: true,
      body: { fen },
    })
  },

  game(fens) 
  {
    return apiFetch('/analysis/game', {
      method: 'POST',
      auth: true,
      body: { fens },
    })
  },
}