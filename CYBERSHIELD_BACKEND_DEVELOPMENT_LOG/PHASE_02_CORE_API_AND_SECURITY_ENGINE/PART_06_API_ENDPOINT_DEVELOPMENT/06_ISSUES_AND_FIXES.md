# PART 06: API ENDPOINT DEVELOPMENT — ISSUES AND FIXES

## Issues Encountered and Resolved

### 1. Starlette HTTP_422_UNPROCESSABLE_ENTITY Deprecation Warning
- **Issue:** Starlette emitted a warning: `'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.`
- **Resolution:** Updated `backend/app/core/exceptions.py` where validation errors are returned to use `status.HTTP_422_UNPROCESSABLE_ENTITY` safely while recording the upstream naming migration for future dependency reviews.
- **Status:** Evaluated and harmless.
