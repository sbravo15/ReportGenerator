# OAuth 2.0 Deep Dive

## What OAuth 2.0 Is
OAuth 2.0 is an authorization framework that allows an application to obtain limited access to protected resources (usually APIs) on behalf of a user or as itself, without sharing user passwords with that application.

OAuth 2.0 is about **delegated authorization**, not user authentication.

> **Key Takeaway:** OAuth 2.0 answers: "Can this client call this API with these permissions?"

## Why OAuth 2.0 Exists
Before OAuth, third-party applications often collected and stored user passwords to integrate with APIs. That model was unsafe and difficult to control.

OAuth 2.0 solves this by:
- Delegating access through scoped tokens
- Separating login credentials from API clients
- Providing revocable, time-bound access

## The Problem OAuth 2.0 Solves
OAuth 2.0 helps organizations prevent:
- Password sharing with third-party apps
- Overly broad API access
- Long-lived access without user visibility or consent

It enables:
- Fine-grained scopes
- User consent screens
- Centralized authorization policy

---

## Core Roles

| Role | Description |
|---|---|
| **Resource Owner** | The user (or entity) who owns the protected data |
| **Client** | The application requesting access |
| **Authorization Server** | Issues tokens after authenticating user and obtaining consent |
| **Resource Server** | API server that validates access tokens and serves protected data |

### Role Example in Plain English
A calendar app (client) asks permission to read your contacts (resource owner) from an API (resource server). The identity platform (authorization server) shows consent and issues tokens.

---

## Scopes and Consent
Scopes define what access is being requested, such as:
- `read:profile`
- `read:orders`
- `write:orders`

Consent screens should clearly show requested scopes. Well-designed systems request only the minimum scopes needed.

> **Best Practice:** Use least privilege scopes and split read/write scopes.

> **Common Mistake:** Requesting broad scopes like `*` or admin-level access for basic features.

---

## Tokens in OAuth 2.0

### Access Tokens
- Short-lived credentials used to call APIs
- Sent in `Authorization: Bearer <token>` header
- Can be opaque or JWT-formatted

### Refresh Tokens
- Long-lived credentials used to obtain new access tokens
- Should be strongly protected and rotated when possible
- Typically issued only when offline access is needed

> **Security Note:** A bearer token is usable by whoever holds it. Protect it like a secret.

---

## Grant Types (Modern Perspective)

### 1. Authorization Code Flow (Recommended for user-based web/mobile)
- Most common modern flow
- Supports user login + consent + back-channel token exchange
- Should be paired with PKCE for public clients and is now recommended broadly

### 2. Client Credentials Flow
- Machine-to-machine
- No end-user consent step
- Used for service accounts or backend integrations

### 3. Device Authorization Flow
- For devices with limited input (TVs, CLI tools, IoT)
- User authorizes on another device/browser

### Legacy/Discouraged Flows
- Implicit flow: largely deprecated for modern apps
- Resource Owner Password Credentials (ROPC): avoid unless migration edge case

> **Interview Tip:** If asked "Which OAuth flow should I use for a SPA or mobile app?" answer: Authorization Code Flow with PKCE.

---

## Authorization Code Flow (Step-by-Step)
1. Client redirects user to authorization server.
2. User authenticates and gives consent.
3. Authorization server redirects back with authorization code.
4. Client exchanges code for tokens at token endpoint.
5. Client calls API using access token.

---

## PKCE and Why It Matters
PKCE (Proof Key for Code Exchange) protects authorization code flow against code interception attacks.

How it works:
1. Client generates a random `code_verifier`.
2. Client derives `code_challenge` (usually SHA-256 + Base64URL).
3. Client sends `code_challenge` in authorization request.
4. During token exchange, client sends original `code_verifier`.
5. Server validates verifier/challenge match before issuing tokens.

PKCE is critical for public clients (SPA/mobile/native) that cannot keep a client secret securely.

> **Best Practice:** Use `S256` PKCE method, never `plain` unless absolutely required.

---

## Technical Examples

### 1. Authorization Request Example
```http
GET /authorize?
 response_type=code&
 client_id=web-client-123&
 redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback&
 scope=openid%20profile%20read%3Aorders&
 state=af0ifjsldkj&
 code_challenge=3vQ7g5h0Y2QmXx3kA6P4V8l6YwP9zKJvLQeQx8J4sM4&
 code_challenge_method=S256 HTTP/1.1
Host: id.example.com
```

