# PART 05: PYDANTIC SCHEMA DEVELOPMENT — ISSUES AND FIXES

## Issues Encountered and Resolved

### 1. Extra Fields Infiltration Prevention
- **Issue:** Permitting arbitrary extra fields in JSON bodies could allow attackers to bypass strict schema checks or pollute downstream state.
- **Resolution:** Configured `model_config = ConfigDict(extra="forbid")` across all request and response schemas to fail closed on unexpected attributes.
- **Status:** Resolved and tested.
