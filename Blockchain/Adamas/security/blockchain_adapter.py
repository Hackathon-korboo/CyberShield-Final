"""
CyberShield AI — Blockchain Integration & Off-Chain Fallback Adapter (v2.2)
============================================================================
Manages report-hash anchoring and verification on EVM chains.

Key Security Rules:
1. Hash Consistency:
   - Keccak-256 is used for on-chain anchoring and report-ID derivation:
     report_id = keccak256(NAMESPACE + keccak256_report_hash)
   - SHA-256 is used for Member 1 API evidence integrity (integrity.evidence_hash).
   - In both on-chain and off-chain fallback modes, report_integrity.report_hash
     is strictly Keccak-256, ensuring that derive_report_id(report_hash) == report_id
     is always consistent and mathematically verifiable.
2. Dynamic Chain ID verification: Queries and validates actual on-chain network ID.
3. Signer enforcement: Unlocked node accounts are strictly restricted to local dev
   chains (Chain ID 31337 / 1337). External/production networks require explicitly
   configured signers / private keys.
4. Post-transaction readback verification: After registration, the record is immediately
   read back and verified from contract state (getReport and verifyReport).
5. Transparent off-chain fallback: When EVM nodes are unavailable, cleanly provides
   local cryptographic proof without ever faking on-chain transactions or contracts.
6. Output strictly conforms to Member 1's backend schema:
   {
       "integrity": {
           "status": "verified" | "failed" | "not_available",
           "evidence_hash": "<sha256_hash>"
       }
   }
"""

from __future__ import annotations

__version__ = "2.2.0"

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .evidence_hasher import EvidenceHasher, IntegrityResult


# ThreatReportRegistry ABI
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "reportHash", "type": "bytes32"}],
        "name": "registerReport",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "reportId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "reportHash", "type": "bytes32"},
        ],
        "name": "verifyReport",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "reportId", "type": "bytes32"}],
        "name": "getReport",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
            {"internalType": "bytes32", "name": "", "type": "bytes32"},
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "reportHash", "type": "bytes32"}],
        "name": "hashExists",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "reportCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

KNOWN_CHAIN_NAMES: dict[int, str] = {
    1: "Ethereum Mainnet",
    11155111: "Ethereum Sepolia Testnet",
    1337: "Ganache Local Devnet",
    31337: "Hardhat Local Devnet",
}


@dataclass
class BlockchainStatus:
    is_operational: bool
    network: str
    chain_id: int | None
    rpc_url: str
    contract_address: str | None
    report_count: int = 0
    signer_mode: str = "none"  # "private_key" | "local_dev_account" | "none"
    note: str = ""


