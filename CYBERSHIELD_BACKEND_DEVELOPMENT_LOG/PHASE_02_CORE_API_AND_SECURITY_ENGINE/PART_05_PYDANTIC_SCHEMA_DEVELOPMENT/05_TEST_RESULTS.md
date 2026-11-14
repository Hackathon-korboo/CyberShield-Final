# PART 05: PYDANTIC SCHEMA DEVELOPMENT — TEST RESULTS

## 1. Unit Test Results

| Test Identifier | Description | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|---|
| `test_valid_url_analysis_request` | Test legitimate URL parsing | Valid request object instantiated | Parsed successfully | PASSED |
| `test_invalid_url_analysis_request` | Reject empty, ftp, control characters, extra fields | ValidationError raised with descriptive detail | ValidationError raised on all cases | PASSED |
| `test_valid_email_analysis_request` | Parse subject, sender, and body | Instantiated correctly | Parsed successfully | PASSED |
| `test_invalid_email_analysis_request` | Reject whitespace and null bytes | ValidationError raised | ValidationError raised | PASSED |
| `test_valid_sms_analysis_request` | Parse sender and message text | Instantiated correctly | Parsed successfully | PASSED |
| `test_invalid_sms_analysis_request` | Reject empty SMS | ValidationError raised | ValidationError raised | PASSED |
| `test_security_indicator_schema` | Validate Indicator model serialization | Serializes with enums | Matches schema | PASSED |
| `test_url_analysis_response_schema` | Validate composite response structure | Serializes with evidence and findings | Matches schema | PASSED |

**Total:** 8 schema unit tests executed, 8 passed, 0 failed.
