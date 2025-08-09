#!/usr/bin/env python3
"""
Continuous Balance Checker - Never stops until all addresses are checked
Modified version that runs indefinitely until all controlled addresses are verified
"""

import json
import time
import random
import requests
import sys
import os
import signal
from typing import Dict, List, Optional, Set

class ContinuousBalanceChecker:
    def __init__(self):
        self.running = True
        self.total_checked = 0
        self.total_found = 0
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Load wallet data
        try:
            with open('detected_wallet_data_summary.json', 'r') as f:
                self.wallet_data = json.load(f)
            print("📁 Wallet data loaded successfully")
        except Exception as e:
            print(f"❌ Error loading wallet data: {e}")
            sys.exit(1)
            
        # Build controlled addresses mapping
        self.controlled_addresses = self.build_controlled_mapping()
        print(f"🔑 Total controlled addresses: {len(self.controlled_addresses):,}")
        
    def signal_handler(self, signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def build_controlled_mapping(self):
        """Build mapping of addresses to their private keys"""
        controlled = {}
        cross_checks = self.wallet_data.get('cross_check_results', [])
        
        for check in cross_checks:
            if check.get('matched', False):
                addr = check['address']
                chain = check['chain']
                privkey = check['private_key']
                controlled[addr] = {
                    'chain': chain,
                    'private_key': privkey
                }
                
        return controlled
        
    def load_checking_history(self):
        """Load previously checked addresses"""
        try:
            with open('checked_addresses_history.json', 'r') as f:
                return json.load(f)
        except:
            return {}
            
    def save_checking_history(self, history):
        """Save checking history"""
        try:
            with open('checked_addresses_history.json', 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
            
    def check_ethereum_balance(self, address):
        """Check Ethereum balance"""
        try:
            time.sleep(random.uniform(2.0, 4.0))  # Rate limiting
            url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=YourApiKeyToken"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    wei = int(data['result'])
                    eth = wei / 1e18
                    return eth, 'etherscan'
        except Exception as e:
            print(f"⚠️ ETH API error for {address[:10]}...: {e}")
            
        return 0.0, 'error'
        
    def check_bitcoin_balance(self, address):
        """Check Bitcoin balance"""
        try:
            time.sleep(random.uniform(2.0, 4.0))  # Rate limiting
            url = f"https://blockstream.info/api/address/{address}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                balance_sat = data.get('chain_stats', {}).get('funded_txo_sum', 0) - \
                             data.get('chain_stats', {}).get('spent_txo_sum', 0)
                balance_btc = balance_sat / 1e8
                return balance_btc, 'blockstream'
        except Exception as e:
            print(f"⚠️ BTC API error for {address[:10]}...: {e}")
            
        return 0.0, 'error'
        
    def check_solana_balance(self, address):
        """Check Solana balance"""
        try:
            time.sleep(random.uniform(1.0, 2.0))  # Rate limiting
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [address]
            }
            
            response = requests.post(
                "https://api.mainnet-beta.solana.com",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data and 'value' in data['result']:
                    lamports = data['result']['value']
                    sol = lamports / 1e9
                    return sol, 'solana_rpc'
        except Exception as e:
            print(f"⚠️ SOL API error for {address[:10]}...: {e}")
            
        return 0.0, 'error'
        
    def check_address_balance(self, address, chain):
        """Check balance for a specific address"""
        if chain == 'ethereum':
            return self.check_ethereum_balance(address)
        elif chain == 'bitcoin':
            return self.check_bitcoin_balance(address)
        elif chain == 'solana':
            return self.check_solana_balance(address)
        else:
            return 0.0, 'unknown_chain'
            
    def run_continuous_checking(self):
        """Main continuous checking loop"""
        history = self.load_checking_history()
        addresses_to_check = [(addr, info) for addr, info in self.controlled_addresses.items() 
                            if addr not in history]
        
        print(f"🎯 Addresses to check: {len(addresses_to_check):,}")
        print(f"📚 Previously checked: {len(history):,}")
        
        if not addresses_to_check:
            print("✅ All controlled addresses have been checked!")
            return
            
        batch_size = 25
        batch_count = 0
        
        while self.running and addresses_to_check:
            batch_count += 1
            batch = addresses_to_check[:batch_size]
            addresses_to_check = addresses_to_check[batch_size:]
            
            print(f"\n🔸 Batch {batch_count} - Checking {len(batch)} addresses...")
            print(f"📊 Remaining: {len(addresses_to_check):,} addresses")
            
            for i, (address, info) in enumerate(batch, 1):
                if not self.running:
                    break
                    
                chain = info['chain']
                privkey = info['private_key']
                
                chain_short = chain[:3].upper()
                addr_short = address[:10] + '...'
                
                print(f"    {i:2d}/{len(batch)} {chain_short} {addr_short}", end="")
                
                balance, source = self.check_address_balance(address, chain)
                self.total_checked += 1
                
                # Save to history
                history[address] = {
                    'chain': chain,
                    'balance': balance,
                    'source': source,
                    'private_key': privkey,
                    'checked_at': time.time()
                }
                
                if balance > 0:
                    self.total_found += 1
                    print(f" 💰 {balance} {chain.upper()} - FUNDED! 🎉")
                    print(f"🔑 Private Key: {privkey}")
                    
                    # Log funded address to separate file
                    with open('FUNDED_ADDRESSES.txt', 'a') as f:
                        f.write(f"{time.ctime()}: {chain.upper()} {address} = {balance} (Private Key: {privkey})\n")
                        
                else:
                    print(f" 💸 0 {chain.upper()}")
                    
                # Save history every 10 addresses
                if self.total_checked % 10 == 0:
                    self.save_checking_history(history)
                    
            # Save batch results
            self.save_checking_history(history)
            
            # Short break between batches
            if self.running and addresses_to_check:
                print(f"⏳ Batch complete. Brief pause before next batch...")
                time.sleep(random.uniform(5, 10))
                
        # Final save and summary
        self.save_checking_history(history)
        
        print(f"\n🎉 CONTINUOUS CHECKING COMPLETE!")
        print(f"✅ Total addresses checked: {self.total_checked:,}")
        print(f"💰 Funded addresses found: {self.total_found}")
        
        if self.total_found > 0:
            print(f"📄 Funded addresses logged to: FUNDED_ADDRESSES.txt")
            
if __name__ == "__main__":
    print("🚀 CONTINUOUS BALANCE CHECKER")
    print("============================")
    print("Press Ctrl+C to stop gracefully")
    print()
    
    checker = ContinuousBalanceChecker()
    checker.run_continuous_checking()
