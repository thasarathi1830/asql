"""PHANTOM — E2E Blockchain Anchor & Tamper Detection Runner.

Invokes the Hardhat E2E script to anchor 100 real PaySim transactions and verify tamper detection.
"""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def run_anchor_and_verify() -> int:
    blockchain_dir = ROOT_DIR / "blockchain"
    cmd = ["cmd", "/c", "npx hardhat run scripts/anchor_e2e.ts"]
    print(f"[AnchorRunner] Executing: {' '.join(cmd)} in {blockchain_dir}")
    res = subprocess.run(cmd, cwd=str(blockchain_dir))
    return res.returncode

if __name__ == "__main__":
    sys.exit(run_anchor_and_verify())

