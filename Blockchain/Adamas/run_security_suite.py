"""
CyberShield AI — Master Security Suite Test Runner (v2.2)
=========================================================
Executes all Member 3 security validation and regression test suites:
- SSRF & URL Preflight Security Tests (including port, IPv6, DNS-pinning, trust_env)
- Cryptographic Evidence Hashing & Tamper Detection Tests (including genuine Keccak-256)
- Blockchain Adapter, Chain-ID Verification & Readback Tests
- Member 1 API Contract Schema Compliance, Pydantic v2 & Async Compatibility Tests

Outputs detailed metrics and pass/fail summary.
"""

import hashlib
import sys
import time
import unittest
from pathlib import Path

# Ensure workspace root is always in path regardless of cwd
WORKSPACE_ROOT = Path(__file__).resolve().parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def get_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file for integrity provenance."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_all_security_tests():
    print("=" * 78)
    print("   CyberShield AI 2.0 — Member 3 Security & Verification Suite (v2.2)")
    print("   Workstream: Security Engineering, Cryptography & Blockchain")
    print("=" * 78)

    # Document audited file provenance
    security_files = [
        WORKSPACE_ROOT / "security" / "__init__.py",
        WORKSPACE_ROOT / "security" / "ssrf_validator.py",
        WORKSPACE_ROOT / "security" / "evidence_hasher.py",
        WORKSPACE_ROOT / "security" / "blockchain_adapter.py",
        WORKSPACE_ROOT / "contracts" / "ThreatReportRegistry.sol",
        WORKSPACE_ROOT / "artifacts" / "ThreatReportRegistry.json",
    ]

    print("\n[PROVENANCE] Audited Source Files & Cryptographic Fingerprints:")
    for f in security_files:
        if f.exists():
            h = get_file_sha256(f)
            print(f"  - {f.relative_to(WORKSPACE_ROOT).as_posix()}: {h[:16]}... (len: {f.stat().st_size} bytes)")
        else:
            print(f"  - {f.relative_to(WORKSPACE_ROOT).as_posix()}: [MISSING]")
    print()

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Discover and add test modules
    from tests.test_ssrf_security import TestSSRFSecurity
    from tests.test_cryptography import TestCryptographicIntegrity
    from tests.test_blockchain import TestBlockchainAdapter
    from tests.test_api_contract import TestAPIContractIntegration

    suite.addTests(loader.loadTestsFromTestCase(TestSSRFSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestCryptographicIntegrity))
    suite.addTests(loader.loadTestsFromTestCase(TestBlockchainAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIContractIntegration))

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed = time.time() - start_time

    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - (failed + errors)
    pass_rate = (passed / total * 100) if total > 0 else 0

    print()
    print("=" * 78)
    print("                    SECURITY TEST SUMMARY")
    print("=" * 78)
    print(f"Total Tests Run   : {total}")
    print(f"Passed            : {passed} [ {pass_rate:.1f}% ]")
    print(f"Failed            : {failed}")
    print(f"Errors            : {errors}")
    print(f"Execution Latency : {elapsed:.3f} seconds")
    print("-" * 78)
    if failed == 0 and errors == 0:
        print(">>> ALL SECURITY CONTROLS, CRYPTOGRAPHIC GATES & REGRESSIONS PASSED <<<")
    else:
        print(">>> WARNING: SECURITY CONTROLS FAILED <<<")
    print("=" * 78)

    return 0 if (failed == 0 and errors == 0) else 1


if __name__ == "__main__":
    sys.exit(run_all_security_tests())
