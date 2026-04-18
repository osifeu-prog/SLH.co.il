"""
SLH Token Transfer Module
Handles BNB/SLH transfers on BSC network.
Private keys are used ONCE and immediately discarded.
"""
import logging
import asyncio
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

log = logging.getLogger("slh.transfer")

BSC_RPC = "https://bsc-dataseed.binance.org/"
BSC_TESTNET_RPC = "https://data-seed-prebsc-1-s1.binance.org:8545/"
SLH_CONTRACT = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
CHAIN_ID = 56  # BSC Mainnet
TESTNET_CHAIN_ID = 97


async def _rpc_call(method, params, testnet=False):
    """Make a JSON-RPC call to BSC."""
    if not HAS_AIOHTTP:
        return None
    rpc = BSC_TESTNET_RPC if testnet else BSC_RPC
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    async with aiohttp.ClientSession() as session:
        async with session.post(rpc, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            return data.get("result")


async def get_nonce(address, testnet=False):
    """Get transaction count (nonce) for address."""
    result = await _rpc_call("eth_getTransactionCount", [address, "latest"], testnet)
    return int(result, 16) if result else None


async def get_gas_price(testnet=False):
    """Get current gas price."""
    result = await _rpc_call("eth_gasPrice", [], testnet)
    return int(result, 16) if result else 5000000000  # Default 5 gwei


async def get_bnb_balance(address, testnet=False):
    """Get BNB balance."""
    result = await _rpc_call("eth_getBalance", [address, "latest"], testnet)
    return int(result, 16) / 1e18 if result else 0


async def get_slh_balance(address, testnet=False):
    """Get SLH token balance."""
    func_sig = "0x70a08231"
    padded = address.lower().replace("0x", "").zfill(64)
    data = func_sig + padded
    result = await _rpc_call("eth_call", [{"to": SLH_CONTRACT, "data": data}, "latest"], testnet)
    return int(result, 16) / 1e18 if result and result != "0x" else 0


async def estimate_gas_slh_transfer(from_addr, to_addr, amount_wei, testnet=False):
    """Estimate gas for SLH transfer."""
    # ERC20 transfer(address,uint256)
    func_sig = "0xa9059cbb"
    padded_to = to_addr.lower().replace("0x", "").zfill(64)
    padded_amount = hex(amount_wei)[2:].zfill(64)
    data = func_sig + padded_to + padded_amount

    result = await _rpc_call("eth_estimateGas", [{
        "from": from_addr,
        "to": SLH_CONTRACT,
        "data": data,
    }], testnet)
    return int(result, 16) if result else 60000  # Default estimate


async def transfer_slh(private_key, from_addr, to_addr, amount, testnet=False):
    """
    Transfer SLH tokens.
    Returns: (success, tx_hash_or_error, gas_used_bnb)

    IMPORTANT: private_key should be discarded after this call!
    """
    try:
        # We need web3 for signing - try import
        try:
            from web3 import Web3
        except ImportError:
            return False, "web3 not installed", 0

        rpc = BSC_TESTNET_RPC if testnet else BSC_RPC
        chain_id = TESTNET_CHAIN_ID if testnet else CHAIN_ID

        w3 = Web3(Web3.HTTPProvider(rpc))

        # Convert amount to wei (18 decimals)
        amount_wei = int(amount * 1e18)

        # Build ERC20 transfer data
        func_sig = "0xa9059cbb"
        padded_to = to_addr.lower().replace("0x", "").zfill(64)
        padded_amount = hex(amount_wei)[2:].zfill(64)
        data = func_sig + padded_to + padded_amount

        nonce = w3.eth.get_transaction_count(from_addr)
        gas_price = w3.eth.gas_price
        gas_limit = 60000  # Standard ERC20 transfer

        tx = {
            "nonce": nonce,
            "to": Web3.to_checksum_address(SLH_CONTRACT),
            "value": 0,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "data": data,
            "chainId": chain_id,
        }

        # Sign and send
        signed = w3.eth.account.sign_transaction(tx, private_key)
        raw = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction', None)
        tx_hash = w3.eth.send_raw_transaction(raw)
        tx_hex = tx_hash.hex()

        gas_cost_bnb = (gas_limit * gas_price) / 1e18

        log.info("SLH transfer sent: %s -> %s | %s SLH | tx: %s",
                 from_addr[:10], to_addr[:10], amount, tx_hex)

        return True, tx_hex, gas_cost_bnb

    except Exception as e:
        log.error("Transfer failed: %s", e)
        return False, str(e), 0


def format_gas_info(gas_price_wei, gas_limit=60000):
    """Format gas cost for display."""
    gas_gwei = gas_price_wei / 1e9
    gas_bnb = (gas_price_wei * gas_limit) / 1e18
    gas_usd = gas_bnb * 600  # Approximate BNB price
    return {
        "gwei": f"{gas_gwei:.1f}",
        "bnb": f"{gas_bnb:.6f}",
        "usd": f"~${gas_usd:.4f}",
        "ils": f"~{gas_usd * 3.7:.2f} ILS",
    }
