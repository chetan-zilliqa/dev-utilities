---

# 🚀 ZQ2 API Benchmarking Utilities

This folder contains the dedicated benchmarking scripts for comparing ZQ2 RPC behavior across networks.

---

## Prerequisites

Install the following on your system before running the benchmarking scripts:

* Python 3
* `pip` for installing Python packages
* Python package: `requests`

Example install commands on Ubuntu or Debian:

```bash
sudo apt update
sudo apt install -y python3 python3-pip
python3 -m pip install --user requests
```

Most users only need the above to run the benchmark commands.

Only if you want to deploy a new EVM benchmark contract, also install:

* Node.js and `npm`
* Node.js package: `ethers`

```bash
sudo apt install -y nodejs npm
npm install ethers
```

Only if you use the EVM deploy flow, you also need:

* `PRIVATE_KEY` exported in your shell
* an EVM wallet with enough balance to pay for deployment

If you use the Scilla state flow with your own contract, you also need:

* a deployed Scilla contract on the target network
* a Zilliqa native wallet with balance if you need to deploy that contract yourself

---

## 📂 Files

### 1. ⚡ Benchmark API

**File:** `benchmark_api.py`
Benchmarks RPC endpoints with separate commands for legacy Scilla state calls and EVM `eth_call`.

* ✅ Separate command lines for Scilla and EVM RPC tests
* ✅ Measures min/avg/max latency
* ✅ Throughput & success rate
* ✅ Concurrent workers

## Benchmark API Usage

Most users will only use `benchmark_api.py`.

There is no need to deploy a new EVM contract if a benchmark contract is already deployed and you already have the contract address.

Benchmark the current Scilla RPC:

```bash
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py zilliqa-state --total-calls 100 --workers 20
```

Benchmark `eth_call` against an already deployed contract:

```bash
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py evm-call --contract-address 0xb1Dd28BBC3d92BDB51F61bf989aaF147aEA3Bf62 --total-calls 100 --workers 20
```

For the Scilla state flow, you need a deployed Scilla contract and then query that contract's state with `zilliqa-state`.
If the Scilla contract is missing, please let me know.

---

### 2. 🧱 EVM Deploy Helper

**File:** `deploy_evm_contract.js`
Deploys the tiny EVM contract used by the benchmark command.

It reads:

```env
RPC_URL=https://api.zq2-devnet.zilliqa.com
PRIVATE_KEY=<your-private-key>
```

Direct usage:

```bash
node deploy_evm_contract.js https://api.zq2-devnet.zilliqa.com
```

## Optional: Deploy a New EVM Benchmark Contract

Only use this if you specifically want to deploy a fresh benchmark contract.

```bash
export PRIVATE_KEY=<your-private-key>
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py deploy-evm
```

Before deploying, make sure you have:

* an EVM wallet with balance for the EVM deployment
* a Zilliqa native wallet with balance if you also want to deploy a Scilla contract for state benchmarking

---

## ⚠️ Disclaimer

These scripts are for **testing & benchmarking** only.
Prefer environment variables over command-line secrets.
Do **not** use real private keys or mainnet funds unless you understand the risks.

---
