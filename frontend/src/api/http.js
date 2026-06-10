const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error 
{
  constructor(message, status, data = null) 
  {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function authHeader() 
{
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}


export async function apiFetch(path, { method = 'GET', body, auth = false, headers = {} } = {}) {
  const reqHeaders = { ...headers }
  if(body !== undefined) 
    reqHeaders['Content-Type'] = 'application/json'
  if(auth) 
    Object.assign(reqHeaders, authHeader())

  let res
  try 
  {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: reqHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } 
  catch 
  {
    throw new ApiError('Cannot connect to server.', 0)
  }

  let data = null
  try
  {
    data = await res.json()
  } 
  catch {}

  if(!res.ok) 
  {
    const detail = data?.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail) && detail.length
        ? detail.map(d => d.msg).join(', ')
        : `Request failed (${res.status})`
    throw new ApiError(message, res.status, data)
  }
  return data
}

export const apiBaseUrl = BASE_URL

export function wsBaseUrl() {
  if(/^https?:\/\//.test(BASE_URL)) 
    {
    return BASE_URL.replace(/^http/, 'ws')
  }
  const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const prefix = BASE_URL.replace(/\/$/, '')
  return `${scheme}://${window.location.host}${prefix}`
}