class BlockchainAdapter:
    """Hybrid Web3 client with verified chain ID, transaction readback, and honest fallback."""

    def __init__(
        self,
        rpc_url: str | None = None,
        contract_address: str | None = None,
        deployment_file: str | Path | None = None,
        private_key: str | None = None,
    ):
        self.rpc_url = rpc_url or os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.contract_address = contract_address or os.getenv("BLOCKCHAIN_CONTRACT_ADDRESS")
        self.deployment_file = deployment_file or Path("deployment.json")
        self.private_key = private_key or os.getenv("BLOCKCHAIN_PRIVATE_KEY")

        self.w3 = None
        self.contract = None
        self.chain_id: int | None = None
        self.network_name: str = "off-chain (local fallback)"
        self.is_operational = False
        self.signer_mode = "none"
        self.status_note = ""

        self._check_operational_status()

    def _check_operational_status(self) -> None:
        """Inspect Web3 connection, verify actual chain ID, and check contract bytecode."""
        try:
            from web3 import Web3
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url, request_kwargs={"timeout": 1.5}))

            if not self.w3.is_connected():
                self.is_operational = False
                self.network_name = "off-chain (local fallback)"
                self.status_note = (
                    f"EVM node offline at {self.rpc_url}. Operating in local cryptographic integrity mode."
                )
                return

            self.chain_id = self.w3.eth.chain_id
            self.network_name = KNOWN_CHAIN_NAMES.get(
                self.chain_id, f"EVM Network (Chain ID: {self.chain_id})"
            )

            if self.private_key:
                self.signer_mode = "private_key"
            elif self.chain_id in (31337, 1337):
                self.signer_mode = "local_dev_account"
            else:
                self.signer_mode = "none"

            if not self.contract_address and Path(self.deployment_file).exists():
                try:
                    data = json.loads(Path(self.deployment_file).read_text())
                    self.contract_address = data.get("contractAddress")
                except Exception:
                    pass

            if not self.contract_address:
                self.is_operational = False
                self.status_note = (
                    f"Connected to {self.network_name}, but no contract address configured or deployed."
                )
                return

            code = self.w3.eth.get_code(self.w3.to_checksum_address(self.contract_address))
            if not code or code == b"" or code.hex() == "0x":
                self.is_operational = False
                self.status_note = (
                    f"No contract bytecode deployed at {self.contract_address} on {self.network_name}."
                )
                return

            self.contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.contract_address),
                abi=CONTRACT_ABI,
            )
            self.is_operational = True
            self.status_note = (
                f"Connected to ThreatReportRegistry at {self.contract_address} on {self.network_name}."
            )

        except Exception as e:
            self.is_operational = False
            self.status_note = f"Blockchain check failed: {e}. Fallback active."

    def get_status(self) -> BlockchainStatus:
        """Return operational status summary."""
        count = 0
        if self.is_operational and self.contract:
            try:
                count = self.contract.functions.reportCount().call()
            except Exception:
                count = 0

        return BlockchainStatus(
            is_operational=self.is_operational,
            network=self.network_name,
            chain_id=self.chain_id,
            rpc_url=self.rpc_url,
            contract_address=self.contract_address if self.is_operational else None,
            report_count=count,
            signer_mode=self.signer_mode,
            note=self.status_note,
        )

    def register_report(
        self,
        report_data: dict[str, Any],
        sender_account: str | None = None,
    ) -> dict[str, Any]:
        """
        Anchor report hash on-chain if operational; otherwise preserve off-chain.
        Maintains bit-exact mathematical consistency:
        - report_integrity.report_hash is ALWAYS Keccak-256.
        - report_integrity.report_id is ALWAYS derived from report_hash.
        - integrity.evidence_hash is ALWAYS SHA-256 (Member 1 API contract).
        """
        sha256_hash = EvidenceHasher.hash_report(report_data, algorithm="sha256")
        keccak_hash = EvidenceHasher.hash_report(report_data, algorithm="keccak256")
        derived_id = EvidenceHasher.derive_report_id(keccak_hash)

        # 1. On-Chain registration when operational
        if self.is_operational and self.contract and self.w3:
            try:
                hash_bytes32 = bytes.fromhex(keccak_hash.removeprefix("0x"))
                id_bytes32 = bytes.fromhex(derived_id.removeprefix("0x"))

                already_exists = self.contract.functions.hashExists(hash_bytes32).call()
                if already_exists:
                    on_chain_rec = self.contract.functions.getReport(id_bytes32).call()
                    return {
                        "integrity": {
                            "status": "verified",
                            "evidence_hash": sha256_hash,
                        },
                        "report_integrity": {
                            "report_hash": keccak_hash,
                            "report_id": derived_id,
                            "keccak256_report_hash": keccak_hash,
                            "sha256_evidence_hash": sha256_hash,
                            "algorithm": "keccak256",
                            "blockchain_network": self.network_name,
                            "chain_id": self.chain_id,
                            "contract_address": self.contract_address,
                            "registered_by": on_chain_rec[2],
                            "registered_at": on_chain_rec[3],
                            "verification_status": "already_registered_on_chain",
                            "readback_verified": True,
                            "is_on_chain": True,
                            "note": "Report fingerprint was previously registered on-chain and confirmed via readback.",
                        },
                    }

                if self.private_key:
                    acct = self.w3.eth.account.from_key(self.private_key)
                    from_address = acct.address
                elif self.chain_id in (31337, 1337):
                    from_address = sender_account or self.w3.eth.accounts[0]
                else:
                    raise PermissionError(
                        f"External network ({self.network_name}) requires an explicitly configured "
                        "private key or signer. Unlocked node accounts are prohibited."
                    )

                if self.private_key:
                    acct = self.w3.eth.account.from_key(self.private_key)
                    nonce = self.w3.eth.get_transaction_count(acct.address)
                    tx = self.contract.functions.registerReport(hash_bytes32).build_transaction({
                        "from": acct.address,
                        "nonce": nonce,
                        "gas": 200000,
                        "maxFeePerGas": self.w3.to_wei("2", "gwei"),
                        "maxPriorityFeePerGas": self.w3.to_wei("1", "gwei"),
                    })
                    signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                else:
                    tx_hash = self.contract.functions.registerReport(hash_bytes32).transact({"from": from_address})

                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)

                if receipt.status != 1:
                    return {
                        "integrity": {
                            "status": "failed",
                            "evidence_hash": sha256_hash,
                        },
                        "report_integrity": {
                            "report_hash": keccak_hash,
                            "report_id": derived_id,
                            "keccak256_report_hash": keccak_hash,
                            "sha256_evidence_hash": sha256_hash,
                            "algorithm": "keccak256",
                            "blockchain_network": self.network_name,
                            "chain_id": self.chain_id,
                            "contract_address": self.contract_address,
                            "transaction_hash": receipt.transactionHash.hex(),
                            "verification_status": "transaction_reverted",
                            "readback_verified": False,
                            "is_on_chain": False,
                            "note": "Blockchain transaction reverted during registration.",
                        },
                    }

                readback_record = self.contract.functions.getReport(id_bytes32).call()
                readback_valid = (
                    readback_record[1] == hash_bytes32
                    and self.contract.functions.verifyReport(id_bytes32, hash_bytes32).call()
                )

                if not readback_valid:
                    return {
                        "integrity": {
                            "status": "failed",
                            "evidence_hash": sha256_hash,
                        },
                        "report_integrity": {
                            "report_hash": keccak_hash,
                            "report_id": derived_id,
                            "keccak256_report_hash": keccak_hash,
                            "sha256_evidence_hash": sha256_hash,
                            "algorithm": "keccak256",
                            "blockchain_network": self.network_name,
                            "chain_id": self.chain_id,
                            "contract_address": self.contract_address,
                            "transaction_hash": receipt.transactionHash.hex(),
                            "verification_status": "readback_verification_failed",
                            "readback_verified": False,
                            "is_on_chain": False,
                            "note": "Transaction succeeded but post-registration contract readback verification failed.",
                        },
                    }

                return {
                    "integrity": {
                        "status": "verified",
                        "evidence_hash": sha256_hash,
                    },
                    "report_integrity": {
                        "report_hash": keccak_hash,
                        "report_id": derived_id,
                        "keccak256_report_hash": keccak_hash,
                        "sha256_evidence_hash": sha256_hash,
                        "algorithm": "keccak256",
                        "blockchain_network": self.network_name,
                        "chain_id": self.chain_id,
                        "contract_address": self.contract_address,
                        "transaction_hash": receipt.transactionHash.hex(),
                        "block_number": receipt.blockNumber,
                        "registered_by": readback_record[2],
                        "registered_at": readback_record[3],
                        "verification_status": "registered_on_chain",
                        "readback_verified": True,
                        "is_on_chain": True,
                        "note": "Report fingerprint successfully anchored to blockchain and confirmed via contract readback.",
                    },
                }

            except Exception as e:
                return {
                    "integrity": {
                        "status": "verified",
                        "evidence_hash": sha256_hash,
                    },
                    "report_integrity": {
                        "report_hash": keccak_hash,
                        "report_id": derived_id,
                        "keccak256_report_hash": keccak_hash,
                        "sha256_evidence_hash": sha256_hash,
                        "algorithm": "keccak256",
                        "blockchain_network": "off-chain (local cryptographic fallback)",
                        "chain_id": None,
                        "contract_address": None,
                        "transaction_hash": None,
                        "verification_status": "off_chain_verified",
                        "readback_verified": False,
                        "is_on_chain": False,
                        "note": f"On-chain anchoring failed ({e}). Cryptographic integrity preserved off-chain.",
                    },
                }

        # 2. Off-Chain Fallback Mode (Consistent Keccak report_id and SHA-256 evidence_hash)
        return {
            "integrity": {
                "status": "verified",
                "evidence_hash": sha256_hash,
            },
            "report_integrity": {
                "report_hash": keccak_hash,
                "report_id": derived_id,
                "keccak256_report_hash": keccak_hash,
                "sha256_evidence_hash": sha256_hash,
                "algorithm": "keccak256",
                "blockchain_network": "off-chain (local cryptographic proof)",
                "chain_id": None,
                "contract_address": None,
                "transaction_hash": None,
                "verification_status": "off_chain_verified",
                "readback_verified": False,
                "is_on_chain": False,
                "note": (
                    "Smart contract deployment unavailable. Cryptographic integrity "
                    "verified locally using deterministic Keccak-256 report ID and SHA-256 evidence hash."
                ),
            },
        }

    def verify_report(
        self,
        report_data: dict[str, Any],
        expected_hash: str,
        report_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Verify report against expected hash and on-chain record if available.
        Supports both SHA-256 and Keccak-256 expected hashes.
        """
        # Determine algorithm of expected_hash
        clean_exp = expected_hash.lower().removeprefix("0x")
        algo = "sha256" if len(clean_exp) == 64 and not expected_hash.startswith("0x") else "keccak256"

        local_result = EvidenceHasher.verify_integrity(report_data, expected_hash, algorithm=algo)
        if local_result.status != "verified":
            return {
                "integrity": local_result.to_api_contract()["integrity"],
                "report_integrity": {
                    "verification_status": "failed",
                    "tamper_detected": True,
                    "details": local_result.details,
                    "is_on_chain": False,
                },
            }

        if self.is_operational and self.contract and self.w3 and report_id:
            try:
                keccak_hash = EvidenceHasher.hash_report(report_data, algorithm="keccak256")
                hash_bytes32 = bytes.fromhex(keccak_hash.removeprefix("0x"))
                id_bytes32 = bytes.fromhex(report_id.removeprefix("0x"))

                on_chain_valid = self.contract.functions.verifyReport(id_bytes32, hash_bytes32).call()
                if on_chain_valid:
                    rec = self.contract.functions.getReport(id_bytes32).call()
                    return {
                        "integrity": {
                            "status": "verified",
                            "evidence_hash": local_result.evidence_hash,
                        },
                        "report_integrity": {
                            "verification_status": "on_chain_verified",
                            "blockchain_network": self.network_name,
                            "chain_id": self.chain_id,
                            "contract_address": self.contract_address,
                            "registered_by": rec[2],
                            "registered_at": rec[3],
                            "tamper_detected": False,
                            "readback_verified": True,
                            "is_on_chain": True,
                            "details": "Report verified successfully against both local hash and on-chain smart contract.",
                        },
                    }
                else:
                    return {
                        "integrity": {
                            "status": "failed",
                            "evidence_hash": local_result.evidence_hash,
                        },
                        "report_integrity": {
                            "verification_status": "on_chain_mismatch",
                            "blockchain_network": self.network_name,
                            "chain_id": self.chain_id,
                            "contract_address": self.contract_address,
                            "tamper_detected": True,
                            "readback_verified": False,
                            "is_on_chain": True,
                            "details": "Local hash passed, but on-chain smart contract does not match this report ID.",
                        },
                    }
            except Exception:
                pass

        return {
            "integrity": local_result.to_api_contract()["integrity"],
            "report_integrity": {
                "verification_status": "off_chain_verified",
                "blockchain_network": "off-chain (local cryptographic proof)",
                "tamper_detected": False,
                "readback_verified": False,
                "is_on_chain": False,
                "details": local_result.details,
            },
        }
