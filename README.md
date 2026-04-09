# Identity and Access Management Fundamentals: IAM, OAuth 2.0, and OpenID Connect

A portfolio-ready documentation project that explains core Identity and Access Management (IAM) concepts and modern authentication/authorization protocols used in real production systems.

## Professional Summary
This repository demonstrates practical understanding of identity security fundamentals, including IAM, IGA, PAM, OAuth 2.0, and OpenID Connect (OIDC). It is written as both:
- A technical portfolio artifact for interviews and recruiter review
- A structured study guide for self-paced learning and revision

## Why This Project Exists
Identity is a primary control plane for modern security. Most breaches involve weak authentication, over-privileged access, mismanaged credentials, or broken session/token handling. This project exists to provide a clear, practical foundation for designing and reviewing secure identity architectures.

## Topics Covered
- IAM vs IGA vs PAM foundations
- OAuth 2.0 roles, tokens, scopes, grant flows, and PKCE
- OpenID Connect authentication model on top of OAuth 2.0
- ID tokens, claims, discovery, JWKS, and token validation
- OAuth 2.0 vs OIDC decision-making for real-world scenarios
- Suggested visuals to improve technical communication

## Who This Project Is For
- Security analysts and engineers building identity fundamentals
- Developers integrating enterprise SSO, API authorization, and federated login
- Students preparing for IAM/security interviews
- Teams creating internal identity documentation and onboarding material

## Table of Contents
| Document | Purpose |
|---|---|
| [`README.md`](./README.md) | Project overview and navigation |
| [`docs/iam-iga-pam.md`](./docs/iam-iga-pam.md) | Foundational glossary for IAM, IGA, and PAM |
| [`docs/oauth2.md`](./docs/oauth2.md) | Deep technical guide to OAuth 2.0 |
| [`docs/openid-connect.md`](./docs/openid-connect.md) | Deep technical guide to OpenID Connect |
| [`docs/oauth2-vs-oidc.md`](./docs/oauth2-vs-oidc.md) | Practical comparison and decision guide |
| [`docs/suggested-visuals.md`](./docs/suggested-visuals.md) | Image concepts and generation prompts |

## How to Use This Repo
1. Start with [`docs/iam-iga-pam.md`](./docs/iam-iga-pam.md) to build terminology and mental models.
2. Continue with [`docs/oauth2.md`](./docs/oauth2.md) to understand delegated authorization and API access.
3. Read [`docs/openid-connect.md`](./docs/openid-connect.md) to understand authentication and user identity.
4. Use [`docs/oauth2-vs-oidc.md`](./docs/oauth2-vs-oidc.md) for interview prep and quick conceptual checks.
5. Use [`docs/suggested-visuals.md`](./docs/suggested-visuals.md) to add architecture diagrams and explainers.

> **Interview Tip:** Be ready to explain OAuth 2.0 and OIDC in one sentence each, then justify when each is used in a real architecture.

## Why This Matters in Security
- Identity controls who can access systems and data.
- Authorization models define what actions are allowed.
- Strong token handling reduces account takeover and API abuse risk.
- Privileged access controls reduce blast radius during incidents.
- Governance and lifecycle controls reduce entitlement sprawl and compliance exposure.

> **Key Takeaway:** If identity design is weak, every downstream security control becomes easier to bypass.

## Conclusion
This project is designed to be practical, interview-ready, and production-relevant. It focuses on the identity knowledge that engineers and security teams use daily to build secure login, API access, governance, and privileged access workflows.
