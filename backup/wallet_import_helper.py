#!/usr/bin/env python3
"""
Wallet Import Helper
Formats recovered private keys for different wallet software
"""

import json
from eth_keys import keys as eth_keys
from eth_utils import to_checksum_address
from solders.keypair import Keypair as SolanaKeypair
from bip_utils import Bip44, Bip44Coins

# Your recovered private keys
private_keys = [
    "b597a26f1636c43d0f390ade41eefc219c2d7ef80af5542ddfbd23ed98725dd4",
    "16e4c3027f332cd0b83b2bc886bcf23c277479073844d29a070680dfc27d0d41"
]

print("🔐 WALLET IMPORT GUIDE")
print("=" * 50)

for i, privkey in enumerate(private_keys, 1):
    print(f"\n📋 PRIVATE KEY #{i}:")
    print(f"Raw: {privkey}")
    print(f"With 0x prefix: 0x{privkey}")
    
    # Ethereum address
    try:
        priv_bytes = bytes.fromhex(privkey)
        pk = eth_keys.PrivateKey(priv_bytes)
        eth_address = to_checksum_address(pk.public_key.to_address())
        print(f"Ethereum Address: {eth_address}")
    except Exception as e:
        print(f"Ethereum Address: Error - {e}")
    
    # Solana address
    try:
        if len(priv_bytes) == 32:
            from nacl.signing import SigningKey
            signing_key = SigningKey(priv_bytes)
            kp = SolanaKeypair.from_bytes(signing_key._seed + signing_key.verify_key.encode())
        else:
            kp = SolanaKeypair.from_bytes(priv_bytes)
        solana_address = str(kp.pubkey())
        print(f"Solana Address: {solana_address}")
    except Exception as e:
        print(f"Solana Address: Error - {e}")
    
    # Bitcoin address
    try:
        bip44_mst = Bip44.FromPrivateKey(priv_bytes, Bip44Coins.BITCOIN)
        btc_address = bip44_mst.PublicKey().ToAddress()
        print(f"Bitcoin Address: {btc_address}")
    except Exception as e:
        print(f"Bitcoin Address: Error - {e}")

print("\n" + "=" * 50)
print("📱 IMPORT INSTRUCTIONS:")
print("=" * 50)

print("""
🦊 METAMASK (Ethereum, Polygon, BSC, etc.):
1. Click profile icon → Import Account
2. Select 'Private Key'
3. Paste private key (without 0x prefix)
4. Click Import

🛡️ TRUST WALLET (Multi-chain):
1. Settings → Wallets → + → Import Wallet
2. Select 'Private Key'
3. Paste private key
4. Enable desired networks

👻 PHANTOM (Solana):
1. Settings → Add/Connect Wallet
2. Import Private Key
3. Paste private key
4. Set name and confirm

₿ ELECTRUM (Bitcoin):
1. File → New/Restore
2. Import Bitcoin addresses or private keys
3. Enter private key
4. Follow setup wizard

🔒 EXODUS (Multi-chain):
1. Settings → Private Keys
2. Export/Import
3. Import Private Key
4. Select blockchain and paste key

⚠️  SECURITY TIPS:
• Never share these private keys with anyone
• Store them securely offline
• Consider using a hardware wallet for large amounts
• Test with small amounts first
• Keep backups in multiple secure locations
""")

print("\n💰 BALANCE CHECK COMMANDS:")
print("=" * 30)
print("# Check Ethereum balance:")
print(f"# Visit: https://etherscan.io/address/0xff0B84464603AD6A0b46495bfd0E13b654194023")
print(f"# Visit: https://etherscan.io/address/0x88227b39ba522b5AeBf75f355118a57C3a4a243a")
print("\n# Check Solana balance:")
print("# Visit: https://explorer.solana.com/address/[address]")
print("# Or use: solana balance [address]")
print("\n# Check Bitcoin balance:")
print("# Visit: https://blockchair.com/bitcoin/address/[address]")
