#!/usr/bin/env python3
"""Test all our new APIs quickly"""

import requests
import time

def test_bitcoin_api(address):
    """Test Bitcoin APIs"""
    apis = [
        ("Mempool", "https://mempool.space/api/address/" + address),
        ("Blockchain.info", f"https://blockchain.info/rawaddr/{address}?limit=0"),
        ("BlockCypher", f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"),
    ]
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'WalletRecovery/2.0'})
    
    print(f"🔍 Testing Bitcoin APIs with address: {address[:15]}...{address[-10:]}")
    
    for name, url in apis:
        try:
            print(f"  🌐 {name}: ", end="", flush=True)
            response = session.get(url, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                if 'chain_stats' in data:
                    balance = data['chain_stats'].get('funded_txo_sum', 0)
                elif 'final_balance' in data:
                    balance = data.get('final_balance', 0)
                elif 'balance' in data:
                    balance = data.get('balance', 0)
                else:
                    balance = 0
                
                btc_balance = balance / 100000000
                print(f"✅ {btc_balance} BTC")
            else:
                print(f"❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
        
        time.sleep(0.5)

def test_ethereum_api(address):
    """Test Ethereum APIs"""
    apis = [
        ("Etherscan", "https://api.etherscan.io/api", {
            'module': 'account',
            'action': 'balance', 
            'address': address,
            'tag': 'latest',
            'apikey': 'RHI2QM5XKCUI3TDNKSEVI28PGHR4RY9I79'
        }),
        ("Alchemy", "https://eth-mainnet.g.alchemy.com/v2/6Zn_wn5ckNFSoL6Ch3_kQ", {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBalance",
            "params": [address, "latest"]
        }),
    ]
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'WalletRecovery/2.0'})
    
    print(f"🔍 Testing Ethereum APIs with address: {address[:15]}...{address[-10:]}")
    
    for name, url, params in apis:
        try:
            print(f"  🌐 {name}: ", end="", flush=True)
            
            if name == "Etherscan":
                response = session.get(url, params=params, timeout=8)
            else:
                response = session.post(url, json=params, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                
                if name == "Etherscan" and data.get('status') == '1':
                    balance_wei = int(data.get('result', 0))
                    balance_eth = balance_wei / (10**18)
                    print(f"✅ {balance_eth} ETH")
                elif name == "Alchemy" and 'result' in data:
                    balance_wei = int(data['result'], 16)
                    balance_eth = balance_wei / (10**18)
                    print(f"✅ {balance_eth} ETH")
                else:
                    print(f"❌ Parse error: {data}")
            else:
                print(f"❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    print("🚀 Testing wallet scanner APIs...\n")
    
    # Test with known addresses
    bitcoin_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block
    ethereum_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's address
    
    test_bitcoin_api(bitcoin_address)
    print()
    test_ethereum_api(ethereum_address)
    
    print("\n🎉 API test complete!")
