# PART 07: INPUT VALIDATION AND NORMALIZATION — TASK SCOPE

## 1. Goal & Objective
Implement rigorous, multi-layered input sanitization and normalization for all user-submitted content (URLs, email headers/bodies, SMS messages) to eliminate malformed characters, normalize Unicode/Punycode representations, and enforce defensive constraints.

## 2. In-Scope Tasks
1. Extend `backend/app/utils/sanitizer.py` with specialized normalizers:
   - URL normalization (scheme validation, lowercase netloc, trailing slash handling, port extraction).
   - Punycode / IDN normalization (`idna.encode` / `idna.decode` / homoglyph normalization).
   - Email normalization (whitespace trimming, sender address parsing, header/body separation).
   - SMS message normalization (control character stripping, null byte removal, space collapse).
2. Author comprehensive test suite covering empty inputs, whitespace-only, massive strings, internationalized domains, control characters, and malformed syntax.

## 3. Out-of-Scope Tasks
- Transforming or mutating input semantics silently.
- Performing live network calls during normalization.

## 4. Acceptance Criteria
- Valid inputs are normalized to canonical representations.
- Malformed or illegal inputs raise explicit validation errors.
- Zero unhandled exceptions or crashes on hostile input.
