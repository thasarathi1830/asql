// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/**
 * @title PhantomAuditRegistry
 * @notice Immutable on-chain registry for PHANTOM audit record hashes.
 *         Once a hash is registered it can never be modified or deleted,
 *         providing tamper-proof evidence for forensic investigations.
 */
contract PhantomAuditRegistry {
    // ──────────────────────────────────────────────
    //  Types
    // ──────────────────────────────────────────────

    /// @notice The three audit-record categories.
    uint8 public constant TYPE_TRANSACTION    = 1;
    uint8 public constant TYPE_IDENTITY       = 2;
    uint8 public constant TYPE_INVESTIGATION  = 3;

    /// @notice A single immutable audit record.
    struct AuditRecord {
        bytes32 recordHash;
        uint8   recordType;     // 1 = TRANSACTION, 2 = IDENTITY, 3 = INVESTIGATION
        string  recordId;
        uint256 timestamp;
        address submitter;
        bool    exists;
    }

    // ──────────────────────────────────────────────
    //  Storage
    // ──────────────────────────────────────────────

    mapping(bytes32 => AuditRecord) private _records;
    bytes32[] private _recordHashes;

    // ──────────────────────────────────────────────
    //  Errors
    // ──────────────────────────────────────────────

    /// @notice Thrown when a caller tries to register a hash that already exists.
    error RecordAlreadyExists(bytes32 recordHash);

    /// @notice Thrown when the supplied hash is the zero hash.
    error InvalidRecordHash();

    // ──────────────────────────────────────────────
    //  Events
    // ──────────────────────────────────────────────

    /// @notice Emitted every time a new record hash is registered.
    event RecordRegistered(
        bytes32 indexed recordHash,
        uint8   recordType,
        string  recordId,
        address indexed submitter,
        uint256 timestamp
    );

    // ──────────────────────────────────────────────
    //  Write functions
    // ──────────────────────────────────────────────

    /**
     * @notice Register an audit-record hash on-chain.
     * @param hash       The SHA-256 (or keccak) hash of the canonical record.
     * @param recordType 1 = TRANSACTION, 2 = IDENTITY, 3 = INVESTIGATION.
     * @param recordId   A human-readable record identifier (e.g. "TXN-001").
     */
    function registerRecordHash(
        bytes32 hash,
        uint8   recordType,
        string calldata recordId
    ) public {
        if (hash == bytes32(0)) {
            revert InvalidRecordHash();
        }
        if (_records[hash].exists) {
            revert RecordAlreadyExists(hash);
        }

        AuditRecord storage record = _records[hash];
        record.recordHash  = hash;
        record.recordType  = recordType;
        record.recordId    = recordId;
        record.timestamp   = block.timestamp;
        record.submitter   = msg.sender;
        record.exists      = true;

        _recordHashes.push(hash);

        emit RecordRegistered(
            hash,
            recordType,
            recordId,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @notice Convenience: register a TRANSACTION hash.
     */
    function registerTransactionHash(
        bytes32 hash,
        string calldata recordId
    ) external {
        registerRecordHash(hash, TYPE_TRANSACTION, recordId);
    }

    /**
     * @notice Convenience: register an IDENTITY hash.
     */
    function registerIdentityHash(
        bytes32 hash,
        string calldata recordId
    ) external {
        registerRecordHash(hash, TYPE_IDENTITY, recordId);
    }

    /**
     * @notice Convenience: register an INVESTIGATION hash.
     */
    function registerInvestigationHash(
        bytes32 hash,
        string calldata recordId
    ) external {
        registerRecordHash(hash, TYPE_INVESTIGATION, recordId);
    }

    // ──────────────────────────────────────────────
    //  Read / verify functions
    // ──────────────────────────────────────────────

    /**
     * @notice Check whether a hash has been registered and return its metadata.
     */
    function verifyRecord(bytes32 hash)
        external
        view
        returns (
            bool    exists,
            uint8   recordType,
            string memory recordId,
            uint256 timestamp,
            address submitter
        )
    {
        AuditRecord storage r = _records[hash];
        return (r.exists, r.recordType, r.recordId, r.timestamp, r.submitter);
    }

    /**
     * @notice Return the full AuditRecord struct for a given hash.
     */
    function getRecord(bytes32 hash)
        external
        view
        returns (AuditRecord memory)
    {
        return _records[hash];
    }

    /**
     * @notice Total number of registered record hashes.
     */
    function getTotalRecords() external view returns (uint256) {
        return _recordHashes.length;
    }

    /**
     * @notice Paginated retrieval of registered hashes.
     * @param offset Start index in the _recordHashes array.
     * @param limit  Maximum number of hashes to return.
     */
    function getRecordHashes(uint256 offset, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        uint256 total = _recordHashes.length;
        if (offset >= total) {
            return new bytes32[](0);
        }

        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }

        uint256 count = end - offset;
        bytes32[] memory result = new bytes32[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = _recordHashes[offset + i];
        }
        return result;
    }
}
