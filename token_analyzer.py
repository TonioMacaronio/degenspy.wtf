#!/usr/bin/env python3
"""
Solana Token Holder Analyzer
Analyzes token holders on Solana blockchain and shows ownership distribution
"""

import asyncio
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import click
from tabulate import tabulate
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey as PublicKey
from solana.rpc.types import TokenAccountOpts
from solana.rpc.commitment import Confirmed
import json
import csv
from datetime import datetime
import os


@dataclass
class TokenHolder:
    address: str  # Token account address
    owner: str    # Owner wallet address
    balance: int
    percentage: float
    account_type: str  # "user" or "program"


@dataclass
class SnapshotInfo:
    """Information about when the snapshot was taken"""
    block_number: int
    timestamp: datetime
    slot: int


class SolanaTokenAnalyzer:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.client = AsyncClient(rpc_url)
    
    async def close(self):
        """Close the RPC client"""
        await self.client.close()
    
    async def get_snapshot_info(self) -> SnapshotInfo:
        """Get current block information for snapshot metadata"""
        try:
            # Get current slot
            slot_response = await self.client.get_slot()
            slot = slot_response.value
            
            # Get block time (Unix timestamp)
            block_time_response = await self.client.get_block_time(slot)
            timestamp = datetime.fromtimestamp(block_time_response.value) if block_time_response.value else datetime.now()
            
            return SnapshotInfo(
                block_number=slot,  # In Solana, slot is equivalent to block number
                timestamp=timestamp,
                slot=slot
            )
        except Exception as e:
            # Fallback to current time if we can't get block info
            print(f"⚠️  Warning: Could not get block info, using current time: {e}")
            return SnapshotInfo(
                block_number=0,
                timestamp=datetime.now(),
                slot=0
            )
    
    async def get_token_supply(self, mint_address: str) -> int:
        """Get total supply of the token"""
        try:
            mint_pubkey = PublicKey.from_string(mint_address)
            response = await self.client.get_token_supply(mint_pubkey)
            if response.value:
                return int(response.value.amount)
            return 0
        except Exception as e:
            raise Exception(f"Failed to get token supply: {e}")
    
    async def get_token_accounts_with_owners(self, mint_address: str) -> List[Dict]:
        """Get token accounts and their owners for a given mint"""
        try:
            mint_pubkey = PublicKey.from_string(mint_address)
            
            # First try to get token accounts by mint (more detailed info)
            try:
                response = await self.client.get_token_accounts_by_mint(
                    mint_pubkey,
                    commitment=Confirmed
                )
                
                if response.value:
                    accounts_with_owners = []
                    for account_info in response.value:
                        if account_info.account and account_info.account.data:
                            parsed_data = account_info.account.data.parsed
                            if parsed_data and 'info' in parsed_data:
                                info = parsed_data['info']
                                accounts_with_owners.append({
                                    'account_address': str(account_info.pubkey),
                                    'owner': info.get('owner', ''),
                                    'amount': int(info.get('tokenAmount', {}).get('amount', 0))
                                })
                    return accounts_with_owners
            except Exception as e:
                print(f"⚠️  get_token_accounts_by_mint failed: {e}")
            
            # Fallback to largest accounts (less detailed but more reliable)
            print("🔄 Falling back to largest accounts method...")
            response = await self.client.get_token_largest_accounts(
                mint_pubkey,
                commitment=Confirmed
            )
            
            if response.value:
                # For largest accounts, we need to get account info for each to find owners
                accounts_with_owners = []
                print(f"🔍 Getting owner info for {len(response.value)} accounts...")
                
                for i, account in enumerate(response.value):
                    try:
                        account_address = str(account.address)
                        
                        # Get account info to find the owner
                        account_pubkey = PublicKey.from_string(account_address)
                        account_info = await self.client.get_account_info(account_pubkey)
                        
                        if account_info.value and account_info.value.data:
                            # Parse token account data to get owner
                            try:
                                # Token accounts are owned by the Token Program
                                # The actual wallet owner is stored in the account data
                                import base64
                                import struct
                                
                                data = account_info.value.data
                                if len(data) >= 32:  # Token account data structure
                                    # Owner is bytes 32-64 in token account data
                                    owner_bytes = data[32:64]
                                    owner_pubkey = PublicKey(owner_bytes)
                                    owner = str(owner_pubkey)
                                else:
                                    owner = str(account_info.value.owner)
                            except Exception:
                                owner = str(account_info.value.owner)
                        else:
                            owner = "Unknown"
                        
                        # Handle different amount types
                        if hasattr(account.amount, 'amount'):
                            balance = int(account.amount.amount)
                        else:
                            balance = int(account.amount)
                        
                        accounts_with_owners.append({
                            'account_address': account_address,
                            'owner': owner,
                            'amount': balance
                        })
                        
                        if (i + 1) % 5 == 0:
                            print(f"  Processed {i + 1}/{len(response.value)} accounts")
                            
                    except Exception as e:
                        print(f"⚠️  Failed to get owner for account {account.address}: {e}")
                        # Add with unknown owner
                        balance = int(account.amount.amount) if hasattr(account.amount, 'amount') else int(account.amount)
                        accounts_with_owners.append({
                            'account_address': str(account.address),
                            'owner': 'Unknown',
                            'amount': balance
                        })
                
                return accounts_with_owners
            
            return []
            
        except Exception as e:
            # If all methods fail, it might be due to:
            # - Token has no holders
            # - Token is too small/new
            # - API limitations
            # - Rate limiting
            error_msg = str(e)
            if "429" in error_msg or "rate" in error_msg.lower():
                raise Exception(f"Rate limited by RPC endpoint. Try again later or use a different RPC endpoint.")
            elif "not found" in error_msg.lower():
                raise Exception(f"Token not found or has no holders.")
            else:
                raise Exception(f"Unable to fetch token holders. This might be due to: token has no holders, token is too new/small, or API limitations. Error: {e}")
    
    async def is_program_account(self, address: str) -> bool:
        """Check if an address is a program account or program-owned account"""
        try:
            pubkey = PublicKey.from_string(address)
            account_info = await self.client.get_account_info(pubkey)
            
            if account_info.value is None:
                return False
            
            account = account_info.value
            
            # Check if it's an executable program
            if account.executable:
                return True
            
            # Check if it's owned by known programs (making it a program-controlled account)
            owner_str = str(account.owner)
            
            # Known program owners that indicate program-controlled accounts
            program_owners = {
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token Program
                "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",  # Associated Token Program
                "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter
                "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",  # Whirlpool
                "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Pump.fun
                "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",   # Pump.fun bonding curve
                "CAMMCzo5YL8w4VFF8KVHrK22GGUQzaNm4fLK7vQ4CxNE",  # Raydium
                "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium Authority v4
            }
            
            # If owned by a known program, it's a program-controlled account
            if owner_str in program_owners:
                return True
                
            # If owned by System Program, it's typically a user wallet
            if owner_str == "11111111111111111111111111111111":
                return False
                
            # Unknown owner - could be another program, but be conservative
            return False
            
        except Exception:
            return False
    
    async def analyze_token_holders(self, mint_address: str) -> List[TokenHolder]:
        """Analyze token holders and return sorted list by ownership percentage"""
        print(f"🔍 Analyzing token holders for: {mint_address}")
        
        # Get total supply
        total_supply = await self.get_token_supply(mint_address)
        if total_supply == 0:
            raise Exception("Token not found or has zero supply")
        
        print(f"📊 Total supply: {total_supply:,}")
        
        # Get all token accounts with their owners
        token_accounts = await self.get_token_accounts_with_owners(mint_address)
        if not token_accounts:
            raise Exception("No token accounts found")
        
        print(f"🏦 Found {len(token_accounts)} token accounts")
        
        # Group by owner and track account details
        owner_data: Dict[str, Dict] = {}
        
        for account in token_accounts:
            try:
                account_address = account['account_address']
                owner = account['owner']
                balance = account['amount']
                
                if balance > 0:  # Only include accounts with positive balance
                    if owner in owner_data:
                        owner_data[owner]['total_balance'] += balance
                        owner_data[owner]['account_addresses'].append(account_address)
                    else:
                        owner_data[owner] = {
                            'total_balance': balance,
                            'account_addresses': [account_address],
                            'primary_account': account_address  # Store the first/largest account
                        }
            except Exception as e:
                print(f"⚠️  Warning: Failed to process account: {e}")
                continue
        
        # Create holder objects with account type detection
        holders = []
        total_holders = len(owner_data)
        
        print(f"🔎 Checking account types for {total_holders} unique owners...")
        
        for i, (owner, data) in enumerate(owner_data.items(), 1):
            if i % 10 == 0 or i == total_holders:
                print(f"  Progress: {i}/{total_holders}")
            
            percentage = (data['total_balance'] / total_supply) * 100
            is_program = await self.is_program_account(owner)
            account_type = "program" if is_program else "user"
            
            # Use the primary account address (first one) for display
            primary_account = data['primary_account']
            
            holders.append(TokenHolder(
                address=primary_account,  # Token account address
                owner=owner,              # Owner wallet address
                balance=data['total_balance'],
                percentage=percentage,
                account_type=account_type
            ))
        
        # Sort by percentage (descending)
        holders.sort(key=lambda x: x.percentage, reverse=True)
        
        return holders
    
    async def export_to_csv(self, holders: List[TokenHolder], mint_address: str, snapshot_info: SnapshotInfo, filename: Optional[str] = None) -> str:
        """Export token holder data to CSV file"""
        if not filename:
            # Generate filename with timestamp
            timestamp_str = snapshot_info.timestamp.strftime("%Y%m%d_%H%M%S")
            short_mint = mint_address[:8]
            filename = f"token_holders_{short_mint}_{timestamp_str}.csv"
        
        # Ensure the filename has .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write metadata header
            writer.writerow(['# Token Holder Analysis Export'])
            writer.writerow(['# Mint Address:', mint_address])
            writer.writerow(['# Snapshot Block:', snapshot_info.block_number])
            writer.writerow(['# Snapshot Slot:', snapshot_info.slot])
            writer.writerow(['# Snapshot Time:', snapshot_info.timestamp.isoformat()])
            writer.writerow(['# Export Time:', datetime.now().isoformat()])
            writer.writerow(['# Total Holders:', len(holders)])
            writer.writerow([])  # Empty row for separation
            
            # Write data headers
            writer.writerow(['Rank', 'Token_Account', 'Owner_Address', 'Balance', 'Percentage', 'Account_Type'])
            
            # Write holder data
            for i, holder in enumerate(holders, 1):
                writer.writerow([
                    i,
                    holder.address,    # Token account address
                    holder.owner,      # Owner wallet address
                    holder.balance,
                    f"{holder.percentage:.6f}",
                    holder.account_type
                ])
        
        return filename


