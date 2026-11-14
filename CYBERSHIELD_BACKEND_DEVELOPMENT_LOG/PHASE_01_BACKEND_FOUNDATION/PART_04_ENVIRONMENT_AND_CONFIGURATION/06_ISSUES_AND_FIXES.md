# PART 04: ENVIRONMENT AND CONFIGURATION — ISSUES AND FIXES

## Issues Encountered and Resolved

### Issue 1: Ensuring Pydantic Field Validator Compatibility in V2
- **Description:** Pydantic V2 uses `@field_validator` with `mode="before"` instead of V1's `@validator(pre=True)`.
- **Resolution:** Implemented V2-native `@field_validator("cors_origins", mode="before")` and `@classmethod` signatures, guaranteeing clean type coercion and forward compatibility.
- **Status:** Resolved cleanly.

### Issue 2: Flawed Substitution Backreference in SecretScrubbingFilter
- **Description:** In `backend/app/core/logging.py`, `SecretScrubbingFilter` applied `pattern.sub(r"\1[REDACTED]", scrubbed)` generically across all secret patterns. For Pattern 1 (Google API key: `AIza...`), Group 1 captured the key itself, which caused the substitution to retain the raw API key instead of redacting it.
- **Root Cause:** A single generic replacement template `r"\1[REDACTED]"` was applied across disparate regex group structures without rule-specific substitution targets.
- **Resolution:** Re-architected `SECRET_SCRUB_RULES` into explicit `(compiled_pattern, replacement_template)` tuples:
  1. Google API keys (`AIza...`) replaced with `[REDACTED_API_KEY]`.
  2. Bearer tokens replaced with `\g<1>[REDACTED]`.
  3. Key-value secrets (`password="..."`, `api_key=...`) replaced with `\g<1>[REDACTED]\g<3>`.
  Added dedicated unit test `test_secret_scrubbing_log_filter` in `backend/tests/test_config.py` verifying all 3 redactions.
- **Status:** Resolved and verified with 100% test pass rate.
