# PART 07: INPUT VALIDATION AND NORMALIZATION — FILES CREATED OR MODIFIED

## 1. Files Created
1. `backend/tests/test_sanitizer.py` — 8 unit tests for URL normalization, IDNA conversion, path dot-segments, text extraction, and control character scrubbing.

## 2. Files Modified
1. `backend/app/utils/sanitizer.py` — Added IDNA Punycode normalization, dot-segment resolution, URL extraction, phone extraction, and sender parsing.
2. `backend/app/utils/__init__.py` — Exported new sanitization utilities.
