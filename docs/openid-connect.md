# OpenID Connect (OIDC) Deep Dive

## What OpenID Connect Is
OpenID Connect (OIDC) is an identity layer built on top of OAuth 2.0 that standardizes user authentication and identity data exchange.

OAuth 2.0 alone tells APIs what a client can do. OIDC adds a standard way to answer: "Who is the user that authenticated?"

> **Key Takeaway:** OIDC is OAuth 2.0 + identity (authentication + user claims).

## How OIDC Builds on OAuth 2.0
OIDC reuses OAuth 2.0 infrastructure:
- Authorization endpoint
- Token endpoint
- Scopes and consent model
- Access tokens

Then adds identity-specific elements:
- `id_token` (JWT containing identity claims)
- Standard user scopes (`openid`, `profile`, `email`, etc.)
- UserInfo endpoint
- Discovery metadata endpoint
- JWKS endpoint for signature verification

---

## Authentication vs Authorization

| Concept | Purpose | Typical Artifact |
|---|---|---|
| Authentication | Verify who the user is | ID token, login session |
| Authorization | Determine what access is allowed | Access token, scopes |

> **Common Mistake:** Treating access tokens as proof of login identity in frontend apps.

---

## ID Tokens
An ID token is usually a signed JWT issued by the OpenID Provider (OP). It carries claims about the authentication event and the authenticated user.

Common claims:
- `iss` (issuer)
- `sub` (stable user identifier)
- `aud` (intended client)
- `exp` (expiration)
- `iat` (issued at)
- `nonce` (replay protection for browser-based flows)
- `auth_time` (optional authentication timestamp)

> **Best Practice:** Use `sub` as the durable user key. Avoid using mutable fields like email as the primary identifier.

---

## Claims
Claims are key-value identity attributes in ID token and/or UserInfo response.

Examples:
- `name`
- `preferred_username`
- `email`
- `email_verified`
- `given_name`
- `family_name`

Claims returned depend on scopes, consent, and provider policy.

---

## Standard OIDC Scopes
- `openid` (required for OIDC; signals an authentication request)
- `profile` (basic profile claims)
- `email` (email claims)
- `address` (address claims)
- `phone` (phone number claims)
- `offline_access` (request refresh token, provider-dependent)

> **Interview Tip:** If the scope does not include `openid`, it is not an OIDC authentication request.

---

## UserInfo Endpoint
The UserInfo endpoint returns claims about the authenticated user when called with a valid access token.

Typical use:
- Keep ID token lean
- Retrieve additional profile data after login

---

## Discovery Endpoint
OIDC discovery lets clients fetch provider metadata from:

```text
https://id.example.com/.well-known/openid-configuration
```

This document usually includes endpoint URLs, supported scopes, signing algorithms, and the JWKS URI.

---

## JWKS Endpoint
JWKS (JSON Web Key Set) endpoint publishes public keys used to verify token signatures:

```text
https://id.example.com/.well-known/jwks.json
```

Clients or backend validators use `kid` in token header to pick the matching key from JWKS.

---

## OIDC Login Flow (Authorization Code + PKCE)
1. Client sends user to authorization endpoint with `scope=openid ...`, `state`, `nonce`, and PKCE challenge.
2. User authenticates and grants consent.
3. Authorization server returns authorization code to redirect URI.
4. Client exchanges code (+ PKCE verifier) at token endpoint.
5. Server returns `id_token` and `access_token` (plus optional `refresh_token`).
6. Client validates ID token and establishes local session.

> **Key Takeaway:** OIDC login security depends heavily on proper ID token validation.

---

## Technical Examples

### 1. OIDC Authorization Request
```http
GET /authorize?
 response_type=code&
 client_id=spa-client-789&
 redirect_uri=https%3A%2F%2Fapp.example.com%2Foidc-callback&
 scope=openid%20profile%20email&
 state=5f2f6c9f8a&
 nonce=n-0S6_WzA2Mj&
 code_challenge=RkQ4Wk8zZ0R2V2syQ0I5d0dldU5mR1JfVVJ6ZzE2S0h2NW5Zd2M0SQ&
 code_challenge_method=S256 HTTP/1.1
Host: id.example.com
```

