import time
#!/usr/bin/env python3
"""
💎 JACKPOT VALIDATOR & ANALYZER
===============================
Validate and analyze discovered jackpot wallets
"""

import json
import requests
from datetime import datetime
from eth_keys import keys
from bit import Key
from api_manager import APIManager

class JackpotValidator:
    def __init__(self):
        """Initialize jackpot validator"""
        self.api_manager = APIManager()
    
    def validate_jackpot(self, private_key_hex):
        """Validate and analyze a jackpot wallet"""
        print("💎 JACKPOT VALIDATOR & ANALYZER")
        print("=" * 60)
        print(f"🔑 Private Key: {private_key_hex}")
        
        # Derive addresses
        eth_address, btc_address = self.derive_addresses(private_key_hex)
        
        print(f"📍 ETH Address: {eth_address}")
        print(f"📍 BTC Address: {btc_address}")
        
        # Validate balances with multiple APIs
        print("\n🔍 VALIDATING BALANCES...")
        
        # Ethereum balance validation
        eth_balances = self.validate_eth_balance(eth_address)
        btc_balances = self.validate_btc_balance(btc_address)
        
        # Show results
        print(f"\n📊 ETHEREUM VALIDATION:")
        for api_name, balance in eth_balances.items():
            if balance > 0:
                print(f"   🎉 {api_name}: {balance:,} wei ({balance / 1e18:.18f} ETH)")
            else:
                print(f"   ⚪ {api_name}: {balance} wei")
        
        print(f"\n📊 BITCOIN VALIDATION:")
        for api_name, balance in btc_balances.items():
            if balance > 0:
                print(f"   🎉 {api_name}: {balance:,} sat ({balance / 1e8:.8f} BTC)")
            else:
                print(f"   ⚪ {api_name}: {balance} sat")
        
        # Calculate total confirmed balances
        eth_confirmed = max(eth_balances.values()) if eth_balances else 0
        btc_confirmed = max(btc_balances.values()) if btc_balances else 0
        
        print(f"\n💎 CONFIRMED JACKPOT VALUES:")
        print(f"   💰 ETH: {eth_confirmed:,} wei ({eth_confirmed / 1e18:.18f} ETH)")
        print(f"   💰 BTC: {btc_confirmed:,} sat ({btc_confirmed / 1e8:.8f} BTC)")
        
        # Check transaction history
        print(f"\n📜 TRANSACTION HISTORY:")
        self.check_transaction_history(eth_address, btc_address)
        
        return {
            'private_key': private_key_hex,
            'eth_address': eth_address,
            'btc_address': btc_address,
            'eth_balance_confirmed': eth_confirmed,
            'btc_balance_confirmed': btc_confirmed,
            'eth_validations': eth_balances,
            'btc_validations': btc_balances,
            'validated_at': datetime.now().isoformat()
        }
    
    def derive_addresses(self, private_key_hex):
        """Derive addresses from private key"""
        try:
            if private_key_hex.startswith('0x'):
                private_key_hex = private_key_hex[2:]
            
            # Ethereum
            private_key_bytes = bytes.fromhex(private_key_hex)
            eth_key = keys.PrivateKey(private_key_bytes)
            eth_address = eth_key.public_key.to_checksum_address()
            
            # Bitcoin
            btc_key = Key.from_hex(private_key_hex)
            btc_address = btc_key.address
            
            return eth_address, btc_address
            
        except Exception as e:
            print(f"❌ Error deriving addresses: {e}")
            return None, None
    
    def validate_eth_balance(self, address):
        """Validate Ethereum balance with multiple APIs"""
        balances = {}
        
        # Etherscan
        try:
            eth_apis = self.api_manager.get_ethereum_apis()
            
            if eth_apis.get('etherscan'):
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': address,
                    'tag': 'latest',
                    'apikey': eth_apis['etherscan']
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        balances['Etherscan'] = int(data.get('result', 0))
        except Exception as e:
            balances['Etherscan'] = f"Error: {e}"
        
        # Alchemy
        try:
            if eth_apis.get('alchemy'):
                url = f"https://eth-mainnet.g.alchemy.com/v2/{eth_apis['alchemy']}"
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                
                response = requests.post(url, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        balances['Alchemy'] = int(data['result'], 16)
        except Exception as e:
            balances['Alchemy'] = f"Error: {e}"
        
        # Infura
        try:
            if eth_apis.get('infura'):
                url = f"https://mainnet.infura.io/v3/{eth_apis['infura']}"
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                
                response = requests.post(url, json=payload, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        balances['Infura'] = int(data['result'], 16)
        except Exception as e:
            balances['Infura'] = f"Error: {e}"
        
        return balances
    
    def validate_btc_balance(self, address):
        """Validate Bitcoin balance with multiple APIs"""
        balances = {}
        
        # Blockstream
        try:
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                funded = data.get('chain_stats', {}).get('funded_txo_sum', 0)
                spent = data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balances['Blockstream'] = funded - spent
        except Exception as e:
            balances['Blockstream'] = f"Error: {e}"
        
        # BlockCypher
        try:
            url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                balances['BlockCypher'] = data.get('balance', 0)
        except Exception as e:
            balances['BlockCypher'] = f"Error: {e}"
        
        return balances
    
    def check_transaction_history(self, eth_address, btc_address):
        """Check transaction history for both addresses"""
        
        # Ethereum transactions
        print("   🔍 Ethereum Transactions:")
        try:
            eth_apis = self.api_manager.get_ethereum_apis()
            
            if eth_apis.get('etherscan'):
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': eth_address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'sort': 'desc',
                    'apikey': eth_apis['etherscan']
                }
                
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1':
                        txs = data.get('result', [])
                        print(f"     📊 Total transactions: {len(txs)}")
                        
                        if txs:
                            latest = txs[0]
                            print(f"     📅 Latest: Block {latest.get('blockNumber')}")
                            print(f"     💰 Value: {int(latest.get('value', 0)):,} wei")
                        else:
                            print(f"     💡 No transactions found")
                    else:
                        print(f"     ⚠️ API Error: {data.get('message', 'Unknown')}")
                else:
                    print(f"     ❌ Request failed: {response.status_code}")
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
        # Bitcoin transactions
        print("   🔍 Bitcoin Transactions:")
        try:
            url = f"https://blockstream.info/api/address/{btc_address}/txs"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                txs = response.json()
                print(f"     📊 Total transactions: {len(txs)}")
                
                if txs:
                    latest = txs[0]
                    print(f"     📅 Latest: {latest.get('status', {}).get('block_time')}")
                    print(f"     🔗 TXID: {latest.get('txid')}")
                else:
                    print(f"     💡 No transactions found")
            else:
                print(f"     ❌ Request failed: {response.status_code}")
        except Exception as e:
            print(f"     ❌ Error: {e}")

def main():
    """Validate the discovered jackpot"""
    validator = JackpotValidator()
    
    # The jackpot private key
    jackpot_key = "aa102235a5ccb18bd3668c0e14aa3ea7e2503cfac2a7a9bf3d6549899e125af4"
    
    result = validator.validate_jackpot(jackpot_key)
    
    # Save validation result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"JACKPOT_VALIDATION_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n💾 Validation saved: {filename}")

if __name__ == "__main__":
    main()
