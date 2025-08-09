#!/usr/bin/env python3
"""
Secure Wallet Import Script
Helps format private keys for safe import into wallet software
"""

import sys
import getpass

def main():
    print("🔐 SECURE WALLET IMPORT ASSISTANT")
    print("=" * 50)
    
    # Your recovered keys
    keys = [
        "b597a26f1636c43d0f390ade41eefc219c2d7ef80af5542ddfbd23ed98725dd4",
        "16e4c3027f332cd0b83b2bc886bcf23c277479073844d29a070680dfc27d0d41"
    ]
    
    addresses = {
        keys[0]: {
            "ethereum": "0xff0B84464603AD6A0b46495bfd0E13b654194023",
            "bitcoin": "1Je9nE7cCya1e5Ny9qFREDXmMCw97UbZgh",
            "solana": "Acte5ZRRne7hJuwLvo2ESoDn9qCP8hwN1bnhjNoM43es"
        },
        keys[1]: {
            "ethereum": "0x88227b39ba522b5AeBf75f355118a57C3a4a243a",
            "bitcoin": "1Stanr1KfXpP54LY3MGZWQCgEuidneZXf", 
            "solana": "FqpRvHZYppycZ2BNtYanDhPku3YC6HWiaNk3AjJTGEQ2"
        }
    }
    
    print("\n📱 WALLET IMPORT OPTIONS:")
    print("1. MetaMask (Ethereum & EVM chains)")
    print("2. Trust Wallet (Multi-chain)")
    print("3. Phantom (Solana)")
    print("4. Exodus (Multi-chain)")
    print("5. Electrum (Bitcoin)")
    print("6. Show all keys for manual import")
    print("7. Check balances online")
    
    choice = input("\nSelect option (1-7): ").strip()
    
    if choice == "1":
        print("\n🦊 METAMASK IMPORT:")
        print("1. Open MetaMask extension")
        print("2. Click account icon (top right)")
        print("3. Select 'Import Account'")
        print("4. Choose 'Private Key'")
        print("5. Copy and paste ONE of these keys:")
        for i, key in enumerate(keys, 1):
            print(f"\n   Key #{i}: {key}")
            print(f"   Address: {addresses[key]['ethereum']}")
        print("\n⚠️  Import each key separately to create separate accounts")
        
    elif choice == "2":
        print("\n🛡️ TRUST WALLET IMPORT:")
        print("1. Open Trust Wallet app")
        print("2. Go to Settings → Wallets")
        print("3. Tap '+' → 'I already have a wallet'")
        print("4. Select 'Private Key'")
        print("5. Use these keys:")
        for i, key in enumerate(keys, 1):
            print(f"\n   Key #{i}: {key}")
            
    elif choice == "3":
        print("\n👻 PHANTOM IMPORT:")
        print("1. Open Phantom wallet")
        print("2. Settings → Add/Connect Wallet")
        print("3. Select 'Import Private Key'")
        print("4. Use these keys for Solana access:")
        for i, key in enumerate(keys, 1):
            print(f"\n   Key #{i}: {key}")
            print(f"   Solana Address: {addresses[key]['solana']}")
            
    elif choice == "4":
        print("\n🔒 EXODUS IMPORT:")
        print("1. Open Exodus wallet")
        print("2. Settings → Private Keys")
        print("3. Export/Import → Import Private Key")
        print("4. Select blockchain and paste key")
        
    elif choice == "5":
        print("\n₿ ELECTRUM IMPORT:")
        print("1. File → New/Restore")
        print("2. 'Import Bitcoin addresses or private keys'")
        print("3. Enter private keys:")
        for i, key in enumerate(keys, 1):
            print(f"\n   Key #{i}: {key}")
            print(f"   Bitcoin Address: {addresses[key]['bitcoin']}")
            
    elif choice == "6":
        print("\n📋 ALL PRIVATE KEYS:")
        for i, key in enumerate(keys, 1):
            print(f"\n🔑 KEY #{i}:")
            print(f"Private Key: {key}")
            print(f"Ethereum:    {addresses[key]['ethereum']}")
            print(f"Bitcoin:     {addresses[key]['bitcoin']}")
            print(f"Solana:      {addresses[key]['solana']}")
            
    elif choice == "7":
        print("\n💰 BALANCE CHECK LINKS:")
        for i, key in enumerate(keys, 1):
            print(f"\n🔍 KEY #{i} BALANCE CHECKS:")
            print(f"Ethereum: https://etherscan.io/address/{addresses[key]['ethereum']}")
            print(f"Bitcoin:  https://blockchair.com/bitcoin/address/{addresses[key]['bitcoin']}")
            print(f"Solana:   https://explorer.solana.com/address/{addresses[key]['solana']}")
    
    print("\n" + "=" * 50)
    print("⚠️  SECURITY REMINDERS:")
    print("• These private keys control your funds - keep them secret!")
    print("• Consider using a hardware wallet for large amounts")
    print("• Test with small amounts first")
    print("• Never enter private keys on suspicious websites")
    print("• Keep secure offline backups")

if __name__ == "__main__":
    main()
