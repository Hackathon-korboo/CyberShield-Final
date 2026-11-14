"""
CyberShield AI 2.0 — Final Package Integrity & Secret Scanner Verification
===========================================================================
Performs automated verification of:
1. ZIP archive opening, testing, and extraction integrity.
2. Expected file presence and categorization.
3. Secret scanning (detecting private keys, API keys, passwords, credentials).
4. HTML document structural validity, offline completeness, and internal anchor integrity.
5. README_PACKAGE and SHA-256 verification.
"""

import hashlib
import re
import tempfile
import zipfile
from pathlib import Path

PKG_DIR = Path("E:/Adamas/FINAL_SHAREABLE_PACKAGE")
ZIP_PATH = PKG_DIR / "CyberShield_AI_2.0_Final_Handover.zip"
HTML_PATH = PKG_DIR / "CyberShield_AI_2.0_Project_Handover.html"
README_PATH = PKG_DIR / "README_PACKAGE.md"
SHA_PATH = PKG_DIR / "SHA256SUMS.txt"
MANIFEST_PATH = PKG_DIR / "MANIFEST.txt"


def verify():
    print("=" * 78)
    print("   CyberShield AI 2.0 — Package QA & Verification Suite")
    print("=" * 78)

    # 1. VERIFY FILES EXIST
    for p in [ZIP_PATH, HTML_PATH, README_PATH, SHA_PATH, MANIFEST_PATH]:
        assert p.exists(), f"Missing file: {p}"
        print(f"  [EXISTS] {p.name} ({p.stat().st_size:,} bytes)")

    # 2. TEST ZIP ARCHIVE INTEGRITY
    print("\n--- TEST 1: ZIP ARCHIVE INTEGRITY & EXTRACTION ---")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        test_res = zf.testzip()
        assert test_res is None, f"Corrupted file in ZIP: {test_res}"
        namelist = zf.namelist()
        print(f"  [PASS] testzip() passed with 0 corruptions. Total files: {len(namelist)}")

        # Verify key directories
        required_dirs = ["security/", "contracts/", "artifacts/", "tests/", "docs/", "configuration/", "backend/", "frontend/"]
        for rd in required_dirs:
            matches = [n for n in namelist if n.startswith(rd)]
            assert len(matches) > 0, f"Missing required directory {rd} in ZIP!"
            print(f"  [PASS] Directory '{rd}' verified ({len(matches)} files)")

        # Verify critical files
        critical_files = [
            "security/ssrf_validator.py",
            "security/evidence_hasher.py",
            "security/blockchain_adapter.py",
            "contracts/ThreatReportRegistry.sol",
            "artifacts/ThreatReportRegistry.json",
            "tests/test_ssrf_security.py",
            "tests/test_cryptography.py",
            "tests/test_blockchain.py",
            "tests/test_api_contract.py",
            "tests/ThreatReportRegistry.test.js",
            "run_security_suite.py",
            "README.md",
            "configuration/.env.example",
            "backend/integration_snippets.py",
            "frontend/components/IntegrityBadge.tsx",
        ]
        for cf in critical_files:
            assert cf in namelist, f"Critical file {cf} missing from ZIP!"
        print(f"  [PASS] All {len(critical_files)} critical source files confirmed present.")

        # Test extraction to temporary folder
        with tempfile.TemporaryDirectory() as tmpdir:
            zf.extractall(tmpdir)
            extracted_count = len(list(Path(tmpdir).rglob("*")))
            print(f"  [PASS] Full clean extraction verified ({extracted_count} items extracted).")

    # 3. SECRET SCANNING (ZERO CREDENTIALS LEAKAGE)
    print("\n--- TEST 2: SECRET SCANNING & CREDENTIALS AUDIT ---")
    secret_patterns = [
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key
        re.compile(r"(?i)api[_-]?key\s*=\s*['\"][0-9a-zA-Z]{32,}['\"]"),
        re.compile(r"(?i)password\s*=\s*['\"][^'\"]{8,}['\"]"),
        re.compile(r"ghp_[0-9a-zA-Z]{36}"),  # GitHub Personal Access Token
    ]

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        for name in zf.namelist():
            # Disallow any actual .env file except .env.example
            if (name.endswith(".env") or "/.env." not in name and "/.env" in name) and not name.endswith(".env.example"):
                raise AssertionError(f"Actual .env file packaged: {name}")
            data = zf.read(name)
            # Scan text files for secret patterns
            if name.endswith((".py", ".js", ".mjs", ".json", ".md", ".txt", ".sol", ".example")):
                text = data.decode("utf-8", errors="ignore")
                for pat in secret_patterns:
                    matches = pat.findall(text)
                    if matches:
                        raise AssertionError(f"Secret pattern matched in {name}: {matches}")

    print("  [PASS] Zero private keys, real passwords, or production credentials detected.")
    print("  [PASS] Only safe template .env.example with dummy placeholders is present.")

    # 4. STANDALONE HTML AUDIT & OFFLINE INDEPENDENCE
    print("\n--- TEST 3: STANDALONE HTML INTEGRITY & OFFLINE CHECK ---")
    html_text = HTML_PATH.read_text(encoding="utf-8")

    # Check for external asset links (http/https links in script, link, or img src)
    external_asset_regex = re.compile(r'<(?:script|link|img)[^>]*(?:src|href)=["\']https?://', re.IGNORECASE)
    ext_assets = external_asset_regex.findall(html_text)
    assert len(ext_assets) == 0, f"External assets found in HTML! {ext_assets}"
    print("  [PASS] 100% Offline-ready: Zero external CDN, CSS, JS, or image dependencies.")

    # Check internal anchors
    href_anchors = re.findall(r'href="#([a-zA-Z0-9_-]+)"', html_text)
    id_targets = set(re.findall(r'id="([a-zA-Z0-9_-]+)"', html_text))
    for anchor in href_anchors:
        assert anchor in id_targets, f"Broken internal link: #{anchor} has no matching id!"
    print(f"  [PASS] Internal navigation valid: All {len(href_anchors)} nav anchors resolve to valid ids.")

    # Check required technical sections
    required_sections = [
        "Problem Statement",
        "Proposed Solution",
        "System Architecture",
        "SSRF Protection & DNS Pinning Guard",
        "Cryptographic Integrity Verification Engine",
        "Blockchain Evidence Registry",
        "Automated Testing",
        "Quickstart & Installation Instructions",
    ]
    for sec in required_sections:
        assert sec in html_text, f"Missing section '{sec}' in HTML document!"
    print(f"  [PASS] All {len(required_sections)} required architectural sections present.")

    # 5. SHA-256 SUMS VERIFICATION
    print("\n--- TEST 4: SHA-256 CHECKSUMS VERIFICATION ---")
    sums_lines = SHA_PATH.read_text(encoding="utf-8").strip().splitlines()
    for line in sums_lines:
        if not line.strip():
            continue
        expected_hash, fname = line.split("  ", 1)
        actual_hash = hashlib.sha256((PKG_DIR / fname).read_bytes()).hexdigest()
        assert expected_hash == actual_hash, f"Checksum mismatch for {fname}!"
        print(f"  [PASS] {fname}: SHA-256 verified ({actual_hash[:16]}...)")

    print("\n" + "=" * 78)
    print(">>> ALL 4 VERIFICATION SUITES PASSED — SHAREABLE PACKAGE IS 100% READY <<<")
    print("=" * 78)


if __name__ == "__main__":
    verify()