Plain English:
- `openid` requests authentication semantics.
- `state` protects request/response integrity.
- `nonce` binds login response to this browser session.
- PKCE protects the authorization code.

### 2. Example ID Token
```json
{
  "header": {
    "alg": "RS256",
    "kid": "a1b2c3"
  },
  "payload": {
    "iss": "https://id.example.com",
    "sub": "00u123abc456def789",
    "aud": "spa-client-789",
    "exp": 1760003600,
    "iat": 1760000000,
    "nonce": "n-0S6_WzA2Mj",
    "email": "analyst@example.com",
    "email_verified": true,
    "name": "Alex Analyst"
  }
}
```

Plain English:
- This token says which provider issued it, for which client, for which subject, and until when it is valid.
- `nonce` helps detect replay/substitution attacks in browser flows.

### 3. Decoded Claim Validation Checklist
```text
1. Signature validates against provider JWKS key matching kid
2. iss exactly matches expected issuer
3. aud includes this client_id
4. exp is in the future (with small clock skew allowance)
5. iat is reasonable and not far in the past/future
6. nonce matches the value stored before redirect (for browser flows)
```

Plain English:
- If any check fails, login should be rejected.

### 4. UserInfo Response Example
```http
GET /userinfo HTTP/1.1
Host: id.example.com
Authorization: Bearer eyJraWQiOiJhMWIyYzMifQ.eyJzY29wZSI6Im9wZW5pZCBlbWFpbCJ9.signature
```

```json
{
  "sub": "00u123abc456def789",
  "name": "Alex Analyst",
  "given_name": "Alex",
  "family_name": "Analyst",
  "email": "analyst@example.com",
  "email_verified": true
}
```

Plain English:
- UserInfo is useful for profile data not needed in every ID token.
- `sub` should match ID token subject.

### 5. Discovery Document Snippet
```json
{
  "issuer": "https://id.example.com",
  "authorization_endpoint": "https://id.example.com/authorize",
  "token_endpoint": "https://id.example.com/oauth2/token",
  "userinfo_endpoint": "https://id.example.com/userinfo",
  "jwks_uri": "https://id.example.com/.well-known/jwks.json",
  "scopes_supported": ["openid", "profile", "email", "offline_access"],
  "response_types_supported": ["code"],
  "id_token_signing_alg_values_supported": ["RS256"]
}
```

Plain English:
- Clients can auto-configure endpoints and supported capabilities safely.

---

## Critical Validation Concepts

### `nonce`
Prevents token replay/substitution in browser-based authentication. Store before redirect, compare after callback.

### `state`
Protects against CSRF and response mix-up attacks. Must be unpredictable and strictly validated.

### `issuer` (`iss`)
Must exactly match the trusted provider issuer URL from discovery.

### `audience` (`aud`)
Must contain your client ID; otherwise token is not meant for your app.

### `exp` and `iat`
- `exp`: reject expired tokens.
- `iat`: ensure token issuance time is reasonable.

### Redirect URI Validation
Authorization server should require exact redirect URI match. No wildcard callback URLs in production.

> **Best Practice:** Keep an allowlist of exact redirect URIs per client.

---

## Security Best Practices
- Use Authorization Code Flow with PKCE.
- Require HTTPS for all redirect URIs (except specific localhost dev cases).
- Validate ID token signature and claims server-side where possible.
- Verify `nonce` for browser login flows.
- Use short session lifetimes and re-authentication for sensitive actions.
- Do not put tokens in URL fragments for modern web apps.
- Rotate keys safely and honor `kid` key rollover behavior.

---

## Common Implementation Pitfalls
- Accepting ID tokens without signature verification.
- Skipping `iss` or `aud` checks.
- Forgetting `nonce` validation in SPA login flows.
- Trusting unverified email claim for authorization decisions.
- Mixing authentication logic with API authorization scopes.

> **Common Mistake:** Granting admin privileges based only on `email` domain without additional authorization policy.

## Quick Interview Review
- OIDC adds authentication to OAuth 2.0.
- ID token represents authentication event and user identity claims.
- Access token authorizes API calls; ID token should not be used as an API bearer token.
- Discovery and JWKS standardize secure interoperability.

> **Interview Tip:** In interviews, say: "OAuth 2.0 delegates API authorization; OIDC standardizes identity authentication on top of it."
