# CyberShield AI 2.0 — GitHub Organization to Vercel Automatic Deployment Report

**Document Reference**: `CYBERSHIELD_GITHUB_AUTO_DEPLOYMENT_REPORT`  
**Classification**: CI/CD & Automated DevOps Architecture  
**GitHub Organization**: `Hackathon-korboo`  
**GitHub Repository**: `https://github.com/Hackathon-korboo/CyberShield-Final`  
**Production Branch**: `main`  
**Status**: CONFIGURED & ACTIVATED  

---

## 1. Automated Deployment Architecture

The CyberShield AI 2.0 repository uses a structured monorepo layout containing both frontend and backend modules. To achieve seamless, zero-maintenance production updates, the GitHub repository has been directly integrated into the Vercel platform using the native GitHub App integration.

```
                  Developer Local Push
             (D:\My Created Projects\new member 2)
                           │
                           ▼
          ┌───────────────────────────────────┐
          │     GitHub Organization Repo      │
          │ Hackathon-korboo/CyberShield-Final│
          │           Branch: main            │
          └───────────────────────────────────┘
                           │
                Automated Webhook Event
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  ┌───────────────────────┐   ┌───────────────────────┐
  │  Vercel Frontend App  │   │  Vercel Backend App   │
  │  (cybershield-ai-web) │   │  (cybershield-ai-api) │
  │  Root: frontend       │   │  Root: backend        │
  └───────────────────────┘   └───────────────────────┘
             │                           │
      Build & Optimize           Deploy ASGI Lambda
             │                           │
             ▼                           ▼
  https://cybershield-ai-    https://cybershield-ai-
     web-roan.vercel.app            api.vercel.app
```

---

## 2. Monorepo Root Directory Configuration

Because both projects live in a single repository, independent root directories are configured on Vercel to isolate builds and prevent unnecessary redeployments:

### Project 1: Frontend (`cybershield-ai-web`)
- **Project ID**: `prj_3RJ3RDtlcj4Cqp0jviflTU3nWUnB`
- **Root Directory**: `frontend`
- **Framework Preset**: Vite / Static
- **Build Command**: Auto-detected (`npm run build` or static output)
- **Output Directory**: `dist` (or root if serving pre-bundled SPA)
- **Automatic Trigger Filter**: Vercel inspects the git commit diff. Only commits modifying files inside `frontend/**` or global dependencies trigger a frontend rebuild.

### Project 2: Backend (`cybershield-ai-api`)
- **Project ID**: `prj_3bD2Oyk7hBm9Ub7qqcXfgpsxcNf0`
- **Root Directory**: `backend`
- **Framework Preset**: Other (Python Serverless Function)
- **Entry File**: `api/index.py`
- **Automatic Trigger Filter**: Only commits modifying files inside `backend/**` trigger a backend serverless function build and deployment.

---

## 3. GitHub Branch Strategy & Automated Triggers

### A. Direct Push to `main`
- Any code merged into or pushed directly to `main` immediately triggers a **Production Deployment**.
- Vercel automatically assigns the live production domain aliases:
  - `cybershield-ai-web-roan.vercel.app`
  - `cybershield-ai-api.vercel.app`
- Deployment status is reported back to GitHub as an official commit check badge (`vercel / deployment — Success`).

### B. Pull Request (PR) Workflow
- When a developer creates a feature branch (e.g. `feat/new-threat-engine` or `fix/model-tuning`), opening a Pull Request against `main` automatically triggers a **Preview Deployment**.
- A unique preview URL (e.g. `cybershield-ai-web-git-feat-threat.vercel.app`) is generated and commented on the PR.
- This allows team members to verify features in isolation before merging into `main`.

---

## 4. Rollback and Zero-Downtime Guarantee

1. **Instant Rollback**: If a commit introduces a regression in production, any previous deployment in Vercel can be instantly promoted to production with zero rebuild time (< 500ms).
2. **Immutable Artifacts**: Every deployment is permanently preserved and addressable by its unique deployment ID (`dpl_*`).
3. **Atomic Swaps**: Incoming user traffic is instantly switched to the new deployment only after the serverless function passes container compilation and health checks.
