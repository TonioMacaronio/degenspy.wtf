#!/usr/bin/env python3
"""
Complete CSV Demo - Shows all CSV export functionality
"""

import asyncio
import os
from datetime import datetime
from token_analyzer import SolanaTokenAnalyzer, TokenHolder, SnapshotInfo


async def demo_all_csv_features():
    """Demonstrate all CSV export features"""
    print("📊 COMPLETE CSV EXPORT DEMO")
    print("=" * 60)
    
    # Create mock analyzer
    analyzer = SolanaTokenAnalyzer()
    
    # Create realistic snapshot info
    snapshot_info = SnapshotInfo(
        block_number=287654321,
        timestamp=datetime.now(),
        slot=287654321
    )
    
    # Create comprehensive mock data
    mock_holders = [
        TokenHolder("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", 50000000000000, 35.2, "program"),
        TokenHolder("So11111111111111111111111111111111111111112", "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL", 25000000000000, 17.6, "program"),
        TokenHolder("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB", "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4", 20000000000000, 14.1, "program"),
        TokenHolder("5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8", "9WzDXwHNVqhMGNB4mN2Wnfyp6ZjXsF8kJ7Kb3KLmm4mN2", 10000000000000, 7.0, "user"),
        TokenHolder("3Hx8qP7NyYyRF5Lm9KjT2VpQx4YkD6sG8mN1oP2Qr5Ss7", "2vb8kM9qYm7sP4XtLcN6Fg8dR3BxTw5KpN7Q9h4L8mX3", 8000000000000, 5.6, "user"),
        TokenHolder("7dHbWXmci3dT1aHLVFbvQJN5BZQC7LzUJZ9V8k3KaP5X", "8mN2sP5vT9wX7fK3qH6B4cL8dR5eY7nA1pU9tJ2iO4sX", 6000000000000, 4.2, "user"),
        TokenHolder("6dHbWXmci3dT1aHLVFbvQJN5BZQC7LzUJZ9V8k3KaP5Z", "CAMMCzo5YL8w4VFF8KVHrK22GGUQzaNm4fLK7vQ4CxNE", 5000000000000, 3.5, "program"),
        TokenHolder("5vb8kM9qYm7sP4XtLcN6Fg8dR3BxTw5KpN7Q9h4L8mX4", "4pQ7rX3fN8kL9dB6mY2cW5vH1sT8eJ4iN6uA7gR3oP2X", 4000000000000, 2.8, "user"),
        TokenHolder("4mN2sP5vT9wX7fK3qH6B4cL8dR5eY7nA1pU9tJ2iO4sY", "1nc1nerator11111111111111111111111111111111", 3500000000000, 2.5, "user"),
        TokenHolder("3pQ7rX3fN8kL9dB6mY2cW5vH1sT8eJ4iN6uA7gR3oP2Z", "burn1111111111111111111111111111111111111111", 3000000000000, 2.1, "user"),
    ]
    
    mock_mint = "DemoToken987654321abcdefghijk"
    
    print(f"🎯 Mock Token: {mock_mint}")
    print(f"📈 Total Holders: {len(mock_holders)}")
    print(f"🏦 Block/Slot: {snapshot_info.block_number}")
    print(f"⏰ Timestamp: {snapshot_info.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Demo 1: Auto-generated filename
    print("1️⃣ AUTO-GENERATED FILENAME")
    print("-" * 30)
    csv_file_1 = await analyzer.export_to_csv(mock_holders, mock_mint, snapshot_info)
    print(f"✅ Created: {csv_file_1}")
    
    # Demo 2: Custom filename
    print("\n2️⃣ CUSTOM FILENAME")
    print("-" * 30)
    custom_filename = "my_token_analysis_demo.csv"
    csv_file_2 = await analyzer.export_to_csv(mock_holders, mock_mint, snapshot_info, custom_filename)
    print(f"✅ Created: {csv_file_2}")
    
    # Demo 3: Show file contents
    print("\n3️⃣ FILE CONTENT PREVIEW")
    print("-" * 30)
    
    with open(csv_file_1, 'r') as f:
        lines = f.readlines()
        
    print(f"📄 {csv_file_1} ({len(lines)} lines):")
    for i, line in enumerate(lines[:12], 1):
        print(f"{i:2d}: {line.rstrip()}")
    
    if len(lines) > 12:
        print(f"... and {len(lines) - 12} more data rows")
    
    # Demo 4: File size info
    print("\n4️⃣ FILE STATISTICS")
    print("-" * 30)
    
    file_size_1 = os.path.getsize(csv_file_1)
    file_size_2 = os.path.getsize(csv_file_2)
    
    print(f"📊 {csv_file_1}: {file_size_1} bytes")
    print(f"📊 {csv_file_2}: {file_size_2} bytes")
    
    # Summary
    print("\n5️⃣ USAGE EXAMPLES")
    print("-" * 30)
    print("Command line usage:")
    print(f"  🔸 Auto filename:  python3 token_analyzer.py -m {mock_mint} --csv")
    print(f"  🔸 Custom name:    python3 token_analyzer.py -m {mock_mint} --csv-file analysis.csv")
    print(f"  🔸 CSV only:       python3 token_analyzer.py -m {mock_mint} --csv-only")
    
    await analyzer.close()
    
    print(f"\n✅ Demo complete! Files created:")
    print(f"   • {csv_file_1}")
    print(f"   • {csv_file_2}")


if __name__ == "__main__":
    asyncio.run(demo_all_csv_features()) 