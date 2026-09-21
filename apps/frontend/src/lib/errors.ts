/**
 * Convert raw API/AI errors into user-friendly messages.
 * Never expose internal error codes or stack traces to the user.
 */

export function friendlyError(raw: unknown): string {
  const msg = raw instanceof Error ? raw.message : String(raw || '')

  // Rate limit
  if (/429|rate.limit|token.per.day|TPD|quota/i.test(msg)) {
    return 'The AI service has reached its usage limit. Please wait a few minutes, or switch to a different provider in Settings.'
  }

  // Auth / API key
  if (/401|403|authentication|invalid.api|api.key|unauthorized/i.test(msg)) {
    return 'Invalid API key. Please check your Settings and make sure the correct key is active.'
  }

  // Model not found
  if (/404|model.not.found|decommissioned/i.test(msg)) {
    return 'The selected AI model is no longer available. Please update your provider settings.'
  }

  // Network
  if (/network|ECONNREFUSED|fetch.failed|failed.to.fetch/i.test(msg)) {
    return 'Could not reach the AI service. Please check your internet connection.'
  }

  // Server error
  if (/500|internal.server/i.test(msg)) {
    return 'A server error occurred. Please try again in a moment.'
  }

  // Timeout
  if (/timeout|timed.out/i.test(msg)) {
    return 'The request timed out. Please try again.'
  }

  // Generic fallback — never show the raw message
  return 'Something went wrong. Please try again or check your Settings.'
}

export function friendlySseError(raw: string): string {
  return friendlyError(raw)
}
