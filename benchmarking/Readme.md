---

# 🚀 ZQ2 Benchmarking Utilities

This folder contains the dedicated benchmarking scripts for comparing ZQ2 RPC behavior across networks.

---

## 📂 Files

### 1. ⚡ Benchmark API

**File:** `benchmark_api.py`
Benchmarks RPC endpoints with separate commands for legacy Scilla state calls and EVM `eth_call`.

* ✅ Separate command lines for Scilla and EVM RPC tests
* ✅ Measures min/avg/max latency
* ✅ Throughput & success rate
* ✅ Concurrent workers
* ✅ Deploys a tiny EVM contract for `eth_call` benchmarking

Benchmark the current Scilla RPC:

```bash
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py zilliqa-state
```

Deploy the EVM benchmark contract:

```bash
export PRIVATE_KEY=<your-private-key>
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py deploy-evm
```

Benchmark `eth_call` against that deployed contract:

```bash
export RPC_URL=https://api.zq2-devnet.zilliqa.com
python3 benchmark_api.py evm-call --contract-address <deployed-contract-address>
```

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

---

## ⚠️ Disclaimer

These scripts are for **testing & benchmarking** only.
Prefer environment variables over command-line secrets.
Do **not** use real private keys or mainnet funds unless you understand the risks.

---
