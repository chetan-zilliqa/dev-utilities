#!/usr/bin/env node

const ethersPkg = require("ethers");
const ethers = ethersPkg.ethers || ethersPkg;

const rpcUrl = process.argv[2] || process.env.RPC_URL;
const privateKey = process.env.PRIVATE_KEY;

if (!rpcUrl) {
  console.error("Missing RPC URL. Pass it as the first argument or set RPC_URL.");
  process.exit(1);
}

if (!privateKey) {
  console.error("Missing PRIVATE_KEY in the environment.");
  process.exit(1);
}

function createProvider(url) {
  if (ethers.JsonRpcProvider) {
    return new ethers.JsonRpcProvider(url);
  }
  if (ethers.providers && ethers.providers.JsonRpcProvider) {
    return new ethers.providers.JsonRpcProvider(url);
  }
  throw new Error("Unsupported ethers version: JsonRpcProvider not found.");
}

function toBigIntValue(value) {
  if (value == null) {
    return null;
  }
  if (typeof value === "bigint") {
    return value;
  }
  if (typeof value === "number") {
    return BigInt(value);
  }
  if (typeof value.toBigInt === "function") {
    return value.toBigInt();
  }
  if (typeof value.toString === "function") {
    return BigInt(value.toString());
  }
  throw new Error("Unsupported numeric value returned by ethers.");
}

async function getRecommendedGasPrice(provider) {
  const rpcGasPriceHex = await provider.send("eth_gasPrice", []);
  const rpcGasPrice = BigInt(rpcGasPriceHex);
  const feeData = await provider.getFeeData();

  const candidates = [rpcGasPrice];

  if (feeData.gasPrice) {
    candidates.push(toBigIntValue(feeData.gasPrice));
  }
  if (feeData.maxFeePerGas) {
    candidates.push(toBigIntValue(feeData.maxFeePerGas));
  }
  if (feeData.maxPriorityFeePerGas) {
    candidates.push(toBigIntValue(feeData.maxPriorityFeePerGas));
  }

  let selected = candidates[0];
  for (const candidate of candidates.slice(1)) {
    if (candidate > selected) {
      selected = candidate;
    }
  }

  return selected * 2n;
}

async function main() {
  const provider = createProvider(rpcUrl);
  const wallet = new ethers.Wallet(privateKey, provider);
  const network = await provider.getNetwork();
  const gasPrice = await getRecommendedGasPrice(provider);

  // Init code that deploys a runtime returning the uint256 value 42 for any eth_call.
  const initCode = "0x600a600c600039600a6000f3602a60005260206000f3";

  const tx = {
    data: initCode,
    gasLimit: 100000n,
    gasPrice,
  };

  const response = await wallet.sendTransaction(tx);
  const receipt = await response.wait();

  if (!receipt || !receipt.contractAddress) {
    throw new Error("Deployment completed without a contract address.");
  }

  console.log(
    JSON.stringify(
      {
        chainId: network.chainId.toString(),
        contractAddress: receipt.contractAddress,
        txHash: response.hash,
        blockNumber: receipt.blockNumber,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.message || String(error));
  process.exit(1);
});
