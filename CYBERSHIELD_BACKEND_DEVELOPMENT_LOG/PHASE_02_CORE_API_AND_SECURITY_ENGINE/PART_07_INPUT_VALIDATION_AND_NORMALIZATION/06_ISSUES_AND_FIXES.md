# PART 07: INPUT VALIDATION AND NORMALIZATION — ISSUES AND FIXES

## Issues Encountered and Resolved

### 1. Preserving Formatting in Email Bodies
- **Issue:** Overly aggressive regex `[\x00-\x1f]` stripped essential formatting newlines (`\n`) and tabs (`\t`), degrading readability of multiline email payloads.
- **Resolution:** Refined `CONTROL_CHAR_REGEX` to `[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]`, explicitly exempting `\t` (0x09), `\n` (0x0A), and `\r` (0x0D).
- **Status:** Resolved and verified.
