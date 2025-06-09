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


@dataclass
class TokenHolder:
    address: str
    balance: int
    percentage: float
    account_type: str  # "user" or "program"


class SolanaTokenAnalyzer:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.client = AsyncClient(rpc_url)
    
    async def close(self):
        """Close the RPC client"""
        await self.client.close()
    
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
    
    async def get_token_accounts(self, mint_address: str) -> List[Dict]:
        """Get largest token accounts for a given mint"""
        try:
            mint_pubkey = PublicKey.from_string(mint_address)
            
            # Get largest token accounts for this mint (top 20 by default)
            response = await self.client.get_token_largest_accounts(
                mint_pubkey,
                commitment=Confirmed
            )
            
            if response.value:
                return response.value
            return []
        except Exception as e:
            # If largest accounts fails, it might be due to:
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
        
        # Get all token accounts
        token_accounts = await self.get_token_accounts(mint_address)
        if not token_accounts:
            raise Exception("No token accounts found")
        
        print(f"🏦 Found {len(token_accounts)} token accounts")
        
        # Group by owner and sum balances
        owner_balances: Dict[str, int] = {}
        
        for account in token_accounts:
            try:
                # Handle different response structures
                if hasattr(account, 'address') and hasattr(account, 'amount'):
                    # Structure from get_token_largest_accounts
                    owner = str(account.address)
                    
                    # Handle different amount types
                    if hasattr(account.amount, 'amount'):
                        # UiTokenAmount object with .amount attribute
                        balance = int(account.amount.amount)
                    else:
                        # Direct string amount
                        balance = int(account.amount)
                        
                elif hasattr(account, 'account'):
                    # Old structure from get_token_accounts_by_mint
                    account_data = account.account.data.parsed
                    owner = account_data["info"]["owner"]
                    balance = int(account_data["info"]["tokenAmount"]["amount"])
                else:
                    print(f"⚠️  Warning: Unknown account structure: {account}")
                    print(f"   Available attributes: {[attr for attr in dir(account) if not attr.startswith('_')]}")
                    continue
                
                if balance > 0:  # Only include accounts with positive balance
                    if owner in owner_balances:
                        owner_balances[owner] += balance
                    else:
                        owner_balances[owner] = balance
            except Exception as e:
                print(f"⚠️  Warning: Failed to process account: {e}")
                continue
        
        # Create holder objects with account type detection
        holders = []
        total_holders = len(owner_balances)
        
        print(f"🔎 Checking account types for {total_holders} unique holders...")
        
        for i, (owner, balance) in enumerate(owner_balances.items(), 1):
            if i % 10 == 0 or i == total_holders:
                print(f"  Progress: {i}/{total_holders}")
            
            percentage = (balance / total_supply) * 100
            is_program = await self.is_program_account(owner)
            account_type = "program" if is_program else "user"
            
            holders.append(TokenHolder(
                address=owner,
                balance=balance,
                percentage=percentage,
                account_type=account_type
            ))
        
        # Sort by percentage (descending)
        holders.sort(key=lambda x: x.percentage, reverse=True)
        
        return holders


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
def cli_main(mint: Optional[str], rpc: str, limit: int, start: Optional[int], end: Optional[int]):
    """Solana Token Holder Analyzer CLI"""
    
    if mint:
        # Run with provided mint address
        analyzer = SolanaTokenAnalyzer(rpc)
        
        async def analyze():
            try:
                holders = await analyzer.analyze_token_holders(mint)
                
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
                
                table_data = []
                for i, holder in enumerate(display_holders):
                    actual_rank = (start - 1 if start else 0) + i + 1  # Calculate actual rank
                    balance_str = f"{holder.balance:,}"
                    percentage_str = f"{holder.percentage:.6f}%"
                    address_display = holder.address
                    
                    table_data.append([
                        actual_rank,
                        address_display,
                        balance_str,
                        percentage_str,
                        holder.account_type.upper()
                    ])
                
                headers = ["Rank", "Address", "Balance", "Ownership %", "Type"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
                
                print(f"\nShowing {range_info} of {len(holders)} total holders")
                
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