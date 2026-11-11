import { expect } from "chai";
import { ethers } from "hardhat";
import { PhantomAuditRegistry } from "../typechain-types";

describe("PhantomAuditRegistry", function () {
  let registry: PhantomAuditRegistry;
  let deployer: any;
  let other: any;

  const ZERO_HASH = ethers.ZeroHash;
  const SAMPLE_HASH_1 = ethers.keccak256(ethers.toUtf8Bytes("transaction-record-001"));
  const SAMPLE_HASH_2 = ethers.keccak256(ethers.toUtf8Bytes("identity-record-001"));
  const SAMPLE_HASH_3 = ethers.keccak256(ethers.toUtf8Bytes("investigation-record-001"));
  const SAMPLE_HASH_4 = ethers.keccak256(ethers.toUtf8Bytes("extra-record-001"));
  const SAMPLE_HASH_5 = ethers.keccak256(ethers.toUtf8Bytes("extra-record-002"));

  const TYPE_TRANSACTION = 1;
  const TYPE_IDENTITY = 2;
  const TYPE_INVESTIGATION = 3;

  beforeEach(async function () {
    [deployer, other] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("PhantomAuditRegistry");
    registry = (await Factory.deploy()) as PhantomAuditRegistry;
    await registry.waitForDeployment();
  });

  // ── Test 1: Register a transaction hash successfully ──
  it("should register a transaction hash and emit RecordRegistered", async function () {
    const tx = await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");
    const receipt = await tx.wait();

    // Check event
    await expect(tx)
      .to.emit(registry, "RecordRegistered")
      .withArgs(
        SAMPLE_HASH_1,
        TYPE_TRANSACTION,
        "TXN-001",
        deployer.address,
        (v: any) => v > 0 // timestamp is non-zero
      );

    // Total records should be 1
    expect(await registry.getTotalRecords()).to.equal(1);
  });

  // ── Test 2: Verify registered hash returns correct data ──
  it("should return correct data when verifying a registered hash", async function () {
    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");

    const [exists, recordType, recordId, timestamp, submitter] =
      await registry.verifyRecord(SAMPLE_HASH_1);

    expect(exists).to.be.true;
    expect(recordType).to.equal(TYPE_TRANSACTION);
    expect(recordId).to.equal("TXN-001");
    expect(timestamp).to.be.greaterThan(0);
    expect(submitter).to.equal(deployer.address);
  });

  // ── Test 3: Reject duplicate registration ──
  it("should reject duplicate hash registration", async function () {
    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");

    await expect(
      registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001-dup")
    ).to.be.revertedWithCustomError(registry, "RecordAlreadyExists")
      .withArgs(SAMPLE_HASH_1);
  });

  // ── Test 4: Reject zero hash ──
  it("should reject the zero hash", async function () {
    await expect(
      registry.registerRecordHash(ZERO_HASH, TYPE_TRANSACTION, "INVALID")
    ).to.be.revertedWithCustomError(registry, "InvalidRecordHash");
  });

  // ── Test 5: Register identity hash via shortcut ──
  it("should register an identity hash via registerIdentityHash", async function () {
    await registry.registerIdentityHash(SAMPLE_HASH_2, "ID-001");

    const [exists, recordType, recordId] = await registry.verifyRecord(SAMPLE_HASH_2);
    expect(exists).to.be.true;
    expect(recordType).to.equal(TYPE_IDENTITY);
    expect(recordId).to.equal("ID-001");
  });

  // ── Test 6: Register investigation hash via shortcut ──
  it("should register an investigation hash via registerInvestigationHash", async function () {
    await registry.registerInvestigationHash(SAMPLE_HASH_3, "INV-001");

    const [exists, recordType, recordId] = await registry.verifyRecord(SAMPLE_HASH_3);
    expect(exists).to.be.true;
    expect(recordType).to.equal(TYPE_INVESTIGATION);
    expect(recordId).to.equal("INV-001");
  });

  // ── Test 7: getTotalRecords returns correct count ──
  it("should return correct total record count after multiple registrations", async function () {
    expect(await registry.getTotalRecords()).to.equal(0);

    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");
    expect(await registry.getTotalRecords()).to.equal(1);

    await registry.registerIdentityHash(SAMPLE_HASH_2, "ID-001");
    expect(await registry.getTotalRecords()).to.equal(2);

    await registry.registerInvestigationHash(SAMPLE_HASH_3, "INV-001");
    expect(await registry.getTotalRecords()).to.equal(3);
  });

  // ── Test 8: getRecordHashes pagination ──
  it("should paginate record hashes correctly", async function () {
    // Register 5 records
    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");
    await registry.registerRecordHash(SAMPLE_HASH_2, TYPE_IDENTITY, "ID-001");
    await registry.registerRecordHash(SAMPLE_HASH_3, TYPE_INVESTIGATION, "INV-001");
    await registry.registerRecordHash(SAMPLE_HASH_4, TYPE_TRANSACTION, "TXN-002");
    await registry.registerRecordHash(SAMPLE_HASH_5, TYPE_TRANSACTION, "TXN-003");

    // Page 1: offset=0, limit=2
    const page1 = await registry.getRecordHashes(0, 2);
    expect(page1.length).to.equal(2);
    expect(page1[0]).to.equal(SAMPLE_HASH_1);
    expect(page1[1]).to.equal(SAMPLE_HASH_2);

    // Page 2: offset=2, limit=2
    const page2 = await registry.getRecordHashes(2, 2);
    expect(page2.length).to.equal(2);
    expect(page2[0]).to.equal(SAMPLE_HASH_3);
    expect(page2[1]).to.equal(SAMPLE_HASH_4);

    // Page 3: offset=4, limit=2 → only 1 left
    const page3 = await registry.getRecordHashes(4, 2);
    expect(page3.length).to.equal(1);
    expect(page3[0]).to.equal(SAMPLE_HASH_5);

    // Beyond range
    const empty = await registry.getRecordHashes(10, 5);
    expect(empty.length).to.equal(0);
  });

  // ── Test 9: Tamper detection ──
  it("should detect tampered records (different hash returns not found)", async function () {
    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");

    // The registered hash is found
    const [existsOriginal] = await registry.verifyRecord(SAMPLE_HASH_1);
    expect(existsOriginal).to.be.true;

    // A different hash (simulating tampered data) is NOT found
    const tamperedHash = ethers.keccak256(ethers.toUtf8Bytes("tampered-data"));
    const [existsTampered] = await registry.verifyRecord(tamperedHash);
    expect(existsTampered).to.be.false;
  });

  // ── Test 10: getRecord returns full struct ──
  it("should return full AuditRecord struct via getRecord", async function () {
    await registry.registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-001");

    const record = await registry.getRecord(SAMPLE_HASH_1);
    expect(record.recordHash).to.equal(SAMPLE_HASH_1);
    expect(record.recordType).to.equal(TYPE_TRANSACTION);
    expect(record.recordId).to.equal("TXN-001");
    expect(record.timestamp).to.be.greaterThan(0);
    expect(record.submitter).to.equal(deployer.address);
    expect(record.exists).to.be.true;
  });

  // ── Test 11: Unregistered hash returns empty record ──
  it("should return empty record for unregistered hash", async function () {
    const record = await registry.getRecord(SAMPLE_HASH_1);
    expect(record.exists).to.be.false;
    expect(record.recordType).to.equal(0);
    expect(record.submitter).to.equal(ethers.ZeroAddress);
  });

  // ── Test 12: Different submitter recorded correctly ──
  it("should record the correct submitter for different callers", async function () {
    await registry.connect(other).registerRecordHash(SAMPLE_HASH_1, TYPE_TRANSACTION, "TXN-OTHER");

    const [exists, , , , submitter] = await registry.verifyRecord(SAMPLE_HASH_1);
    expect(exists).to.be.true;
    expect(submitter).to.equal(other.address);
  });
});
