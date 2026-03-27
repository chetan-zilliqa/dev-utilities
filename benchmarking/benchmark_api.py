import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

DEFAULT_URL = "https://api.zq2-devnet.zilliqa.com/"
DEFAULT_SCILLA_CONTRACT = "0xe1c2094d3570cbeb0f4938fd9c25e50a678c12e4"
DEFAULT_TIMEOUT = 10.0
DEPLOY_SCRIPT = os.path.join(os.path.dirname(__file__), "deploy_evm_contract.js")
DEFAULT_RPC_URL = os.environ.get("RPC_URL", DEFAULT_URL)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Benchmark ZQ2 RPCs with separate commands for Scilla state and EVM eth_call."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    state_cmd = subparsers.add_parser(
        "zilliqa-state",
        help="Benchmark the current GetSmartContractState RPC.",
    )
    add_common_benchmark_args(state_cmd)
    state_cmd.add_argument(
        "--url",
        default=DEFAULT_RPC_URL,
        help="RPC URL to benchmark. Defaults to RPC_URL env var, then devnet URL.",
    )
    state_cmd.add_argument(
        "--contract",
        default=DEFAULT_SCILLA_CONTRACT,
        help=f"Scilla contract address for GetSmartContractState. Default: {DEFAULT_SCILLA_CONTRACT}",
    )

    deploy_cmd = subparsers.add_parser(
        "deploy-evm",
        help="Deploy a minimal EVM contract used for RPC benchmarking.",
    )
    deploy_cmd.add_argument(
        "--rpc-url",
        default=os.environ.get("RPC_URL", DEFAULT_URL),
        help="RPC URL to deploy to. Defaults to RPC_URL env var, then devnet URL.",
    )

    evm_cmd = subparsers.add_parser(
        "evm-call",
        help="Benchmark eth_call against a deployed EVM contract.",
    )
    add_common_benchmark_args(evm_cmd)
    evm_cmd.add_argument(
        "--url",
        default=DEFAULT_RPC_URL,
        help="RPC URL to benchmark. Defaults to RPC_URL env var, then devnet URL.",
    )
    evm_cmd.add_argument(
        "--contract-address",
        required=True,
        help="Deployed EVM contract address to query with eth_call.",
    )
    evm_cmd.add_argument(
        "--data",
        default="0x",
        help="Call data to send. The deployed helper contract works with the default 0x.",
    )
    evm_cmd.add_argument(
        "--from-address",
        default=None,
        help="Optional from address for eth_call.",
    )

    return parser


def add_common_benchmark_args(parser):
    parser.add_argument(
        "--total-calls",
        "--runs",
        dest="total_calls",
        type=int,
        default=50,
        help="Total number of requests. Default: 50",
    )
    parser.add_argument("--workers", type=int, default=10, help="Concurrent workers. Default: 10")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Per-request timeout in seconds. Default: {DEFAULT_TIMEOUT}",
    )


def rpc_request(url, payload, timeout):
    start = time.perf_counter()
    try:
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000
        try:
            body = response.json()
        except ValueError:
            body = {"raw_text": response.text}
        rpc_error = body.get("error") if isinstance(body, dict) else None
        return {
            "elapsed_ms": elapsed_ms,
            "status_code": response.status_code,
            "body": body,
            "ok": response.ok and isinstance(body, dict) and "result" in body and rpc_error is None,
            "error": None,
        }
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "elapsed_ms": elapsed_ms,
            "status_code": None,
            "body": None,
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
        }


def benchmark_rpc(url, payload, runs, workers, timeout, label):
    times = []
    statuses = []
    successful_calls = 0

    started_at = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(rpc_request, url, payload, timeout) for _ in range(runs)]
        for i, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            times.append(result["elapsed_ms"])
            statuses.append(result["status_code"] or 0)

            if result["ok"]:
                successful_calls += 1
                status_label = result["status_code"]
            else:
                rpc_error = None
                if isinstance(result["body"], dict):
                    rpc_error = result["body"].get("error", {}).get("message")
                status_label = result["error"] or rpc_error or f"http-{result['status_code']}"

            print(f"Run {i}: {result['elapsed_ms']:.2f} ms | Status {status_label}")

    total_time = time.perf_counter() - started_at
    total_throughput = runs / total_time if total_time else 0.0
    successful_throughput = successful_calls / total_time if total_time else 0.0
    success_rate = (successful_calls / runs * 100) if runs else 0.0

    print("\nSummary:")
    print(f"  Benchmark: {label}")
    print(f"  URL: {url}")
    print(f"  Total calls: {runs}")
    print(f"  Parallel workers: {workers}")
    print(f"  Min: {min(times):.2f} ms")
    print(f"  Max: {max(times):.2f} ms")
    print(f"  Avg: {statistics.mean(times):.2f} ms")
    print(f"  Median: {statistics.median(times):.2f} ms")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Total duration: {total_time:.2f} sec")
    print(f"  Total throughput: {total_throughput:.2f} requests/sec")
    print(f"  Successful throughput: {successful_throughput:.2f} successful requests/sec")

    if successful_calls != runs:
        sys.exit(1)


def deploy_evm_contract(rpc_url):
    private_key = os.environ.get("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("Missing PRIVATE_KEY in the environment.")

    completed = subprocess.run(
        ["node", DEPLOY_SCRIPT, rpc_url],
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown deploy error"
        raise RuntimeError(f"EVM deployment failed: {stderr}")

    output = completed.stdout.strip()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Unexpected deploy output: {output}") from exc


def run_zilliqa_state(args):
    payload = {
        "id": "1",
        "jsonrpc": "2.0",
        "method": "GetSmartContractState",
        "params": [args.contract],
    }
    benchmark_rpc(
        url=args.url,
        payload=payload,
        runs=args.total_calls,
        workers=args.workers,
        timeout=args.timeout,
        label=f"GetSmartContractState({args.contract})",
    )


def run_deploy_evm(args):
    deployment = deploy_evm_contract(args.rpc_url)
    print("Deployment complete:")
    print(f"  Chain ID: {deployment['chainId']}")
    print(f"  Contract: {deployment['contractAddress']}")
    print(f"  Tx Hash: {deployment['txHash']}")
    print(f"  Block: {deployment['blockNumber']}")
    print("\nNext command:")
    print(
        "  "
        f"python3 benchmark_api.py evm-call --url {args.rpc_url} "
        f"--contract-address {deployment['contractAddress']}"
    )


def run_evm_call(args):
    call_object = {
        "to": args.contract_address,
        "data": args.data,
    }
    if args.from_address:
        call_object["from"] = args.from_address

    payload = {
        "id": "1",
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [call_object, "latest"],
    }
    benchmark_rpc(
        url=args.url,
        payload=payload,
        runs=args.total_calls,
        workers=args.workers,
        timeout=args.timeout,
        label=f"eth_call({args.contract_address})",
    )


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "zilliqa-state":
            run_zilliqa_state(args)
        elif args.command == "deploy-evm":
            run_deploy_evm(args)
        elif args.command == "evm-call":
            run_evm_call(args)
        else:
            parser.error(f"Unknown command: {args.command}")
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
