"""
Test suite for Solana Token Holder Analyzer
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from token_analyzer import SolanaTokenAnalyzer, TokenHolder
from solders.pubkey import Pubkey as PublicKey


@dataclass
class MockTokenSupplyValue:
    amount: str
    decimals: int
    ui_amount: float
    ui_amount_string: str


@dataclass
class MockTokenSupplyResponse:
    value: MockTokenSupplyValue


@dataclass
class MockTokenAmount:
    amount: str
    decimals: int
    ui_amount: float
    ui_amount_string: str


@dataclass
class MockTokenAccountInfo:
    owner: str
    tokenAmount: MockTokenAmount


@dataclass
class MockTokenAccountData:
    info: MockTokenAccountInfo


@dataclass
class MockParsedAccountData:
    parsed: MockTokenAccountData


@dataclass
class MockTokenAccount:
    data: MockParsedAccountData


@dataclass
class MockTokenAccountWrapper:
    account: MockTokenAccount


@dataclass
class MockAccountInfo:
    executable: bool
    lamports: int
    owner: str
    rent_epoch: int
    data: bytes


@dataclass
class MockAccountInfoResponse:
    value: MockAccountInfo


class TestSolanaTokenAnalyzer:
    """Test cases for SolanaTokenAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return SolanaTokenAnalyzer("https://api.mainnet-beta.solana.com")
    
    @pytest.fixture
    def mock_token_accounts(self):
        """Create mock token account data for largest accounts response"""
        @dataclass
        class MockLargestAccount:
            address: str
            amount: str
            decimals: int
            ui_amount: float
            ui_amount_string: str
        
        return [
            MockLargestAccount(
                address="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",
                amount="1000000000",
                decimals=6,
                ui_amount=1000.0,
                ui_amount_string="1000"
            ),
            MockLargestAccount(
                address="9WzDXwHNVqhMGNB4mN2Wnfyp6ZjXsF8kJ7Kb3KLmm4mN2",
                amount="500000000",
                decimals=6,
                ui_amount=500.0,
                ui_amount_string="500"
            ),
            MockLargestAccount(
                address="3Hx8qP7NyYyRF5Lm9KjT2VpQx4YkD6sG8mN1oP2Qr5Ss7",
                amount="0",  # Zero balance - should be filtered out
                decimals=6,
                ui_amount=0.0,
                ui_amount_string="0"
            )
        ]

    @pytest.mark.asyncio
    async def test_get_token_supply_success(self, analyzer):
        """Test successful token supply retrieval"""
        mock_response = MockTokenSupplyResponse(
            value=MockTokenSupplyValue(
                amount="1000000000000",
                decimals=6,
                ui_amount=1000000.0,
                ui_amount_string="1000000"
            )
        )
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_response):
            supply = await analyzer.get_token_supply("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            assert supply == 1000000000000

    @pytest.mark.asyncio
    async def test_get_token_supply_failure(self, analyzer):
        """Test token supply retrieval failure"""
        with patch.object(analyzer.client, 'get_token_supply', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Failed to get token supply"):
                await analyzer.get_token_supply("invalid_mint")

    @pytest.mark.asyncio
    async def test_get_token_supply_no_value(self, analyzer):
        """Test token supply retrieval with no value"""
        mock_response = MagicMock()
        mock_response.value = None
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_response):
            supply = await analyzer.get_token_supply("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            assert supply == 0

    @pytest.mark.asyncio
    async def test_get_token_accounts_success(self, analyzer, mock_token_accounts):
        """Test successful token accounts retrieval"""
        mock_response = MagicMock()
        mock_response.value = mock_token_accounts
        
        with patch.object(analyzer.client, 'get_token_largest_accounts', return_value=mock_response):
            accounts = await analyzer.get_token_accounts("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            assert len(accounts) == 3
            assert accounts == mock_token_accounts

    @pytest.mark.asyncio
    async def test_get_token_accounts_failure(self, analyzer):
        """Test token accounts retrieval failure"""
        with patch.object(analyzer.client, 'get_token_largest_accounts', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Failed to get token accounts"):
                await analyzer.get_token_accounts("invalid_mint")

    @pytest.mark.asyncio
    async def test_is_program_account_true(self, analyzer):
        """Test program account detection - executable account"""
        mock_response = MockAccountInfoResponse(
            value=MockAccountInfo(
                executable=True,
                lamports=1000000,
                owner="11111111111111111111111111111112",
                rent_epoch=250,
                data=b""
            )
        )
        
        with patch.object(analyzer.client, 'get_account_info', return_value=mock_response):
            is_program = await analyzer.is_program_account("5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8")
            assert is_program is True

    @pytest.mark.asyncio
    async def test_is_program_account_false(self, analyzer):
        """Test program account detection - non-executable account"""
        mock_response = MockAccountInfoResponse(
            value=MockAccountInfo(
                executable=False,
                lamports=1000000,
                owner="11111111111111111111111111111112",
                rent_epoch=250,
                data=b""
            )
        )
        
        with patch.object(analyzer.client, 'get_account_info', return_value=mock_response):
            is_program = await analyzer.is_program_account("5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8")
            assert is_program is False

    @pytest.mark.asyncio
    async def test_analyze_token_holders_success(self, analyzer, mock_token_accounts):
        """Test complete token holder analysis"""
        # Mock token supply
        mock_supply_response = MockTokenSupplyResponse(
            value=MockTokenSupplyValue(
                amount="1500000000",  # Total supply
                decimals=6,
                ui_amount=1500.0,
                ui_amount_string="1500"
            )
        )
        
        # Mock token accounts
        mock_accounts_response = MagicMock()
        mock_accounts_response.value = mock_token_accounts
        
        # Mock account info responses for program detection
        user_account_response = MockAccountInfoResponse(
            value=MockAccountInfo(executable=False, lamports=1000000, owner="", rent_epoch=250, data=b"")
        )
        program_account_response = MockAccountInfoResponse(
            value=MockAccountInfo(executable=True, lamports=1000000, owner="", rent_epoch=250, data=b"")
        )
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_supply_response), \
             patch.object(analyzer.client, 'get_token_largest_accounts', return_value=mock_accounts_response), \
             patch.object(analyzer.client, 'get_account_info', side_effect=[user_account_response, program_account_response]):
            
            holders = await analyzer.analyze_token_holders("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            
            # Should have 2 holders (excluding zero balance)
            assert len(holders) == 2
            
            # Check first holder (largest)
            assert holders[0].address == "5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8"
            assert holders[0].balance == 1000000000
            assert holders[0].percentage == (1000000000 / 1500000000) * 100
            assert holders[0].account_type == "user"
            
            # Check second holder
            assert holders[1].address == "9WzDXwHNVqhMGNB4mN2Wnfyp6ZjXsF8kJ7Kb3KLmm4mN2"
            assert holders[1].balance == 500000000
            assert holders[1].percentage == (500000000 / 1500000000) * 100
            assert holders[1].account_type == "program"

    @pytest.mark.asyncio
    async def test_analyze_token_holders_zero_supply(self, analyzer):
        """Test analysis with zero token supply"""
        mock_supply_response = MockTokenSupplyResponse(
            value=MockTokenSupplyValue(amount="0", decimals=6, ui_amount=0.0, ui_amount_string="0")
        )
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_supply_response):
            with pytest.raises(Exception, match="Token not found or has zero supply"):
                await analyzer.analyze_token_holders("invalid_mint")

    @pytest.mark.asyncio
    async def test_close_client(self, analyzer):
        """Test client closing"""
        with patch.object(analyzer.client, 'close', new_callable=AsyncMock) as mock_close:
            await analyzer.close()
            mock_close.assert_called_once()


class TestTokenHolder:
    """Test cases for TokenHolder dataclass"""
    
    def test_token_holder_creation(self):
        """Test TokenHolder dataclass creation"""
        holder = TokenHolder(
            address="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",
            balance=1000000,
            percentage=50.0,
            account_type="user"
        )
        
        assert holder.address == "5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8"
        assert holder.balance == 1000000
        assert holder.percentage == 50.0
        assert holder.account_type == "user"


class TestUtilityFunctions:
    """Test utility functions and edge cases"""
    
    def test_public_key_validation(self):
        """Test PublicKey validation with valid address"""
        valid_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        try:
            PublicKey.from_string(valid_address)
            assert True
        except Exception:
            assert False, "Valid address should not raise exception"
    
    def test_public_key_validation_invalid(self):
        """Test PublicKey validation with invalid address"""
        invalid_address = "invalid_address"
        with pytest.raises(Exception):
            PublicKey.from_string(invalid_address)


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    @pytest.mark.asyncio
    async def test_duplicate_owners(self):
        """Test handling of multiple accounts with same owner"""
        analyzer = SolanaTokenAnalyzer()
        
        # Mock accounts with same owner
        duplicate_accounts = [
            MockTokenAccountWrapper(
                account=MockTokenAccount(
                    data=MockParsedAccountData(
                        parsed=MockTokenAccountData(
                            info=MockTokenAccountInfo(
                                owner="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",
                                tokenAmount=MockTokenAmount(amount="300000000", decimals=6, ui_amount=300.0, ui_amount_string="300")
                            )
                        )
                    )
                )
            ),
            MockTokenAccountWrapper(
                account=MockTokenAccount(
                    data=MockParsedAccountData(
                        parsed=MockTokenAccountData(
                            info=MockTokenAccountInfo(
                                owner="5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8",  # Same owner
                                tokenAmount=MockTokenAmount(amount="700000000", decimals=6, ui_amount=700.0, ui_amount_string="700")
                            )
                        )
                    )
                )
            )
        ]
        
        mock_supply_response = MockTokenSupplyResponse(
            value=MockTokenSupplyValue(amount="1000000000", decimals=6, ui_amount=1000.0, ui_amount_string="1000")
        )
        
        mock_accounts_response = MagicMock()
        mock_accounts_response.value = duplicate_accounts
        
        user_account_response = MockAccountInfoResponse(
            value=MockAccountInfo(executable=False, lamports=1000000, owner="", rent_epoch=250, data=b"")
        )
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_supply_response), \
             patch.object(analyzer.client, 'get_token_accounts_by_mint', return_value=mock_accounts_response), \
             patch.object(analyzer.client, 'get_account_info', return_value=user_account_response):
            
            holders = await analyzer.analyze_token_holders("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            
            # Should have 1 holder with combined balance
            assert len(holders) == 1
            assert holders[0].address == "5Q544fKyKrfqJQv2Lmj8m4EZhLLjSeFdRBJ8XXvKK7Rj8"
            assert holders[0].balance == 1000000000  # 300M + 700M
            assert holders[0].percentage == 100.0
        
        await analyzer.close()

    @pytest.mark.asyncio
    async def test_sorting_by_percentage(self):
        """Test that holders are properly sorted by percentage"""
        analyzer = SolanaTokenAnalyzer()
        
        # Mock accounts with different balances
        mixed_accounts = [
            MockTokenAccountWrapper(
                account=MockTokenAccount(
                    data=MockParsedAccountData(
                        parsed=MockTokenAccountData(
                            info=MockTokenAccountInfo(
                                owner="small_holder",
                                tokenAmount=MockTokenAmount(amount="100000000", decimals=6, ui_amount=100.0, ui_amount_string="100")
                            )
                        )
                    )
                )
            ),
            MockTokenAccountWrapper(
                account=MockTokenAccount(
                    data=MockParsedAccountData(
                        parsed=MockTokenAccountData(
                            info=MockTokenAccountInfo(
                                owner="large_holder",
                                tokenAmount=MockTokenAmount(amount="800000000", decimals=6, ui_amount=800.0, ui_amount_string="800")
                            )
                        )
                    )
                )
            ),
            MockTokenAccountWrapper(
                account=MockTokenAccount(
                    data=MockParsedAccountData(
                        parsed=MockTokenAccountData(
                            info=MockTokenAccountInfo(
                                owner="medium_holder",
                                tokenAmount=MockTokenAmount(amount="200000000", decimals=6, ui_amount=200.0, ui_amount_string="200")
                            )
                        )
                    )
                )
            )
        ]
        
        mock_supply_response = MockTokenSupplyResponse(
            value=MockTokenSupplyValue(amount="1100000000", decimals=6, ui_amount=1100.0, ui_amount_string="1100")
        )
        
        mock_accounts_response = MagicMock()
        mock_accounts_response.value = mixed_accounts
        
        user_account_response = MockAccountInfoResponse(
            value=MockAccountInfo(executable=False, lamports=1000000, owner="", rent_epoch=250, data=b"")
        )
        
        with patch.object(analyzer.client, 'get_token_supply', return_value=mock_supply_response), \
             patch.object(analyzer.client, 'get_token_accounts_by_mint', return_value=mock_accounts_response), \
             patch.object(analyzer.client, 'get_account_info', return_value=user_account_response):
            
            holders = await analyzer.analyze_token_holders("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
            
            # Should be sorted by percentage (descending)
            assert len(holders) == 3
            assert holders[0].address == "large_holder"
            assert holders[0].percentage > holders[1].percentage
            assert holders[1].address == "medium_holder"
            assert holders[1].percentage > holders[2].percentage
            assert holders[2].address == "small_holder"
        
        await analyzer.close()


if __name__ == "__main__":
    pytest.main([__file__]) 