// Synthetic shape for client freshness tests. Only FastAPI verifies signatures.
export function fixtureJwt(expires = Math.floor(Date.now() / 1000) + 300) {
  const segment = (value: object) => btoa(JSON.stringify(value)).replace(/=+$/, '')
  return `${segment({ alg: 'EdDSA' })}.${segment({ exp: expires })}.fixture`
}
