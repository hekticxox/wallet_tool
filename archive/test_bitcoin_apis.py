#!/usr/bin/env python3
"""Test multiple Bitcoin APIs to see which ones work and their response formats"""

import requests
import time

def test_all_bitcoin_apis(test_address):
    """Test all Bitcoin APIs with a known address"""
    
    apis_config = [
        ("Mempool.space", "https://mempool.space/api", f"/address/{test_address}"),
        ("Blockstream", "https://blockstream.info/api", f"/address/{test_address}"),
        ("Blockchain.info", "https://blockchain.info", f"/rawaddr/{test_address}?limit=0"),
        ("BlockCypher", "https://api.blockcypher.com/v1/btc/main", f"/addrs/{test_address}/balance"),
        ("BitPay Insight", "https://insight.bitpay.com/api", f"/addr/{test_address}")
    ]
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'WalletRecovery/2.0'})
    
    working_apis = []
    
    for name, base_url, endpoint in apis_config:
        try:
            url = base_url + endpoint
            print(f"\n🌐 Testing {name}:")
            print(f"   URL: {url}")
            
            start_time = time.time()
            response = session.get(url, timeout=10)
            response_time = time.time() - start_time
            
            print(f"   Status: {response.status_code} ({response_time:.2f}s)")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ SUCCESS - JSON response received")
                    
                    # Try to extract balance from different formats
                    balance_sats = 0
                    balance_found = False
                    
                    if 'chain_stats' in data and 'funded_txo_sum' in data['chain_stats']:
                        balance_sats = data['chain_stats']['funded_txo_sum']
                        balance_found = True
                        print(f"   💰 Balance (Blockstream format): {balance_sats} satoshis")
                    elif 'final_balance' in data:
                        balance_sats = data['final_balance']
                        balance_found = True
                        print(f"   💰 Balance (Blockchain.info format): {balance_sats} satoshis")
                    elif 'balance' in data:
                        if isinstance(data['balance'], int):
                            balance_sats = data['balance']
                            balance_found = True
                            print(f"   💰 Balance (Generic satoshi format): {balance_sats} satoshis")
                        else:
                            balance_btc = float(data['balance'])
                            balance_found = True
                            print(f"   💰 Balance (BTC format): {balance_btc} BTC")
                    elif 'balanceSat' in data:
                        balance_sats = data['balanceSat']
                        balance_found = True
                        print(f"   💰 Balance (Insight format): {balance_sats} satoshis")
                    
                    if balance_found:
                        if balance_sats > 0:
                            balance_btc = balance_sats / 100000000
                            print(f"   💰 Balance in BTC: {balance_btc}")
                        working_apis.append((name, base_url, endpoint))
                        print(f"   🎯 API WORKING - Added to working list")
                    else:
                        print(f"   ⚠️  Could not find balance field in response")
                        print(f"   📝 Available fields: {list(data.keys())}")
                
                except ValueError as e:
                    print(f"   ❌ JSON parsing failed: {e}")
                    
            elif response.status_code == 429:
                print(f"   ⚠️  Rate limited - might work with slower requests")
            else:
                print(f"   ❌ HTTP error: {response.status_code}")
                if response.text:
                    print(f"   📝 Response: {response.text[:100]}...")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout (10s)")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Small delay between API calls to be respectful
        time.sleep(1)
    
    print(f"\n📊 SUMMARY:")
    print(f"   APIs tested: {len(apis_config)}")
    print(f"   Working APIs: {len(working_apis)}")
    
    if working_apis:
        print(f"\n✅ WORKING APIs:")
        for name, base_url, endpoint in working_apis:
            print(f"   • {name}: {base_url}")
    else:
        print(f"\n❌ No working APIs found")
    
    return working_apis

if __name__ == "__main__":
    # Test with a known Bitcoin address with balance (Satoshi's address)
    test_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Genesis block address
    
    print("🚀 Testing Bitcoin APIs...")
    print(f"📍 Test address: {test_address}")
    print("="*60)
    
    working_apis = test_all_bitcoin_apis(test_address)
    
    print("="*60)
    print("🎉 Test complete!")
