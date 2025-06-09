# Solana Token Holder Analyzer

A powerful console application that analyzes token holders on the Solana blockchain, showing ownership distribution and identifying whether holders are users or programs.

## Features

- 📊 **Complete Token Analysis**: Get all holders of any SPL token
- 🎯 **Ownership Ranking**: Sort holders by percentage of total supply
- 🔍 **Account Type Detection**: Distinguish between user accounts and programs
- 📈 **Rich Statistics**: Summary data including distribution metrics
- 🎨 **Beautiful Output**: Formatted tables with clear visualization
- ⚡ **Fast & Efficient**: Async operations for optimal performance

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd onchain-researcher
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Demo

Try the demo first to see the expected output:
```bash
python demo.py
```

## Usage

### Interactive Mode

Run the application and enter a token mint address when prompted:

```bash
python token_analyzer.py
```

### CLI Mode

Analyze a specific token directly:

```bash
python token_analyzer.py --mint <TOKEN_MINT_ADDRESS>
```

### Options

- `--mint, -m`: Token mint address to analyze
- `--rpc, -r`: Custom Solana RPC endpoint (default: mainnet-beta)
- `--limit, -l`: Limit number of results to display (default: 100)

### Examples

```bash
# Analyze USDC token holders
python token_analyzer.py --mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v

# Use custom RPC and limit results
python token_analyzer.py --mint EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v --rpc https://api.mainnet-beta.solana.com --limit 50
```

## Output Format

The application provides:

1. **Holder Rankings**: Ranked list showing:
   - Address (truncated for readability)
   - Token balance
   - Ownership percentage
   - Account type (USER/PROGRAM)

2. **Summary Statistics**:
   - Total number of holders
   - User vs program account counts
   - Top 10/100 holder concentration

## Account Type Detection

The application automatically determines if each holder is:
- **USER**: Regular user account (non-executable)
- **PROGRAM**: Smart contract/program account (executable)

## Requirements

- Python 3.7+
- Active internet connection
- Access to Solana RPC endpoint

## Dependencies

- `solana-py`: Solana Python SDK
- `click`: Command-line interface
- `tabulate`: Table formatting
- `asyncio-throttle`: Rate limiting
- `requests`: HTTP requests

## Error Handling

The application gracefully handles:
- Invalid token mint addresses
- Network connectivity issues
- Rate limiting
- Malformed token accounts

## Performance Notes

- Large tokens (many holders) may take several minutes to analyze
- Progress indicators show real-time status
- Uses async operations for optimal speed
- Respects RPC rate limits

## Testing

The application includes comprehensive tests covering all major functionality.

### Running Tests

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-mock
```

Run all tests:
```bash
python run_tests.py
# or
pytest tests/
```

Run specific tests:
```bash
python run_tests.py --test TestSolanaTokenAnalyzer::test_get_token_supply_success
```

Run with coverage:
```bash
python run_tests.py --coverage
```

### Test Coverage

The test suite includes:

- **Unit Tests**: Individual method testing with mocked dependencies
- **Integration Tests**: End-to-end workflow testing  
- **Edge Cases**: Error handling and malformed data
- **Data Processing**: Sorting, filtering, and aggregation logic

**Test Categories:**
- `TestSolanaTokenAnalyzer`: Core functionality tests
- `TestTokenHolder`: Data model tests
- `TestUtilityFunctions`: Helper function tests
- `TestIntegrationScenarios`: Complex workflow tests

### Mock Data

Tests use comprehensive mock objects that simulate:
- Solana RPC responses
- Token account data
- Program/user account detection
- Network errors and edge cases

## License

Business Source License 1.1 - see LICENSE file for details. 