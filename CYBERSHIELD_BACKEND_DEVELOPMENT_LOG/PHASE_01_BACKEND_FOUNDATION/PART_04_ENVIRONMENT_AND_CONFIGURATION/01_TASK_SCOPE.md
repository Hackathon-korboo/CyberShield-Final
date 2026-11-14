# PART 04: ENVIRONMENT AND CONFIGURATION — TASK SCOPE

## 1. Goal & Objective
Establish a centralized, type-safe, and secure configuration management system using Pydantic Settings, configure environment loading with defensive defaults, provide a sanitised `.env.example`, configure safe logging and CORS, and document setup and execution procedures.

## 2. In-Scope Tasks
1. Inspect runtime Python version and environment capabilities.
2. Implement centralized Pydantic `BaseSettings` (`backend/app/core/config.py`).
3. Create `.env.example` documenting all configuration keys (Host, Port, Environment, CORS origins, Logging, Gemini API key placeholder, Blockchain RPC placeholder).
4. Verify strict secret protection (no real secrets in source or logs; masked representation of sensitive keys).
5. Configure safe logging defaults with zero credential reflection.
6. Verify CORS settings compatible with development frontends while remaining secure.
7. Document installation, environment configuration, and execution instructions.
8. Execute self-tests validating configuration loading from default values and `.env`.

## 3. Out-of-Scope Tasks
- Hardcoding real API keys or sensitive values.
- Weakening security controls for convenience.
- Deploying to production environments.

## 4. Acceptance Criteria
- Centralized configuration loads cleanly via Pydantic Settings.
- `.env.example` provided with safe placeholder values and clear descriptions.
- Sensitive fields properly masked during serialization and logging.
- Configuration tests pass without error.
