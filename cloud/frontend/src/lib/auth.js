function readCookieToken() {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(/(?:^|;\s*)app_auth_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

function readStorageToken(storage) {
  if (!storage) return ''
  return (
    storage.getItem('app_auth_token') ||
    storage.getItem('auth_token') ||
    storage.getItem('token') ||
    ''
  )
}

export function getAuthToken() {
  if (typeof window !== 'undefined' && window.__APP_AUTH_TOKEN__) {
    return String(window.__APP_AUTH_TOKEN__)
  }

  if (typeof sessionStorage !== 'undefined') {
    const sessionToken = readStorageToken(sessionStorage)
    if (sessionToken) return sessionToken
  }

  const cookieToken = readCookieToken()
  if (cookieToken) return cookieToken

  if (typeof localStorage !== 'undefined') {
    return readStorageToken(localStorage)
  }

  return ''
}

export function clearAuthState() {
  if (typeof window !== 'undefined' && Object.prototype.hasOwnProperty.call(window, '__APP_AUTH_TOKEN__')) {
    delete window.__APP_AUTH_TOKEN__
  }

  if (typeof document !== 'undefined') {
    document.cookie = 'app_auth_token=; Path=/; Max-Age=0; SameSite=Lax'
  }

  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('app_auth_token')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('token')
  }

  if (typeof sessionStorage !== 'undefined') {
    sessionStorage.removeItem('app_auth_token')
    sessionStorage.removeItem('auth_token')
    sessionStorage.removeItem('token')
  }
}

export function enforceFreshLoginPerTab() {
  if (typeof window === 'undefined' || typeof sessionStorage === 'undefined') return true

  const markerKey = 'auth_fresh_login_checked'
  if (sessionStorage.getItem(markerKey) === '1') return true
  sessionStorage.setItem(markerKey, '1')

  if (window.location.pathname.startsWith('/login')) return true

  const hasRememberedToken =
    !!readCookieToken() ||
    (typeof localStorage !== 'undefined' && !!readStorageToken(localStorage))

  if (!hasRememberedToken) return true

  clearAuthState()
  window.location.replace('/login')
  return false
}

