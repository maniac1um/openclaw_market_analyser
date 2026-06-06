/** @deprecated Use AuthContext getAuthHeaders instead */
export function getWriteHeaders(extra?: Record<string, string>): Record<string, string> {
  return { 'Content-Type': 'application/json', ...extra }
}

export const writeFetchInit: RequestInit = { credentials: 'include' }
