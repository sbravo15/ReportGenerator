# Suggested Visuals for This Repository

This document proposes visuals you can generate later and add manually to the repository.

> **Important:** This file only provides image concepts and prompts. It does not generate images.

## Visual 1: IAM vs IGA vs PAM Comparison Diagram
- **Visual Title:** IAM vs IGA vs PAM at a Glance
- **What the Image Should Show:**
  - Three columns for IAM, IGA, PAM
  - For each column: focus, key controls, owners, risk reduction goal
  - A bottom row showing how they work together in one enterprise architecture
- **Belongs In:** `docs/iam-iga-pam.md`
- **Placement in File:** Right below "## Side-by-Side Comparison"
- **Why It Improves the Explanation:** Converts acronym-heavy text into a fast mental model for interviews and revision.
- **Ready-to-Use Image Generation Prompt:**

```text
Create a professional cybersecurity infographic titled "IAM vs IGA vs PAM at a Glance".
Style: clean enterprise design, white background, blue/gray palette, minimal icons, readable typography.
Layout: 3 vertical columns labeled IAM, IGA, PAM.
For each column include rows: Primary Focus, Security Purpose, Business Purpose, Typical Controls, Typical Owners.
Add a bottom horizontal band labeled "How They Work Together" showing IAM -> IGA -> PAM collaboration in identity security.
Use concise labels, no clutter, 16:9 ratio, suitable for a GitHub technical document.
```

## Visual 2: OAuth 2.0 Authorization Code Flow Diagram
- **Visual Title:** OAuth 2.0 Authorization Code Flow (with API Access)
- **What the Image Should Show:**
  - Actors: User, Client App, Authorization Server, Resource Server
  - Numbered arrows for login, consent, code return, token exchange, API call
  - Distinction between front-channel and back-channel
- **Belongs In:** `docs/oauth2.md`
- **Placement in File:** Right below "## Authorization Code Flow (Step-by-Step)"
- **Why It Improves the Explanation:** Makes flow sequence and trust boundaries easier to understand than text alone.
- **Ready-to-Use Image Generation Prompt:**

```text
Design a clear sequence diagram titled "OAuth 2.0 Authorization Code Flow".
Participants: User, Client Application, Authorization Server, Resource Server API.
Show numbered steps:
1) User redirected to authorization endpoint
2) User authenticates and consents
3) Authorization code returned to client redirect URI
4) Client exchanges code at token endpoint
5) Authorization server returns access token (and optional refresh token)
6) Client calls Resource Server with Bearer token.
Highlight front-channel vs back-channel using different line styles/colors.
Professional enterprise style, flat icons, high readability, light theme, 16:9.
```

## Visual 3: PKCE Flow Diagram
- **Visual Title:** PKCE Security Add-On in Authorization Code Flow
- **What the Image Should Show:**
  - `code_verifier` generation in client
  - `code_challenge` sent in auth request
  - `code_verifier` sent at token exchange
  - Server verification step before issuing tokens
- **Belongs In:** `docs/oauth2.md`
- **Placement in File:** Right below "## PKCE and Why It Matters"
- **Why It Improves the Explanation:** Clarifies why stolen authorization codes are not enough without the verifier.
- **Ready-to-Use Image Generation Prompt:**

```text
Create a technical sequence diagram titled "PKCE in OAuth 2.0 Authorization Code Flow".
Show Client, Authorization Server, and optional attacker note.
Include steps:
- Client generates random code_verifier
- Client derives code_challenge (S256)
- Client sends code_challenge in /authorize request
- Authorization server returns authorization code
- Client sends code + code_verifier to /token
- Authorization server recomputes challenge and verifies match
- Tokens issued only on successful verification.
Add a side note: "Intercepted code alone cannot be redeemed without code_verifier".
Use modern security diagram style, white background, blue/green accents, 16:9.
```