async def main():
    analyzer = SolanaTokenAnalyzer()
    
    try:
        # Get token mint address from user
        mint_address = input("Enter token mint address: ").strip()
        
        if not mint_address:
            print("❌ Token mint address is required")
            return
        
        # Validate address format
        try:
            PublicKey.from_string(mint_address)
        except Exception:
            print("❌ Invalid token mint address format")
            return
        
        # Analyze token holders
        holders = await analyzer.analyze_token_holders(mint_address)
        
        if not holders:
            print("❌ No token holders found")
            return
        
        # Prepare data for display
        table_data = []
        total_percentage = 0
        user_count = 0
        program_count = 0
        
        for i, holder in enumerate(holders, 1):
            # Format balance with commas
            balance_str = f"{holder.balance:,}"
            percentage_str = f"{holder.percentage:.6f}%"
            
            # Show full address
            address_display = holder.address
            
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
        print("\n" + "="*80)
        print(f"🎯 TOKEN HOLDER ANALYSIS: {mint_address}")
        print("="*80)
        
        headers = ["Rank", "Address", "Balance", "Ownership %", "Type"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Summary statistics
        print(f"\n📈 SUMMARY")
        print("-" * 40)
        print(f"Total holders: {len(holders):,}")
        print(f"User accounts: {user_count:,}")
        print(f"Program accounts: {program_count:,}")
        print(f"Total ownership tracked: {total_percentage:.2f}%")
        
        # Top holders summary
        if len(holders) >= 10:
            top_10_percentage = sum(h.percentage for h in holders[:10])
            print(f"Top 10 holders own: {top_10_percentage:.2f}%")
        
        if len(holders) >= 100:
            top_100_percentage = sum(h.percentage for h in holders[:100])
            print(f"Top 100 holders own: {top_100_percentage:.2f}%")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await analyzer.close()


@click.command()
@click.option('--mint', '-m', help='Token mint address')
@click.option('--rpc', '-r', default='https://api.mainnet-beta.solana.com', 
              help='Solana RPC endpoint')
@click.option('--limit', '-l', default=100, type=int, 
              help='Limit number of results to display (ignored if start/end specified)')
@click.option('--start', '-s', default=None, type=int,
              help='Starting rank (1-based index)')
@click.option('--end', '-e', default=None, type=int,
              help='Ending rank (1-based index, inclusive)')
@click.option('--csv', '-c', is_flag=True,
              help='Export to CSV file with auto-generated filename')
@click.option('--csv-file', default=None, type=str,
              help='Export to CSV with custom filename')
@click.option('--csv-only', is_flag=True,
              help='Only export CSV, skip console output')
def cli_main(mint: Optional[str], rpc: str, limit: int, start: Optional[int], end: Optional[int], csv: bool, csv_file: Optional[str], csv_only: bool):
    """Solana Token Holder Analyzer CLI"""
    
    if mint:
        # Run with provided mint address
        analyzer = SolanaTokenAnalyzer(rpc)
        
        async def analyze():
            try:
                # Get snapshot info first
                snapshot_info = await analyzer.get_snapshot_info()
                
                holders = await analyzer.analyze_token_holders(mint)
                
                # Handle CSV export
                csv_filename = None
                if csv or csv_file or csv_only:
                    csv_filename = await analyzer.export_to_csv(holders, mint, snapshot_info, csv_file)
                    print(f"💾 Exported to: {csv_filename}")
                
                # Skip console output if csv_only flag is set
                if csv_only:
                    print(f"✅ CSV export complete: {len(holders)} holders exported")
                    return
                
                # Display snapshot information
                print(f"\n📊 SNAPSHOT INFORMATION")
                print("-" * 40)
                print(f"Block/Slot: {snapshot_info.block_number}")
                print(f"Timestamp: {snapshot_info.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"ISO Time: {snapshot_info.timestamp.isoformat()}")
                
                # Determine which holders to display
                if start is not None or end is not None:
                    # Range-based display
                    start_idx = max(0, (start - 1) if start else 0)  # Convert to 0-based
                    end_idx = min(len(holders), end if end else len(holders))  # Inclusive end
                    
                    if start_idx >= len(holders):
                        print(f"❌ Start rank {start} exceeds total holders ({len(holders)})")
                        return
                    
                    display_holders = holders[start_idx:end_idx]
                    range_start = start_idx + 1
                    range_end = end_idx
                    range_info = f"ranks {range_start}-{range_end}"
                else:
                    # Limit-based display (default behavior)
                    display_holders = holders[:limit]
                    range_info = f"top {len(display_holders)}"
                
                print(f"\n🎯 TOKEN HOLDER ANALYSIS: {mint}")
                print("=" * 80)
                
                table_data = []
                for i, holder in enumerate(display_holders):
                    actual_rank = (start - 1 if start else 0) + i + 1  # Calculate actual rank
                    balance_str = f"{holder.balance:,}"
                    percentage_str = f"{holder.percentage:.6f}%"
                    
                    # Truncate addresses for display
                    token_account_display = f"{holder.address[:8]}...{holder.address[-8:]}"
                    owner_display = f"{holder.owner[:8]}...{holder.owner[-8:]}"
                    
                    table_data.append([
                        actual_rank,
                        token_account_display,
                        owner_display,
                        balance_str,
                        percentage_str,
                        holder.account_type.upper()
                    ])
                
                headers = ["Rank", "Token Account", "Owner", "Balance", "Ownership %", "Type"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                print(f"\nShowing {range_info} of {len(holders)} total holders")
                
                # Summary statistics
                print(f"\n📈 SUMMARY")
                print("-" * 40)
                print(f"Total holders: {len(holders):,}")
                user_count = sum(1 for h in holders if h.account_type == "user")
                program_count = len(holders) - user_count
                print(f"User accounts: {user_count:,}")
                print(f"Program accounts: {program_count:,}")
                
                total_percentage = sum(h.percentage for h in holders)
                print(f"Total ownership tracked: {total_percentage:.2f}%")
                
                if csv_filename:
                    print(f"\n💾 Data exported to: {csv_filename}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                await analyzer.close()
        
        asyncio.run(analyze())
    else:
        # Run interactive mode
        asyncio.run(main())


if __name__ == "__main__":
    cli_main() 