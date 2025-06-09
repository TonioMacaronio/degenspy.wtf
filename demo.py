#!/usr/bin/env python3
"""
Demo script for Solana Token Holder Analyzer
Shows the functionality with mock data
"""

import asyncio
from token_analyzer import SolanaTokenAnalyzer, TokenHolder
from tabulate import tabulate


async def demo_with_mock_data():
    """Demonstrate the analyzer with mock data"""
    print("🎯 SOLANA TOKEN HOLDER ANALYZER DEMO")
    print("=" * 60)
    
    # Create some mock token holders
    mock_holders = [
        TokenHolder(
            address="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",
            balance=1000000000,
            percentage=45.5,
            account_type="user"
        ),
        TokenHolder(
            address="9WzDXwHNVqhMGNB4mN2Wnfyp6ZjXsF8kJ7Kb3KLmm4mN2",
            balance=500000000,
            percentage=22.7,
            account_type="program"
        ),
        TokenHolder(
            address="3Hx8qP7NyYyRF5Lm9KjT2VpQx4YkD6sG8mN1oP2Qr5Ss7",
            balance=300000000,
            percentage=13.6,
            account_type="user"
        ),
        TokenHolder(
            address="7dHbWXmci3dT1aHLVFbvQJN5BZQC7LzUJZ9V8k3KaP5X",
            balance=200000000,
            percentage=9.1,
            account_type="program"
        ),
        TokenHolder(
            address="2vb8kM9qYm7sP4XtLcN6Fg8dR3BxTw5KpN7Q9h4L8mX3",
            balance=100000000,
            percentage=4.5,
            account_type="user"
        ),
        TokenHolder(
            address="8mN2sP5vT9wX7fK3qH6B4cL8dR5eY7nA1pU9tJ2iO4sX",
            balance=75000000,
            percentage=3.4,
            account_type="user"
        ),
        TokenHolder(
            address="4pQ7rX3fN8kL9dB6mY2cW5vH1sT8eJ4iN6uA7gR3oP2X",
            balance=25000000,
            percentage=1.1,
            account_type="program"
        )
    ]
    
    # Sort by percentage (should already be sorted)
    mock_holders.sort(key=lambda x: x.percentage, reverse=True)
    
    # Display results in the same format as the real app
    table_data = []
    total_percentage = 0
    user_count = 0
    program_count = 0
    
    for i, holder in enumerate(mock_holders, 1):
        # Format balance with commas
        balance_str = f"{holder.balance:,}"
        percentage_str = f"{holder.percentage:.6f}%"
        
        # Truncate address for display
        address_display = f"{holder.address[:8]}...{holder.address[-8:]}"
        
        table_data.append([
            i,
            address_display,
            balance_str,
            percentage_str,
            holder.account_type.upper()
        ])
        
        total_percentage += holder.percentage
        if holder.account_type == "user":
            user_count += 1
        else:
            program_count += 1
    
    # Display results
    print(f"🎯 TOKEN HOLDER ANALYSIS: ExampleToken123456789")
    print("=" * 60)
    
    headers = ["Rank", "Address", "Balance", "Ownership %", "Type"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary statistics
    print(f"\n📈 SUMMARY")
    print("-" * 40)
    print(f"Total holders: {len(mock_holders):,}")
    print(f"User accounts: {user_count:,}")
    print(f"Program accounts: {program_count:,}")
    print(f"Total ownership tracked: {total_percentage:.2f}%")
    
    # Top holders summary
    top_3_percentage = sum(h.percentage for h in mock_holders[:3])
    print(f"Top 3 holders own: {top_3_percentage:.2f}%")
    
    top_5_percentage = sum(h.percentage for h in mock_holders[:5])
    print(f"Top 5 holders own: {top_5_percentage:.2f}%")
    
    print("\n✅ Demo completed! This shows the expected output format.")
    print("📝 Note: This demo uses mock data. Real usage requires valid RPC access.")


async def demo_validator_functions():
    """Demo the validation and utility functions"""
    print("\n🔧 UTILITY FUNCTIONS DEMO")
    print("=" * 40)
    
    # Test PublicKey validation
    from solders.pubkey import Pubkey as PublicKey
    
    valid_addresses = [
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        "So11111111111111111111111111111111111111112",   # Wrapped SOL
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"   # USDT
    ]
    
    invalid_addresses = [
        "invalid_address",
        "123",
        "toolong" * 20
    ]
    
    print("✅ Valid addresses:")
    for addr in valid_addresses:
        try:
            PublicKey.from_string(addr)
            print(f"  ✓ {addr[:20]}... (Valid)")
        except Exception as e:
            print(f"  ✗ {addr[:20]}... (Invalid: {e})")
    
    print("\n❌ Invalid addresses:")
    for addr in invalid_addresses:
        try:
            PublicKey.from_string(addr)
            print(f"  ✗ {addr} (Should be invalid but passed)")
        except Exception:
            print(f"  ✓ {addr} (Correctly rejected)")


if __name__ == "__main__":
    print("Starting Solana Token Holder Analyzer Demo...\n")
    asyncio.run(demo_with_mock_data())
    asyncio.run(demo_validator_functions())
    print("\n�� Demo complete!") 