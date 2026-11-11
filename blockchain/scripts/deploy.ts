import { ethers } from "hardhat";

async function main() {
  console.log("Deploying PhantomAuditRegistry...");

  const PhantomAuditRegistry = await ethers.getContractFactory("PhantomAuditRegistry");
  const registry = await PhantomAuditRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log(`PhantomAuditRegistry deployed to: ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
