// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title ThreatReportRegistry
 * @author CyberShield AI — Member 3 (Security Engineering & Blockchain)
 * @notice Immutable on-chain registry for CyberShield AI threat reports.
 *         Stores ONLY cryptographic fingerprints — never sensitive data.
 *
 * Security principles:
 *   - Zero PII / raw data on-chain: No URLs, email bodies, passwords, or IP addresses.
 *   - Cryptographic integrity: Only Keccak-256 fingerprint, report ID, timestamp, and registrar.
 *   - Role-Based Access Control (RBAC): Only owner or authorized registrars can register reports.
 *   - Duplicate prevention: Identical report hashes cannot be registered twice.
 *   - Non-zero hash guard: Prevents empty hash registration.
 */
contract ThreatReportRegistry {

    // ──────────────────────────────────────────────
    //  Constants
    // ──────────────────────────────────────────────

    /// @dev Fixed namespace prevents cross-application hash collisions.
    string private constant NAMESPACE = "CYBERSHIELD_REPORT_V1";

    // ──────────────────────────────────────────────
    //  Data structures
    // ──────────────────────────────────────────────

    struct Report {
        bytes32 reportId;
        bytes32 reportHash;
        address registeredBy;
        uint256 registeredAt;
    }

    // ──────────────────────────────────────────────
    //  State
    // ──────────────────────────────────────────────

    /// @dev Contract administrator
    address public owner;

    /// @dev Allowed backend registrar services
    mapping(address => bool) public authorizedRegistrars;

    /// @dev Report ID  →  full Report record
    mapping(bytes32 => Report) private reports;

    /// @dev Report hash  →  already registered?
    mapping(bytes32 => bool) public hashExists;

    /// @dev Running count of registered reports
    uint256 public reportCount;

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    event ReportRegistered(
        bytes32 indexed reportId,
        bytes32 indexed reportHash,
        address indexed registeredBy,
        uint256 registeredAt
    );

    event RegistrarUpdated(
        address indexed registrar,
        bool authorized
    );

    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    // ──────────────────────────────────────────────
    //  Modifiers
    // ──────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the contract owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner || authorizedRegistrars[msg.sender],
            "Caller is not authorized to register reports"
        );
        _;
    }

    // ──────────────────────────────────────────────
    //  Constructor
    // ──────────────────────────────────────────────

    constructor() {
        owner = msg.sender;
        authorizedRegistrars[msg.sender] = true;
        emit RegistrarUpdated(msg.sender, true);
    }

    // ──────────────────────────────────────────────
    //  Admin functions
    // ──────────────────────────────────────────────

    /**
     * @notice Authorize or revoke a backend registrar service address.
     */
    function setRegistrar(address registrar, bool authorized) external onlyOwner {
        require(registrar != address(0), "Invalid registrar address");
        authorizedRegistrars[registrar] = authorized;
        emit RegistrarUpdated(registrar, authorized);
    }

    /**
     * @notice Transfer ownership of the registry to a new administrator.
     *         Explicitly revokes the previous owner's registrar privileges and grants them to the new owner.
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid new owner");
        address previousOwner = owner;
        authorizedRegistrars[previousOwner] = false;
        emit RegistrarUpdated(previousOwner, false);
        authorizedRegistrars[newOwner] = true;
        emit RegistrarUpdated(newOwner, true);
        emit OwnershipTransferred(previousOwner, newOwner);
        owner = newOwner;
    }

    // ──────────────────────────────────────────────
    //  Pure helpers
    // ──────────────────────────────────────────────

    /**
     * @notice Derive a deterministic report ID from a report hash.
     * @dev    ID = keccak256(NAMESPACE ‖ reportHash)
     *         Identical hashes always produce the same ID.
     */
    function generateReportId(bytes32 reportHash) public pure returns (bytes32) {
        return keccak256(
            abi.encodePacked(NAMESPACE, reportHash)
        );
    }

    // ──────────────────────────────────────────────
    //  Write: register
    // ──────────────────────────────────────────────

    /**
     * @notice Register a new threat report fingerprint on-chain.
     * @param  reportHash  Keccak-256 fingerprint of the canonical report.
     * @return reportId    Deterministic identifier derived from the hash.
     *
     * Requirements:
     *   - Caller must be the owner or an authorized registrar.
     *   - reportHash must not be zero.
     *   - The same hash cannot be registered twice (duplicate protection).
     */
    function registerReport(bytes32 reportHash) external onlyAuthorized returns (bytes32) {
        require(reportHash != bytes32(0), "Invalid report hash");

        bytes32 reportId = generateReportId(reportHash);

        require(!hashExists[reportHash], "Report already registered");
        require(reports[reportId].registeredAt == 0, "Report ID already exists");

        // Persist on-chain
        reports[reportId] = Report({
            reportId:     reportId,
            reportHash:   reportHash,
            registeredBy: msg.sender,
            registeredAt: block.timestamp
        });

        hashExists[reportHash] = true;
        reportCount += 1;

        emit ReportRegistered(
            reportId,
            reportHash,
            msg.sender,
            block.timestamp
        );

        return reportId;
    }

    // ──────────────────────────────────────────────
    //  Read: verify
    // ──────────────────────────────────────────────

    /**
     * @notice Verify that a report ID + hash pair is registered and consistent.
     * @return True only when:
     *         1. A record exists for `reportId`.
     *         2. Its stored hash equals `reportHash`.
     *         3. `generateReportId(reportHash)` reproduces `reportId`.
     */
    function verifyReport(bytes32 reportId, bytes32 reportHash) external view returns (bool) {
        Report memory r = reports[reportId];

        if (r.registeredAt == 0) return false;
        if (r.reportHash != reportHash) return false;
        if (generateReportId(reportHash) != reportId) return false;

        return true;
    }

    // ──────────────────────────────────────────────
    //  Read: metadata
    // ──────────────────────────────────────────────

    /**
     * @notice Retrieve the public metadata of a registered report.
     * @return reportId, reportHash, registeredBy, registeredAt
     */
    function getReport(bytes32 reportId) external view returns (
        bytes32,
        bytes32,
        address,
        uint256
    ) {
        Report memory r = reports[reportId];
        require(r.registeredAt != 0, "Report not found");

        return (
            r.reportId,
            r.reportHash,
            r.registeredBy,
            r.registeredAt
        );
    }
}
