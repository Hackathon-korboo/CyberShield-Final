# PART 07: INPUT VALIDATION AND NORMALIZATION — IMPLEMENTATION DETAILS

## 1. Work Performed
1. Extended `backend/app/utils/sanitizer.py` with enterprise-grade normalizers:
   - `normalize_target_url`: Canonicalizes scheme (http/https), lowercase hostname, IDNA Punycode conversion for homoglyphs, port stripping for default ports, path dot-segment traversal resolution (`/a/../b` -> `/b`).
   - `extract_urls_from_text`: High-precision regex to extract and normalize all embedded URLs in emails or SMS bodies.
   - `extract_phone_numbers`: Regex extractor for domestic and international phone numbers.
   - `parse_email_sender`: RFC-compliant parsing of sender strings into display name, email, and domain.
   - `sanitize_input_text`: Strips hazardous ASCII control characters (`\x00-\x1f\x7f`) while preserving standard newlines and tabs.
2. Updated public utility exports in `backend/app/utils/__init__.py`.
3. Created 8 unit tests in `backend/tests/test_sanitizer.py`.
4. Executed full test suite (35 tests passed).

## 2. Technical Decisions
- **Decision 1: IDNA Punycode Canonicalization:** Encoded Cyrillic/Greek lookalike domains to ASCII Punycode (`xn--...`) so that downstream security rules and DNS queries operate on unambiguous canonical hostnames.
- **Decision 2: Dot-Segment Resolution:** Used `posixpath.normpath` to resolve directory traversal sequences before any security evaluation occurs.
- **Decision 3: Non-Destructive Text Cleaning:** Preserved formatting newlines (`\n`) and tabs (`\t`) in email content while strictly removing null bytes and control codes.
