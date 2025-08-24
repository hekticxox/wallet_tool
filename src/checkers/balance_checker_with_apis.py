#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def check_balance_etherscan(address):
    """Check balance using Etherscan API"""
    api_key = os.getenv('ETHERSCAN_API_KEY')
    if not api_key:
        return None, "No Etherscan API key"
    
    url = f"https://api.etherscan.io/api"
    params = {
        'module': 'account',
        'action': 'balance',
        'address': address,
        'tag': 'latest',
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data['status'] == '1':
            balance_wei = int(data['result'])
            balance_eth = balance_wei / 1e18
            return balance_eth, "Success"
        else:
            return None, f"Error: {data.get('message', 'Unknown error')}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def check_balance_infura(address):
    """Check balance using Infura API"""
    api_key = os.getenv('INFURA_API_KEY')
    if not api_key:
        return None, "No Infura API key"
    
    url = f"https://mainnet.infura.io/v3/{api_key}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        
        if 'result' in data:
            balance_wei = int(data['result'], 16)
            balance_eth = balance_wei / 1e18
            return balance_eth, "Success"
        else:
            return None, f"Error: {data.get('error', 'Unknown error')}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def check_balance_alchemy(address):
    """Check balance using Alchemy API"""
    api_key = os.getenv('ALCHEMY_API_KEY')
    if not api_key:
        return None, "No Alchemy API key"
    
    url = f"https://eth-mainnet.alchemyapi.io/v2/{api_key}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [address, "latest"],
        "id": 1
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        
        if 'result' in data:
            balance_wei = int(data['result'], 16)
            balance_eth = balance_wei / 1e18
            return balance_eth, "Success"
        else:
            return None, f"Error: {data.get('error', 'Unknown error')}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def main():
    # Our funded addresses
    funded_addresses = [
        "0x6e59e2a98d12f45ab5872942fe45a1036b1ea9c9",
        "0x8bd210f4a679eced866b725a85ba75a2c158f651"
    ]
    
    print("🔍 CHECKING BALANCES OF FUNDED ADDRESSES")
    print("="*60)
    
    for i, address in enumerate(funded_addresses, 1):
        print(f"\n📍 Address {i}: {address}")
        print("-" * 50)
        
        # Try Etherscan first
        balance, status = check_balance_etherscan(address)
        if balance is not None:
            print(f"✅ Etherscan: {balance:.6f} ETH")
            if balance > 0:
                usd_estimate = balance * 2500  # Rough ETH price estimate
                print(f"💰 Estimated USD: ${usd_estimate:.2f}")
        else:
            print(f"❌ Etherscan failed: {status}")
        
        time.sleep(0.5)  # Rate limit protection
        
        # Try Infura as backup
        balance, status = check_balance_infura(address)
        if balance is not None:
            print(f"✅ Infura: {balance:.6f} ETH")
        else:
            print(f"❌ Infura failed: {status}")
        
        time.sleep(0.5)  # Rate limit protection
        
        # Try Alchemy as backup
        balance, status = check_balance_alchemy(address)
        if balance is not None:
            print(f"✅ Alchemy: {balance:.6f} ETH")
        else:
            print(f"❌ Alchemy failed: {status}")
        
        time.sleep(1)  # Rate limit protection between addresses
    
    print("\n" + "="*60)
    print("✨ Balance check complete!")
    
    # Also check the third address we found
    third_address = "0x7ddCEF59b494096e74ae496858387aC793b80B61"
    print(f"\n📍 Bonus Address: {third_address}")
    print("-" * 50)
    
    balance, status = check_balance_etherscan(third_address)
    if balance is not None:
        print(f"✅ Etherscan: {balance:.6f} ETH")
        if balance > 0:
            usd_estimate = balance * 2500
            print(f"💰 Estimated USD: ${usd_estimate:.2f}")
    else:
        print(f"❌ Etherscan failed: {status}")

if __name__ == "__main__":
    main()