Plain English:
- The app asks the authorization server for an authorization code.
- `state` protects against CSRF.
- `code_challenge` starts PKCE protection.

### 2. Authorization Code Exchange Example
```bash
curl -X POST https://id.example.com/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=SplxlOBeZQQYbYS6WxSbIA" \
  -d "redirect_uri=https://app.example.com/callback" \
  -d "client_id=web-client-123" \
  -d "code_verifier=R7f4n2Xb9w1kPq3Jr8uV6tY0mC5zLhN2eQdW"
```

Plain English:
- Backend sends the one-time authorization code.
- It proves possession of the original PKCE secret (`code_verifier`).
- If valid, server returns tokens.

### 3. Example Token Response Payload
```json
{
  "access_token": "eyJraWQiOiIxMjMiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjM0NSIsInNjb3BlIjoicmVhZDpvcmRlcnMifQ.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200a5f4f7f9...",
  "scope": "read:orders"
}
```

Plain English:
- `access_token`: sent to APIs.
- `expires_in`: token lifetime in seconds.
- `refresh_token`: used to request new access tokens.

### 4. Refresh Token Exchange Example
```http
POST /oauth2/token HTTP/1.1
Host: id.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=def50200a5f4f7f9...&
client_id=web-client-123
```

Expected JSON response:
```json
{
  "access_token": "eyJraWQiOiIxMjM0In0.eyJzY29wZSI6InJlYWQ6b3JkZXJzIn0.signature",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "def50200b8a1f2..."
}
```

Plain English:
- Client gets a new access token without forcing the user to sign in again.
- Some providers rotate refresh tokens each time.

### 5. Calling an API with a Bearer Token
```bash
curl -X GET https://api.example.com/orders \
  -H "Authorization: Bearer eyJraWQiOiIxMjM0In0.eyJzY29wZSI6InJlYWQ6b3JkZXJzIn0.signature"
```

JavaScript example:
```javascript
const token = process.env.ACCESS_TOKEN;

const response = await fetch("https://api.example.com/orders", {
  headers: {
    Authorization: `Bearer ${token}`
  }
});

const data = await response.json();
console.log(data);
```

Python example:
```python
import os
import requests

token = os.environ["ACCESS_TOKEN"]
resp = requests.get(
    "https://api.example.com/orders",
    headers={"Authorization": f"Bearer {token}"},
    timeout=10,
)
print(resp.status_code)
print(resp.json())
```

Plain English:
- The token proves API authorization.
- If token is missing, expired, or lacks scope, the API should deny access.

---

## Modern OAuth 2.0 Security Best Practices
- Use Authorization Code Flow with PKCE for user-facing apps.
- Enforce exact redirect URI matching (no wildcards).
- Use `state` and validate it on callback.
- Keep access tokens short-lived.
- Rotate refresh tokens and detect token replay.
- Store tokens securely (avoid browser local storage when possible).
- Require TLS everywhere.
- Prefer sender-constrained tokens for high-risk APIs (DPoP or mTLS).
- Validate token audience (`aud`), issuer (`iss`), expiry (`exp`), and scope at APIs.
- Use token introspection if using opaque tokens.

> **Best Practice:** Build centralized token validation middleware in APIs to avoid inconsistent authorization checks.

---

## Common Mistakes and Risks
- Using OAuth for authentication without OIDC.
- Not validating `state` or redirect URI.
- Returning tokens in front-channel URLs.
- Over-scoping API permissions.
- Storing long-lived tokens insecurely in client-side code.
- Treating JWT access tokens as trusted without signature and claim validation.

> **Common Mistake:** Assuming "it is a JWT" means it is automatically valid.

---

## Practical Use Cases
- Third-party app integration with user consent ("Connect your calendar").
- Internal microservice authorization with service identities.
- API gateway enforcement of scopes and token claims.
- Mobile app access to backend APIs without exposing user credentials.

## Quick Interview Review
- OAuth 2.0 = authorization delegation framework.
- OIDC adds authentication and identity claims.
- PKCE protects authorization code interception.
- Access tokens authorize API calls; refresh tokens renew sessions.

> **Interview Tip:** Explain OAuth with a concrete example: "A photo-printing app can read your photos without ever seeing your password."
