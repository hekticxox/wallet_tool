#!/usr/bin/env python3
"""
Manual Bitcoin Address Verifier
Double-check balances using multiple APIs and block explorers
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class BitcoinAddressVerifier:
    def __init__(self):
        self.target_addresses = [
            "16QaFeudRUt8NYy2yzjm3BMvG4xBbAsBFM",
            "1CsFKRQmNj7pkVg5CrPLeXKyzZ8T2Ltu7Y"
        ]
        
        # Multiple API endpoints for verification
        self.api_endpoints = {
            'blockstream': 'https://blockstream.info/api/address',
            'blockchain_info': 'https://blockchain.info/rawaddr',
            'blockcypher': 'https://api.blockcypher.com/v1/btc/main/addrs',
            'blockchair': 'https://api.blockchair.com/bitcoin/dashboards/address'
        }
    
    async def check_blockstream(self, session: aiohttp.ClientSession, address: str) -> dict:
        """Check balance using Blockstream API"""
        try:
            url = f"{self.api_endpoints['blockstream']}/{address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    chain_stats = data.get('chain_stats', {})
                    balance_sat = chain_stats.get('funded_txo_sum', 0) - chain_stats.get('spent_txo_sum', 0)
                    return {
                        'api': 'blockstream',
                        'balance_sat': balance_sat,
                        'balance_btc': balance_sat / 100000000,
                        'status': 'success',
                        'funded_txo_sum': chain_stats.get('funded_txo_sum', 0),
                        'spent_txo_sum': chain_stats.get('spent_txo_sum', 0),
                        'tx_count': chain_stats.get('tx_count', 0)
                    }
        except Exception as e:
            return {'api': 'blockstream', 'error': str(e), 'status': 'error'}
    
    async def check_blockchain_info(self, session: aiohttp.ClientSession, address: str) -> dict:
        """Check balance using Blockchain.info API"""
        try:
            url = f"{self.api_endpoints['blockchain_info']}/{address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_sat = data.get('final_balance', 0)
                    return {
                        'api': 'blockchain_info',
                        'balance_sat': balance_sat,
                        'balance_btc': balance_sat / 100000000,
                        'status': 'success',
                        'total_received': data.get('total_received', 0),
                        'total_sent': data.get('total_sent', 0),
                        'n_tx': data.get('n_tx', 0)
                    }
        except Exception as e:
            return {'api': 'blockchain_info', 'error': str(e), 'status': 'error'}
    
    async def check_blockcypher(self, session: aiohttp.ClientSession, address: str) -> dict:
        """Check balance using BlockCypher API"""
        try:
            url = f"{self.api_endpoints['blockcypher']}/{address}/balance"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    balance_sat = data.get('balance', 0)
                    return {
                        'api': 'blockcypher',
                        'balance_sat': balance_sat,
                        'balance_btc': balance_sat / 100000000,
                        'status': 'success',
                        'total_received': data.get('total_received', 0),
                        'total_sent': data.get('total_sent', 0),
                        'n_tx': data.get('n_tx', 0),
                        'unconfirmed_balance': data.get('unconfirmed_balance', 0)
                    }
        except Exception as e:
            return {'api': 'blockcypher', 'error': str(e), 'status': 'error'}
    
    async def check_blockchair(self, session: aiohttp.ClientSession, address: str) -> dict:
        """Check balance using Blockchair API"""
        try:
            url = f"{self.api_endpoints['blockchair']}/{address}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    address_data = data.get('data', {}).get(address, {}).get('address', {})
                    balance_sat = address_data.get('balance', 0)
                    return {
                        'api': 'blockchair',
                        'balance_sat': balance_sat,
                        'balance_btc': balance_sat / 100000000,
                        'status': 'success',
                        'received': address_data.get('received', 0),
                        'spent': address_data.get('spent', 0),
                        'transaction_count': address_data.get('transaction_count', 0)
                    }
        except Exception as e:
            return {'api': 'blockchair', 'error': str(e), 'status': 'error'}
    
    async def verify_address_comprehensive(self, address: str):
        """Verify address using all available APIs"""
        print(f"\n🔍 Comprehensive verification of {address}")
        print("-" * 60)
        
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        results = []
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Check all APIs concurrently
            tasks = [
                self.check_blockstream(session, address),
                self.check_blockchain_info(session, address),
                self.check_blockcypher(session, address),
                self.check_blockchair(session, address)
            ]
            
            api_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in api_results:
                if isinstance(result, dict):
                    results.append(result)
                    
                    if result.get('status') == 'success':
                        api_name = result['api']
                        balance_btc = result['balance_btc']
                        balance_sat = result['balance_sat']
                        
                        status_icon = "💰" if balance_btc > 0 else "🟢"
                        print(f"  {status_icon} {api_name:<15}: {balance_btc:.8f} BTC ({balance_sat:,} sat)")
                        
                        # Show additional details
                        if 'total_received' in result:
                            received_btc = result['total_received'] / 100000000
                            sent_btc = result.get('total_sent', 0) / 100000000
                            print(f"     {'':15}  Received: {received_btc:.8f} BTC, Sent: {sent_btc:.8f} BTC")
                        
                        if 'tx_count' in result:
                            print(f"     {'':15}  Transactions: {result['tx_count']}")
                        elif 'n_tx' in result:
                            print(f"     {'':15}  Transactions: {result['n_tx']}")
                        elif 'transaction_count' in result:
                            print(f"     {'':15}  Transactions: {result['transaction_count']}")
                    else:
                        api_name = result['api']
                        error = result.get('error', 'Unknown error')
                        print(f"  ❌ {api_name:<15}: Error - {error}")
        
        return results
    
    async def verify_all_addresses(self):
        """Verify all target addresses"""
        print("🚀 BITCOIN ADDRESS VERIFICATION")
        print("=" * 60)
        print(f"📅 Verification Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Checking {len(self.target_addresses)} addresses across {len(self.api_endpoints)} APIs")
        
        all_results = {}
        
        for address in self.target_addresses:
            results = await self.verify_address_comprehensive(address)
            all_results[address] = results
            
            # Analyze consensus
            successful_results = [r for r in results if r.get('status') == 'success']
            if successful_results:
                balances = [r['balance_btc'] for r in successful_results]
                avg_balance = sum(balances) / len(balances)
                consensus = all(abs(b - avg_balance) < 0.00000001 for b in balances)  # 1 satoshi tolerance
                
                print(f"\n  📊 Consensus Analysis:")
                print(f"      APIs Responding: {len(successful_results)}/{len(self.api_endpoints)}")
                print(f"      Average Balance: {avg_balance:.8f} BTC")
                print(f"      Consensus: {'✅ Yes' if consensus else '⚠️  No'}")
                
                if not consensus:
                    print(f"      Balance Range: {min(balances):.8f} - {max(balances):.8f} BTC")
            
            await asyncio.sleep(1)  # Rate limiting between addresses
        
        # Summary
        print(f"\n📋 VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_consensus_balance = 0
        
        for address, results in all_results.items():
            successful_results = [r for r in results if r.get('status') == 'success']
            if successful_results:
                avg_balance = sum(r['balance_btc'] for r in successful_results) / len(successful_results)
                total_consensus_balance += avg_balance
                
                status = "🟢 EMPTY" if avg_balance == 0 else f"💰 {avg_balance:.8f} BTC"
                print(f"  {address}: {status}")
            else:
                print(f"  {address}: ❌ All APIs failed")
        
        print(f"\n💎 Total Verified Balance: {total_consensus_balance:.8f} BTC")
        print(f"💵 Estimated USD Value: ${total_consensus_balance * 65000:.2f}")
        
        if total_consensus_balance == 0:
            print(f"\n⚠️  WARNING: All addresses show zero balance!")
            print(f"   Possible reasons:")
            print(f"   • Funds have already been moved/swept")
            print(f"   • Addresses were dust/fake balances")
            print(f"   • API synchronization delays")
            print(f"   • Network or API issues")
        
        return all_results

async def main():
    verifier = BitcoinAddressVerifier()
    results = await verifier.verify_all_addresses()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"ADDRESS_VERIFICATION_{timestamp}.json"
    
    verification_data = {
        'verification_time': datetime.now().isoformat(),
        'addresses_checked': verifier.target_addresses,
        'api_endpoints_used': list(verifier.api_endpoints.keys()),
        'results': results
    }
    
    with open(results_file, 'w') as f:
        json.dump(verification_data, f, indent=2)
    
    print(f"\n💾 Verification results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())
