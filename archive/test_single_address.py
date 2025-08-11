#!/usr/bin/env python3
"""Test single address balance checking"""

import requests
import time

def test_bitcoin_api(address):
    """Test Bitcoin API call with our new error handling"""
    session = requests.Session()
    session.headers.update({'User-Agent': 'WalletRecovery/2.0'})
    
    apis = ["https://mempool.space/api", "https://blockstream.info/api"]
    
    for i, api_base in enumerate(apis):
        try:
            url = f"{api_base}/address/{address}"
            print(f"🌐 Testing {api_base.split('//')[1]} for {address[:12]}...{address[-8:]}", end="", flush=True)
            
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Different API response formats
                if 'chain_stats' in data:
                    # Blockstream format
                    balance_sats = data['chain_stats'].get('funded_txo_sum', 0)
                elif 'final_balance' in data:
                    # Blockchain.info format
                    balance_sats = data.get('final_balance', 0)
                else:
                    # Generic format
                    balance_sats = data.get('balance', 0)
                
                balance_btc = balance_sats / 100000000  # Convert satoshis to BTC
                
                print(f" ✅ Balance: {balance_btc} BTC")
                return balance_btc
            
            elif response.status_code == 429:
                print(f" ❌ Rate limited (429)")
                if i < len(apis) - 1:  # Not the last API
                    print(f"   🔄 Trying backup API in 3 seconds...")
                    time.sleep(3)
                    continue
                else:
                    print(f"   ❌ All APIs rate limited")
                    return 0
            
            else:
                print(f" ❌ HTTP {response.status_code}")
                continue
            
        except requests.exceptions.Timeout:
            print(f" ❌ Timeout (10s)")
            continue
        except requests.exceptions.ConnectionError:
            print(f" ❌ Connection failed")
            continue
        except Exception as e:
            print(f" ❌ Error: {str(e)[:30]}")
            continue
    
    print(f"❌ All APIs failed for this address")
    return 0

if __name__ == "__main__":
    # Test with the first address that was hanging
    test_address = "1JG5oFpGnj9TQ3v8BqKGCNLEJNK7iEqBr3CwTvie"
    result = test_bitcoin_api(test_address)
    print(f"Final result: {result} BTC")
