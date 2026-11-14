"""
CyberShield AI 2.0 - Privacy Protection & PII Redaction Module
Performs comprehensive client-side data minimization, redacting sensitive personal
and financial information before transmission to any external model or logging service.
"""

import re
from typing import List, Tuple, Dict
from backend.app.schemas.threat_models import PIIEntity


def _luhn_checksum_valid(number_str: str) -> bool:
    """Validate numeric string using Luhn algorithm for credit card numbers."""
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


class PIIRedactor:
    """Comprehensive PII detection and redaction engine."""

    # Pre-compiled high-precision regular expressions
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        re.IGNORECASE
    )

    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?[6-9]\d{4}[-.\s]?\d{5}\b|'
        r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )

    CARD_PATTERN = re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b'
    )

    PAN_PATTERN = re.compile(
        r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b'
    )

    AADHAAR_PATTERN = re.compile(
        r'\b[2-9]\d{3}[-\s]\d{4}[-\s]\d{4}\b'
    )

    UPI_PATTERN = re.compile(
        r'\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b'
    )

    IFSC_PATTERN = re.compile(
        r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
    )

    OTP_CONTEXT_PATTERN = re.compile(
        r'(?i)(?:otp|one\s*time\s*password|verification\s*code|pin|code\s*is|secret\s*code)[\s:=#\-\.]*(\b\d{4,8}\b)'
    )

    BANK_ACCOUNT_PATTERN = re.compile(
        r'(?i)(?:a/c|acc|account|acct)[\s.:#\-no]*([0-9]{9,18})\b'
    )

    PASSWORD_CONTEXT_PATTERN = re.compile(
        r'(?i)(?:password|passwd|pwd|passcode|mpin|secret|token)[\s:=#\-]+([^\s,;]+)'
    )

    def redact(self, text: str) -> Tuple[str, List[PIIEntity]]:
        """
        Redact sensitive PII from input text.

        Returns:
            Tuple[str, List[PIIEntity]]: Sanitized text string and list of detected PII entities.
        """
        if not text:
            return "", []

        entity_counts: Dict[str, Dict[str, Any]] = {}
        sanitized = text

        def record_entity(etype: str, masked_val: str):
            if etype not in entity_counts:
                entity_counts[etype] = {"type": etype, "masked": masked_val, "count": 0}
            entity_counts[etype]["count"] += 1

        # 1. Redact Passwords / MPINs in context
        def redact_password(match):
            pwd = match.group(1)
            # Avoid redacting common filler words
            if pwd.lower() in {"is", "was", "will", "the", "a", "an", "here", "to"}:
                return match.group(0)
            record_entity("CREDENTIAL", "[CREDENTIAL_REDACTED]")
            prefix = match.group(0)[:match.start(1) - match.start(0)]
            return f"{prefix}[CREDENTIAL_REDACTED]"

        sanitized = self.PASSWORD_CONTEXT_PATTERN.sub(redact_password, sanitized)

        # 2. Redact OTPs in context
        def redact_otp(match):
            record_entity("OTP", "[OTP_REDACTED]")
            prefix = match.group(0)[:match.start(1) - match.start(0)]
            return f"{prefix}[OTP_REDACTED]"

        sanitized = self.OTP_CONTEXT_PATTERN.sub(redact_otp, sanitized)

        # 3. Redact Credit / Debit Card numbers (with Luhn check where applicable)
        def redact_cards(match):
            val = match.group(0)
            clean_digits = re.sub(r'\D', '', val)
            if len(clean_digits) in (15, 16) or _luhn_checksum_valid(clean_digits):
                masked = f"****-****-****-{clean_digits[-4:]}"
                record_entity("CARD_NUMBER", masked)
                return "[CARD_NUMBER_REDACTED]"
            return val

        sanitized = self.CARD_PATTERN.sub(redact_cards, sanitized)

        # 4. Redact Bank Account numbers in context
        def redact_bank(match):
            record_entity("BANK_ACCOUNT", "[BANK_ACCOUNT_REDACTED]")
            prefix = match.group(0)[:match.start(1) - match.start(0)]
            return f"{prefix}[BANK_ACCOUNT_REDACTED]"

        sanitized = self.BANK_ACCOUNT_PATTERN.sub(redact_bank, sanitized)

        # 5. Redact IFSC codes
        def redact_ifsc(match):
            record_entity("IFSC_CODE", "[IFSC_REDACTED]")
            return "[IFSC_REDACTED]"

        sanitized = self.IFSC_PATTERN.sub(redact_ifsc, sanitized)

        # 6. Redact Aadhaar Numbers
        def redact_aadhaar(match):
            record_entity("AADHAAR", "[AADHAAR_REDACTED]")
            return "[AADHAAR_REDACTED]"

        sanitized = self.AADHAAR_PATTERN.sub(redact_aadhaar, sanitized)

        # 7. Redact PAN Cards
        def redact_pan(match):
            record_entity("PAN_CARD", "[PAN_REDACTED]")
            return "[PAN_REDACTED]"

        sanitized = self.PAN_PATTERN.sub(redact_pan, sanitized)

        # 8. Redact UPI IDs (must be careful not to clash with standard email, check typical upi handles)
        upi_handles = {
            "okaxis", "okhdfcbank", "okicici", "oksbi", "paytm", "ybl", "ibl",
            "axl", "upi", "apl", "rapl", "icici", "sbi", "hdfcbank", "barodampay"
        }

        def redact_upi(match):
            val = match.group(0)
            handle = val.split("@")[-1].lower()
            if handle in upi_handles:
                record_entity("UPI_ID", "[UPI_ID_REDACTED]")
                return "[UPI_ID_REDACTED]"
            return val

        sanitized = self.UPI_PATTERN.sub(redact_upi, sanitized)

        # 9. Redact Emails
        def redact_email(match):
            val = match.group(0)
            record_entity("EMAIL", "[EMAIL_REDACTED]")
            return "[EMAIL_REDACTED]"

        sanitized = self.EMAIL_PATTERN.sub(redact_email, sanitized)

        # 10. Redact Phone numbers
        def redact_phone(match):
            val = match.group(0)
            # Filter out non-phone numbers like dates or short IDs
            digits_only = re.sub(r'\D', '', val)
            if len(digits_only) >= 10:
                record_entity("PHONE", "[PHONE_REDACTED]")
                return "[PHONE_REDACTED]"
            return val

        sanitized = self.PHONE_PATTERN.sub(redact_phone, sanitized)

        entities = [
            PIIEntity(
                entity_type=info["type"],
                masked_value=info["masked"],
                occurrences=info["count"]
            )
            for info in entity_counts.values()
        ]

        return sanitized, entities


# Module-level singleton instance
redactor_instance = PIIRedactor()


def redact_pii(text: str) -> Tuple[str, List[PIIEntity]]:
    """Helper entry point for PII redaction."""
    return redactor_instance.redact(text)


def safe_log_mask(text: str, max_length: int = 200) -> str:
    """Mask text for safe logging without writing PII to log files."""
    cleaned, _ = redactor_instance.redact(text)
    if len(cleaned) > max_length:
        return cleaned[:max_length] + " [TRUNCATED]..."
    return cleaned