## Visual 4: OpenID Connect Login Flow Diagram
- **Visual Title:** OIDC Authentication Flow (Code + PKCE)
- **What the Image Should Show:**
  - OIDC-specific parameters: `openid`, `nonce`, `state`
  - Token response containing `id_token` and `access_token`
  - Optional call to UserInfo endpoint
  - Session establishment in client app
- **Belongs In:** `docs/openid-connect.md`
- **Placement in File:** Right below "## OIDC Login Flow (Authorization Code + PKCE)"
- **Why It Improves the Explanation:** Visually separates authentication identity outcomes from API authorization outcomes.
- **Ready-to-Use Image Generation Prompt:**

```text
Produce a sequence diagram titled "OpenID Connect Login Flow (Authorization Code + PKCE)".
Actors: User, Relying Party Client, OpenID Provider Authorization Server, UserInfo Endpoint.
Show request parameters including scope=openid profile email, state, nonce, code_challenge.
Show token response including id_token + access_token.
Show client validating id_token (iss, aud, exp, nonce) and creating user session.
Optionally show UserInfo call with access token.
Use clean enterprise design, legible labels, light background, 16:9.
```

## Visual 5: Token Anatomy Infographic
- **Visual Title:** Access Token vs ID Token Anatomy
- **What the Image Should Show:**
  - Side-by-side token cards
  - Common JWT fields (`iss`, `sub`, `aud`, `exp`, `iat`)
  - Scope-focused view for access token
  - Identity-focused view for ID token
  - "Do/Don't" usage guidance
- **Belongs In:** `docs/openid-connect.md` and referenced in `docs/oauth2-vs-oidc.md`
- **Placement in File:**
  - Primary: under "## ID Tokens" in `docs/openid-connect.md`
  - Secondary mention: near comparison table in `docs/oauth2-vs-oidc.md`
- **Why It Improves the Explanation:** Prevents a common implementation error: using ID tokens as API bearer tokens.
- **Ready-to-Use Image Generation Prompt:**

```text
Create an educational infographic titled "Access Token vs ID Token Anatomy".
Split canvas into two panels.
Left panel: Access Token (purpose: API authorization), highlight scope/audience/expiry checks.
Right panel: ID Token (purpose: user authentication), highlight identity claims and nonce.
Include claim labels: iss, sub, aud, exp, iat.
Add a bottom section with Do/Don't:
- Do: use access token for APIs
- Do: validate id token for login
- Don't: send id token to business APIs.
Professional cybersecurity style, clean icons, light background, 4:3.
```

## Visual 6: OAuth 2.0 vs OIDC Comparison Visual
- **Visual Title:** OAuth 2.0 vs OIDC Decision Map
- **What the Image Should Show:**
  - Decision tree or split-panel based on problem statement
  - Branch: "Need API permissions?" -> OAuth
  - Branch: "Need user login identity?" -> OIDC
  - Combined branch for modern app architecture using both
- **Belongs In:** `docs/oauth2-vs-oidc.md`
- **Placement in File:** Right below "## Decision Checklist"
- **Why It Improves the Explanation:** Helps readers choose the right protocol quickly under interview pressure.
- **Ready-to-Use Image Generation Prompt:**

```text
Design a decision-tree style infographic titled "OAuth 2.0 vs OpenID Connect: Which One Do I Need?".
Start with root question: "What problem am I solving?".
Branch 1: "Authorize API access" -> OAuth 2.0.
Branch 2: "Authenticate user identity" -> OpenID Connect.
Branch 3: "Need both login and API access" -> OIDC + OAuth together.
Include small example labels for each branch.
Style: polished technical explainer, white background, navy/teal accents, clear typography, interview-study friendly, 16:9.
```

## Optional Additional Visuals
- Threat model mini-diagram: token theft and replay mitigations (`state`, `nonce`, PKCE, short token lifetime)
- Identity lifecycle diagram: Joiner-Mover-Leaver flow tied to IAM + IGA controls
- Privileged access workflow: request -> approval -> JIT elevation -> session recording -> revoke

> **Best Practice:** Keep a consistent visual style (colors, icon set, font family) across all generated diagrams to make the repo feel cohesive and professional.
