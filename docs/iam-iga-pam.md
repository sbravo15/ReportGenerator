# IAM, IGA, and PAM Foundations

This guide explains three core identity security domains that are often discussed together but solve different problems.

## Quick Definitions
- **IAM (Identity and Access Management):** Manages digital identities, authentication, and access permissions across systems.
- **IGA (Identity Governance and Administration):** Governs identity lifecycle, access approvals, certifications, and compliance controls.
- **PAM (Privileged Access Management):** Secures, controls, and monitors high-risk privileged accounts and sessions.

## Why These Terms Are Commonly Confused
All three involve users and access, but they focus on different control layers:
- IAM focuses on **access enablement and enforcement**.
- IGA focuses on **policy, governance, and auditability**.
- PAM focuses on **high-risk privileged actions**.

---

## IAM (Identity and Access Management)

### Definition
IAM is the discipline of creating and managing digital identities and controlling which users, services, and devices can access which resources.

### Why It Matters
IAM is the operational core of identity security. It connects users to applications and APIs with consistent authentication and authorization rules.

### Security Purpose
- Verify identity (authentication)
- Enforce least-privilege access (authorization)
- Centralize policy controls (SSO, MFA, conditional access)

### Business Purpose
- Improve employee and customer login experience
- Reduce support tickets with SSO and self-service password reset
- Speed onboarding/offboarding access operations

### Common Real-World Use Cases
- Single Sign-On (SSO) for SaaS apps
- Multi-Factor Authentication (MFA)
- Role-Based Access Control (RBAC)
- API access control via OAuth scopes

### Example Organizational Scenarios
- A company adds SSO to Salesforce, Jira, and Google Workspace through one identity provider.
- A customer-facing app requires MFA for high-risk transactions.
- Engineering teams use federation to access cloud consoles without shared passwords.

### How IAM Differs from IGA and PAM
- IAM enables and enforces access decisions day to day.
- IAM alone does not fully solve governance evidence (IGA) or privileged session control (PAM).

> **Key Takeaway:** IAM answers: "Who are you, and what can you access right now?"

---

## IGA (Identity Governance and Administration)

### Definition
IGA is the governance layer for identity that manages access requests, approvals, role models, periodic access reviews, and compliance evidence.

### Why It Matters
Without governance, access tends to accumulate over time. IGA reduces entitlement sprawl and provides traceability for audits and regulatory requirements.

### Security Purpose
- Enforce policy-based access approvals
- Detect and remediate excessive access
- Prove access decisions and review history

### Business Purpose
- Support compliance (SOX, HIPAA, GDPR, PCI DSS, internal controls)
- Improve audit readiness and reduce manual evidence collection
- Standardize joiner-mover-leaver lifecycle controls

### Common Real-World Use Cases
- Access certification campaigns for managers and app owners
- Automated provisioning/deprovisioning tied to HR events
- Separation of Duties (SoD) conflict checks
- Access request workflows with approval chains

### Example Organizational Scenarios
- Finance systems require quarterly manager recertification of user access.
- An employee changes departments and old entitlements are automatically removed.
- An audit asks: "Who approved this access and when?" and IGA provides the record.

### How IGA Differs from IAM and PAM
- IGA governs access quality and accountability over time.
- IAM provides the enforcement mechanism, but IGA provides governance and audit proof.
- IGA is broader than PAM and not limited to privileged accounts.

> **Best Practice:** Treat IGA as a continuous governance program, not a yearly audit exercise.

> **Key Takeaway:** IGA answers: "Should this access exist, who approved it, and is it still appropriate?"

---

## PAM (Privileged Access Management)

### Definition
PAM secures elevated accounts (admins, root, domain admins, break-glass accounts, service accounts with high privileges) through stricter controls and monitoring.

### Why It Matters
Privileged credentials are high-value targets. If compromised, they can enable lateral movement, data destruction, and full environment takeover.

### Security Purpose
- Restrict and time-bound elevated access
- Protect secrets and privileged credentials
- Record privileged sessions for forensic analysis

### Business Purpose
- Reduce breach impact and operational risk
- Enforce accountability for sensitive admin actions
- Meet regulatory and cyber-insurance control expectations

### Common Real-World Use Cases
- Password vaulting and automatic rotation for admin accounts
- Just-in-Time (JIT) admin elevation with approvals
- Session recording for database and server administrator access
- Privileged command controls and session termination

### Example Organizational Scenarios
- A production database administrator receives 2-hour elevated access after approval.
- Domain admin passwords rotate automatically after every use.
- Security operations reviews recorded privileged sessions after an incident.

### How PAM Differs from IAM and IGA
- PAM is focused on high-risk privileged identities, not all users.
- IAM handles broad authentication/authorization; PAM hardens the most sensitive access.
- IGA can govern privileged access approvals, but PAM provides runtime controls and session oversight.

> **Common Mistake:** Treating MFA alone as sufficient protection for privileged accounts.

> **Key Takeaway:** PAM answers: "How do we tightly control and monitor powerful access so compromise impact is minimized?"

---

## Side-by-Side Comparison

| Concept | Primary Focus | Security Goal | Typical Owners | Typical Controls |
|---|---|---|---|---|
| IAM | Identity lifecycle + authentication/authorization | Correct access enforcement | Identity, IT, Security Engineering | SSO, MFA, RBAC/ABAC, federation |
| IGA | Governance, approvals, reviews, compliance | Access accountability and policy alignment | GRC, Identity Governance, Internal Audit | Access certifications, SoD, request workflows |
| PAM | Privileged account/session protection | Reduce impact of privileged credential abuse | Security Operations, Infrastructure Security | Vaulting, JIT, session recording, rotation |

## How Organizations Use Them Together
1. IAM authenticates users and enforces baseline access.
2. IGA governs who should receive access and validates it over time.
3. PAM applies strong controls for privileged access paths.

> **Interview Tip:** A mature enterprise identity program usually combines IAM + IGA + PAM rather than choosing only one.

## Final Review Checklist
- Can you explain each acronym in one sentence?
- Can you map each acronym to a real control?
- Can you explain how they complement each other in one architecture?

> **Key Takeaway:** IAM, IGA, and PAM are complementary layers in a defense-in-depth identity strategy.
