# CYBERSHIELD AI 2.0 — BACKEND MODULE RESPONSIBILITIES

**Document Version:** 2.0.0  
**Phase:** 01 — Backend Foundation & Architecture  
**Part:** 02 — Backend Architecture Planning  
**Status:** Approved for Implementation  

---

## 1. Directory & Package Responsibility Matrix

| Package / Module Path | Primary Responsibility | Inbound Dependencies (Who can import it) | Outbound Dependencies (What it can import) |
|---|---|---|---|
| `backend/app/main.py` | Application entry point, lifespan management, middleware assembly, router mounting | ASGI server (Uvicorn), tests | `app.core`, `app.api`, `app.middleware` |
| `backend/app/core/config.py` | Centralized type-safe settings management via Pydantic Settings, `.env` file parsing, secret masking | All `app.*` modules | Standard library, `pydantic`, `pydantic-settings` |
| `backend/app/core/logging.py` | Structured logger configuration, secret scrubbing filters, safe formatting | All `app.*` modules | Standard library `logging`, `app.core.config` |
| `backend/app/core/exceptions.py` | Application-specific domain exceptions and standard HTTP exception mapping | `app.services`, `app.engines`, `app.api` | Standard library, `fastapi` |
| `backend/app/core/security.py` | Security utilities, cryptographic helpers, API key validation | `app.api.dependencies`, `app.services` | Standard library `hashlib`, `secrets` |
| `backend/app/schemas/` | Pydantic V2 data contracts (request payloads, response structures, health checks, error models) | `app.api`, `app.services`, `app.engines` | `pydantic`, standard library |
| `backend/app/api/dependencies.py` | Dependency injection providers (settings, services, security credentials) | `app.api.routes` | `app.core`, `app.services` |
| `backend/app/api/routes/` | HTTP controller endpoints, status codes, query/body bindings, OpenAPI tags | `app.main` | `app.schemas`, `app.services`, `app.api.dependencies` |
| `backend/app/services/` | Business orchestration, multi-engine pipeline coordination, risk score aggregation | `app.api.routes` | `app.engines`, `app.schemas`, `app.core` |
| `backend/app/engines/` | Specialized analytical engines (Heuristic, AI, Blockchain) | `app.services` | `app.schemas`, `app.core`, `app.utils`, external client SDKs |
| `backend/app/middleware/` | ASGI middlewares: Correlation ID tracing, CORS enforcement, Security headers, safe access logging | `app.main` | `starlette`, `app.core.config`, `app.core.logging` |
| `backend/app/utils/` | Stateless helpers (URL normalization, IP validation, character encoding) | Any `app.*` module | Standard library |
| `backend/tests/` | Automated test suite (unit tests, integration tests, contract tests) | Standalone (Pytest) | `app.*`, `httpx`, `pytest` |

---

## 2. Invariant Rules for Module Decoupling

1. **No Circular Imports:** Imports must flow strictly downwards from API -> Services -> Engines -> Core/Schemas/Utils.
2. **Schema Purity:** Schemas define data contracts only. They must not contain network calls, database queries, or heavy business logic.
3. **Engine Independence:** Engines must operate independently of FastAPI or HTTP request objects (`Request`, `Response`). They accept pure Python objects or Pydantic models.
4. **Single Entry Point:** The sole application factory and ASGI entry point is `backend/app/main.py`. No competing runner files (`run.py`, `server.py`, `app.py`) shall be created in other directories.
