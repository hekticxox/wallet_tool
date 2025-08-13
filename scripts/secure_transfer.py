#!/usr/bin/env python3
"""
Secure Coin Transfer Utility
Transfers discovered coins to your personal wallet addresses
"""

import json
import time
from decimal import Decimal
import requests
from bip_utils import WifEncoder, Bip44, Bip44Coins
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address
import hashlib

class SecureCoinTransfer:
    def __init__(self):
        self.load_config()
        self.load_funded_addresses()
        
    def load_config(self):
        """Load API configuration"""
        try:
            with open('api_config.json', 'r') as f:
                self.config = json.load(f)
                print("✅ API configuration loaded")
        except Exception as e:
            print(f"⚠️ Using default config: {e}")
            self.config = {
                "etherscan_api_key": "RHI2QM5XKCUI3TDNKSEVI28PGHR4RY9I79"
            }
    
    def load_funded_addresses(self):
        """Load all discovered funded addresses"""
        self.funded_addresses = []
        
        # Load from priority scanner results
        try:
            with open('PRIORITY_FUNDED_ADDRESSES.txt', 'r') as f:
                content = f.read()
                # Parse the funded addresses from the text file
                addresses = self.parse_funded_addresses_txt(content, 'priority')
                self.funded_addresses.extend(addresses)
        except:
            pass
        
        # Load from JSON format (enhanced scanner)
        try:
            with open('funded_addresses.json', 'r') as f:
                addresses = json.load(f)
                for addr in addresses:
                    addr['source_scanner'] = 'enhanced'
                self.funded_addresses.extend(addresses)
        except:
            pass
            
        print(f"💰 Loaded {len(self.funded_addresses)} funded addresses")
        
    def parse_funded_addresses_txt(self, content, source):
        """Parse funded addresses from text format"""
        addresses = []
        sections = content.split('FUNDED ADDRESS FOUND!')
        
        for section in sections[1:]:  # Skip first empty section
            lines = section.strip().split('\n')
            addr_info = {'source_scanner': source}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Address:'):
                    addr_info['address'] = line.split('Address:')[1].strip()
                elif line.startswith('Chain:'):
                    addr_info['chain'] = line.split('Chain:')[1].strip().lower()
                elif line.startswith('Balance:'):
                    balance_str = line.split('Balance:')[1].strip()
                    try:
                        addr_info['balance'] = float(balance_str)
                    except:
                        addr_info['balance'] = 0.0
                elif line.startswith('Private Key:'):
                    addr_info['private_key'] = line.split('Private Key:')[1].strip()
                elif line.startswith('Source:'):
                    addr_info['source'] = line.split('Source:')[1].strip()
                    
            if 'address' in addr_info and 'private_key' in addr_info:
                addresses.append(addr_info)
                
        return addresses
    
    def get_destination_addresses(self):
        """Get user's destination wallet addresses"""
        print("\n🏦 DESTINATION WALLET SETUP")
        print("============================")
        print("Please provide your personal wallet addresses where you want to receive the coins:")
        print("(Press Enter to skip a chain if you don't have a wallet for it)")
        print()
        
        destinations = {}
        
        # Bitcoin address
        btc_addr = input("🟠 Your Bitcoin address (starts with 1, 3, or bc1): ").strip()
        if btc_addr and self.validate_bitcoin_address(btc_addr):
            destinations['bitcoin'] = btc_addr
            print(f"✅ Bitcoin address validated: {btc_addr}")
        elif btc_addr:
            print(f"❌ Invalid Bitcoin address format")
            
        # Ethereum address  
        eth_addr = input("🟣 Your Ethereum address (starts with 0x): ").strip()
        if eth_addr and self.validate_ethereum_address(eth_addr):
            destinations['ethereum'] = eth_addr
            print(f"✅ Ethereum address validated: {eth_addr}")
        elif eth_addr:
            print(f"❌ Invalid Ethereum address format")
            
        # Solana address (if needed)
        sol_addr = input("🟢 Your Solana address (optional): ").strip()
        if sol_addr:
            destinations['solana'] = sol_addr
            print(f"✅ Solana address added: {sol_addr}")
        
        return destinations
    
    def validate_bitcoin_address(self, address):
        """Basic Bitcoin address validation"""
        if not address:
            return False
        # Legacy addresses (1...)
        if address.startswith('1') and len(address) >= 26 and len(address) <= 35:
            return True
        # P2SH addresses (3...)
        if address.startswith('3') and len(address) >= 26 and len(address) <= 35:
            return True
        # Bech32 addresses (bc1...)
        if address.startswith('bc1') and len(address) >= 39 and len(address) <= 62:
            return True
        return False
    
    def validate_ethereum_address(self, address):
        """Basic Ethereum address validation"""
        if not address or len(address) != 42 or not address.startswith('0x'):
            return False
        try:
            int(address[2:], 16)  # Check if hex
            return True
        except:
            return False
    
    def estimate_transfer_fees(self, chain, balance):
        """Estimate transfer fees for each chain"""
        fees = {
            'bitcoin': 0.00005,  # ~$3 at current prices
            'ethereum': 0.002,   # ~$5-10 depending on gas
            'solana': 0.000005   # ~$0.001
        }
        
        return fees.get(chain, 0.001)
    
    def check_transfer_viability(self, address_info, destination):
        """Check if transfer is economically viable"""
        chain = address_info['chain']
        balance = address_info['balance']
        estimated_fee = self.estimate_transfer_fees(chain, balance)
        
        print(f"\n📊 Transfer Analysis for {chain.upper()}:")
        print(f"   Address: {address_info['address']}")
        print(f"   Current Balance: {balance}")
        print(f"   Estimated Fee: {estimated_fee}")
        print(f"   Net Amount: {balance - estimated_fee}")
        
        if balance <= estimated_fee:
            print(f"   ❌ Not viable: Balance too low to cover fees")
            return False
        elif (balance - estimated_fee) < estimated_fee:
            print(f"   ⚠️  Marginal: Very little profit after fees")
            return input("   Continue anyway? (y/n): ").lower().startswith('y')
        else:
            print(f"   ✅ Viable: Good profit margin")
            return True
    
    def create_bitcoin_transaction(self, address_info, destination, amount):
        """Create Bitcoin transaction (framework - requires actual implementation)"""
        print(f"🟠 Creating Bitcoin transaction...")
        print(f"   From: {address_info['address']}")
        print(f"   To: {destination}")
        print(f"   Amount: {amount} BTC")
        
        # This is where you'd implement actual Bitcoin transaction creation
        # You'd need libraries like python-bitcoinlib or similar
        print("   ⚠️  Bitcoin transaction creation requires additional implementation")
        print("   📝 Private key available for manual transfer if needed")
        
        return None
    
    def create_ethereum_transaction(self, address_info, destination, amount):
        """Create Ethereum transaction (framework - requires actual implementation)"""
        print(f"🟣 Creating Ethereum transaction...")
        print(f"   From: {address_info['address']}")
        print(f"   To: {destination}")
        print(f"   Amount: {amount} ETH")
        
        # This is where you'd implement actual Ethereum transaction creation
        # You'd need web3.py and proper gas estimation
        print("   ⚠️  Ethereum transaction creation requires additional implementation")
        print("   📝 Private key available for manual transfer if needed")
        
        return None
    
    def generate_manual_transfer_instructions(self, address_info, destination):
        """Generate manual transfer instructions"""
        print(f"\n📋 MANUAL TRANSFER INSTRUCTIONS")
        print("=" * 50)
        print(f"Chain: {address_info['chain'].upper()}")
        print(f"Source Address: {address_info['address']}")
        print(f"Private Key: {address_info['private_key']}")
        print(f"Destination: {destination}")
        print(f"Balance: {address_info['balance']}")
        print()
        
        if address_info['chain'] == 'bitcoin':
            print("🟠 Bitcoin Transfer Instructions:")
            print("1. Import private key into a Bitcoin wallet (Electrum, Bitcoin Core, etc.)")
            print("2. Send the full balance to your destination address")
            print("3. Use a reasonable fee (0.00005 - 0.0001 BTC)")
            
        elif address_info['chain'] == 'ethereum':
            print("🟣 Ethereum Transfer Instructions:")
            print("1. Import private key into MetaMask, MyEtherWallet, or similar")
            print("2. Send ETH to your destination address")
            print("3. Leave some ETH for gas fees (~0.002 ETH)")
            
        print("\n⚠️  SECURITY WARNING:")
        print("- Use these private keys immediately and transfer all funds")
        print("- These keys were found in databases and may not be secure")
        print("- Never reuse these addresses after transfer")
        print("-" * 50)
    
    def save_transfer_instructions(self, instructions):
        """Save transfer instructions to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"transfer_instructions_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("🏦 CRYPTO TRANSFER INSTRUCTIONS\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for instruction in instructions:
                f.write(instruction + "\n\n")
                
        print(f"📁 Instructions saved to: {filename}")
    
    def run_transfer_setup(self):
        """Main transfer setup process"""
        print("🚀 SECURE COIN TRANSFER UTILITY")
        print("=" * 40)
        
        if not self.funded_addresses:
            print("❌ No funded addresses found. Run the scanners first!")
            return
            
        print(f"💰 Found {len(self.funded_addresses)} funded addresses:")
        for i, addr in enumerate(self.funded_addresses, 1):
            print(f"   {i}. {addr['chain'].upper()}: {addr['balance']} ({addr['address'][:20]}...)")
        
        # Get destination addresses
        destinations = self.get_destination_addresses()
        
        if not destinations:
            print("❌ No valid destination addresses provided!")
            return
            
        print(f"\n✅ Destination addresses configured:")
        for chain, addr in destinations.items():
            print(f"   {chain.upper()}: {addr}")
        
        # Process each funded address
        transfer_instructions = []
        
        for addr_info in self.funded_addresses:
            chain = addr_info['chain']
            
            if chain not in destinations:
                print(f"\n⚠️  Skipping {chain.upper()} address - no destination configured")
                continue
                
            destination = destinations[chain]
            
            if self.check_transfer_viability(addr_info, destination):
                # Generate manual transfer instructions
                instruction_text = f"""
TRANSFER #{len(transfer_instructions) + 1} - {chain.upper()}
Source: {addr_info['address']}
Destination: {destination}
Private Key: {addr_info['private_key']}
Balance: {addr_info['balance']}
Scanner: {addr_info.get('source_scanner', 'unknown')}
"""
                transfer_instructions.append(instruction_text)
                self.generate_manual_transfer_instructions(addr_info, destination)
        
        # Save all instructions
        if transfer_instructions:
            self.save_transfer_instructions(transfer_instructions)
            
            print(f"\n🎉 TRANSFER SETUP COMPLETE!")
            print(f"📋 {len(transfer_instructions)} transfers ready")
            print(f"📁 Instructions saved for manual execution")
            print(f"\n💡 Next Steps:")
            print(f"   1. Follow the manual transfer instructions")
            print(f"   2. Transfer funds immediately for security")
            print(f"   3. Never reuse the source addresses")
        else:
            print(f"\n😔 No viable transfers found")
            print(f"   Balances may be too low to cover transaction fees")

def main():
    transfer_util = SecureCoinTransfer()
    transfer_util.run_transfer_setup()

if __name__ == "__main__":
    main()
