#!/usr/bin/env python3
"""
Demo script for CSV export functionality
Shows how the CSV export works with mock data
"""

import asyncio
from datetime import datetime
from token_analyzer import SolanaTokenAnalyzer, TokenHolder, SnapshotInfo


async def demo_csv_export():
    """Demonstrate CSV export with mock data"""
    print("📊 CSV EXPORT DEMO")
    print("=" * 50)
    
    # Create mock analyzer
    analyzer = SolanaTokenAnalyzer()
    
    # Create mock snapshot info
    snapshot_info = SnapshotInfo(
        block_number=123456789,
        timestamp=datetime.now(),
        slot=123456789
    )
    
    # Create mock token holders
    mock_holders = [
        TokenHolder(
            address="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",
            owner="9WzDXwHNVqhMGNB4mN2Wnfyp6ZjXsF8kJ7Kb3KLmm4mN2",
            balance=1000000000,
            percentage=45.5,
            account_type="user"
        ),
        TokenHolder(
            address="3Hx8qP7NyYyRF5Lm9KjT2VpQx4YkD6sG8mN1oP2Qr5Ss7",
            owner="TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            balance=500000000,
            percentage=22.7,
            account_type="program"
        ),
        TokenHolder(
            address="7dHbWXmci3dT1aHLVFbvQJN5BZQC7LzUJZ9V8k3KaP5X",
            owner="2vb8kM9qYm7sP4XtLcN6Fg8dR3BxTw5KpN7Q9h4L8mX3",
            balance=300000000,
            percentage=13.6,
            account_type="user"
        ),
        TokenHolder(
            address="8mN2sP5vT9wX7fK3qH6B4cL8dR5eY7nA1pU9tJ2iO4sX",
            owner="ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
            balance=200000000,
            percentage=9.1,
            account_type="program"
        ),
        TokenHolder(
            address="4pQ7rX3fN8kL9dB6mY2cW5vH1sT8eJ4iN6uA7gR3oP2X",
            owner="1nc1nerator11111111111111111111111111111111",
            balance=100000000,
            percentage=4.5,
            account_type="user"
        )
    ]
    
    mock_mint = "ExampleToken123456789abcdefghijklmnopqrstuvwxyz"
    
    # Export to CSV
    print("📄 Exporting mock data to CSV...")
    csv_filename = await analyzer.export_to_csv(mock_holders, mock_mint, snapshot_info)
    
    print(f"✅ CSV file created: {csv_filename}")
    
    # Show first few lines of the CSV
    print(f"\n📋 Preview of {csv_filename}:")
    print("-" * 50)
    
    with open(csv_filename, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:15]):  # Show first 15 lines
            print(f"{i+1:2d}: {line.rstrip()}")
        
        if len(lines) > 15:
            print(f"... and {len(lines) - 15} more lines")
    
    await analyzer.close()
    
    print(f"\n🎯 Demo complete! Check the file '{csv_filename}' for the full export.")


if __name__ == "__main__":
    asyncio.run(demo_csv_export()) 