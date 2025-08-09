#!/usr/bin/env python3
"""
Balance Checker for Recovered Wallet Keys
Checks ETH and SOL balances for your recovered addresses
"""

import requests
import time
import json

# Your recovered addresses
addresses = {
    "ethereum": [
        "0xff0B84464603AD6A0b46495bfd0E13b654194023",
        "0x88227b39ba522b5AeBf75f355118a57C3a4a243a"
    ],
    "solana": [
        "Acte5ZRRne7hJuwLvo2ESoDn9qCP8hwN1bnhjNoM43es",
        "FqpRvHZYppycZ2BNtYanDhPku3YC6HWiaNk3AjJTGEQ2"
    ],
    "bitcoin": [
        "1Je9nE7cCya1e5Ny9qFREDXmMCw97UbZgh",
        "1Stanr1KfXpP54LY3MGZWQCgEuidneZXf"
    ]
}

def check_eth_balance(address):
    """Check Ethereum balance using public API"""
    try:
        # Using free Etherscan API (no key needed for basic queries)
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == '1':
            wei = int(data['result'])
            eth = wei / 1e18
            return eth
        else:
            print(f"Etherscan error for {address}: {data.get('message', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error checking ETH balance for {address}: {e}")
        return None

def check_solana_balance(address):
    """Check Solana balance using public RPC"""
    try:
        # Using Solana mainnet public RPC
        url = "https://api.mainnet-beta.solana.com"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if 'result' in data:
            lamports = data['result']['value']
            sol = lamports / 1e9  # Convert lamports to SOL
            return sol
        else:
            print(f"Solana RPC error for {address}: {data.get('error', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error checking SOL balance for {address}: {e}")
        return None

def check_btc_balance(address):
    """Check Bitcoin balance using blockchain.info"""
    try:
        url = f"https://blockchain.info/q/addressbalance/{address}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            satoshi = int(response.text)
            btc = satoshi / 1e8
            return btc
        else:
            print(f"Bitcoin API error for {address}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error checking BTC balance for {address}: {e}")
        return None

def main():
    print("🔍 CHECKING BALANCES FOR YOUR RECOVERED WALLETS")
    print("=" * 60)
    
    total_values = {"ethereum": 0, "solana": 0, "bitcoin": 0}
    
    # Check Ethereum balances
    print("\n💎 ETHEREUM BALANCES:")
    print("-" * 30)
    for i, addr in enumerate(addresses["ethereum"], 1):
        print(f"Address #{i}: {addr}")
        balance = check_eth_balance(addr)
        if balance is not None:
            print(f"  💰 Balance: {balance:.6f} ETH")
            total_values["ethereum"] += balance
            if balance > 0:
                print(f"  🌐 Etherscan: https://etherscan.io/address/{addr}")
        else:
            print("  ❌ Could not retrieve balance")
        print()
        time.sleep(1)  # Rate limiting
    
    # Check Solana balances
    print("\n🟣 SOLANA BALANCES:")
    print("-" * 30)
    for i, addr in enumerate(addresses["solana"], 1):
        print(f"Address #{i}: {addr}")
        balance = check_solana_balance(addr)
        if balance is not None:
            print(f"  💰 Balance: {balance:.6f} SOL")
            total_values["solana"] += balance
            if balance > 0:
                print(f"  🌐 Explorer: https://explorer.solana.com/address/{addr}")
        else:
            print("  ❌ Could not retrieve balance")
        print()
        time.sleep(1)  # Rate limiting
    
    # Check Bitcoin balances (we already know these are 0, but let's confirm)
    print("\n₿ BITCOIN BALANCES:")
    print("-" * 30)
    for i, addr in enumerate(addresses["bitcoin"], 1):
        print(f"Address #{i}: {addr}")
        balance = check_btc_balance(addr)
        if balance is not None:
            print(f"  💰 Balance: {balance:.8f} BTC")
            total_values["bitcoin"] += balance
            if balance > 0:
                print(f"  🌐 Explorer: https://blockchair.com/bitcoin/address/{addr}")
        else:
            print("  ❌ Could not retrieve balance")
        print()
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("=" * 60)
    print("📊 TOTAL BALANCES SUMMARY:")
    print("=" * 60)
    print(f"💎 Total Ethereum: {total_values['ethereum']:.6f} ETH")
    print(f"🟣 Total Solana:   {total_values['solana']:.6f} SOL")
    print(f"₿  Total Bitcoin:   {total_values['bitcoin']:.8f} BTC")
    print()
    
    # Save results
    balance_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "addresses": addresses,
        "balances": {
            "ethereum_total": total_values["ethereum"],
            "solana_total": total_values["solana"],
            "bitcoin_total": total_values["bitcoin"]
        }
    }
    
    with open('balance_check_results.json', 'w') as f:
        json.dump(balance_summary, f, indent=2)
    print("💾 Balance results saved to balance_check_results.json")
    
    if any(total_values.values()):
        print("\n🎉 FUNDS FOUND! Check the addresses with non-zero balances!")
    else:
        print("\n💡 No funds found on these addresses, but the keys are valid for importing!")

if __name__ == "__main__":
    main()
