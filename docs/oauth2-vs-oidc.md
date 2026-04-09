# OAuth 2.0 vs OpenID Connect

## Executive Summary
OAuth 2.0 and OpenID Connect are related but not interchangeable.
- **OAuth 2.0** is for delegated **authorization**.
- **OIDC** is for **authentication** and identity claims, built on OAuth 2.0.

> **Key Takeaway:** Use OAuth 2.0 to protect API access. Use OIDC when you need to sign users in.

## Why People Confuse Them
- Both use similar endpoints (`/authorize`, `/token`).
- Both use scopes and consent screens.
- Both often return JWTs.
- Many identity platforms support both in one product.

Similarity in transport does not mean same purpose.

---

## Authorization vs Authentication

| Topic | Authorization | Authentication |
|---|---|---|
| Core Question | "What can this client do?" | "Who is this user?" |
| Protocol Commonly Used | OAuth 2.0 | OpenID Connect |
| Primary Token | Access token | ID token |
| Typical Consumer | API / resource server | Client app / relying party |

> **Interview Tip:** Saying "OAuth is login" is usually a red flag in security interviews.

---

## Side-by-Side Comparison Table

| Dimension | OAuth 2.0 | OpenID Connect |
|---|---|---|
| Primary Goal | Delegated API authorization | User authentication and identity |
| Built On | RFC 6749 framework | OAuth 2.0 + OIDC specs |
| Required Scope | No fixed scope required by framework | `openid` is required |
| Main Identity Artifact | None standardized for login identity | `id_token` with claims |
| User Profile Retrieval | Not standardized | `userinfo` endpoint standardized |
| Discovery Standard | Not universal in OAuth-only deployments | `.well-known/openid-configuration` |
| Key Validation Concern | Access token audience/scope/expiry | ID token signature + `iss`/`aud`/`nonce` |
| Typical Use Cases | API access delegation, service-to-service authz | SSO login, federated identity, session establishment |

---

## When to Use OAuth 2.0
Use OAuth 2.0 when your primary problem is API authorization.

Examples:
- A third-party analytics tool needs read-only access to your CRM API.
- A backend service needs scoped access to another internal API.
- An API gateway must enforce per-client scopes.

## When to Use OIDC
Use OIDC when your primary problem is user authentication.

Examples:
- Implementing "Sign in with Corporate SSO" for a web app.
- Building federated login for a mobile app.
- Establishing user sessions with verifiable identity claims.

> **Best Practice:** In many apps you use both: OIDC for login, OAuth 2.0 access tokens for API authorization.

---

## Practical Scenarios

### Scenario 1: API Integration Without User Login
A nightly billing job calls an internal API using machine identity.
- Recommended: OAuth 2.0 Client Credentials
- OIDC needed: No

### Scenario 2: Employee Portal Login
Users log in with enterprise identity provider and get a local app session.
- Recommended: OIDC Authorization Code + PKCE
- OAuth-only approach: Incomplete for authentication

### Scenario 3: Mobile App Calling User Data APIs
User signs in and app calls profile/orders API.
- Recommended: OIDC for authentication + OAuth 2.0 access token for API calls
- Why: You need both identity and authorization.

### Scenario 4: "Sign in with X" Social Login
App needs verified user identity from external provider.
- Recommended: OIDC
- OAuth-only risk: No standardized identity assertion

---

## Common Misunderstandings
- "I got an access token, so I know who the user is." -> Not always true.
- "JWT means authentication." -> JWT is only a token format.
- "OAuth replaced login protocols completely." -> OIDC is the standardized login layer.
- "ID token should be sent to APIs." -> APIs generally expect access tokens.

> **Common Mistake:** Using ID token as a bearer token to call business APIs.

---

## Decision Checklist
- Need user login and identity claims? -> Use OIDC.
- Need delegated API authorization? -> Use OAuth 2.0.
- Need both login and API access? -> Use OIDC + OAuth together.
- Building browser/mobile app? -> Prefer Authorization Code Flow with PKCE.

## Key Takeaway Summary
- OAuth 2.0 is about **permissions to resources**.
- OIDC is about **proving who the user is**.
- Modern systems commonly combine both for secure, user-friendly architectures.

> **Interview Tip:** A strong answer includes architecture language: "OIDC establishes identity; OAuth scopes govern downstream API access."
