# Approval Risk Auditor

**Bounty #5 - Flag unlimited or stale ERC-20/NFT approvals and build revoke calls**

## Overview

Approval Risk Auditor is a security-focused API service that scans wallets for dangerous token approvals across 7 major blockchain networks. It identifies unlimited approvals, stale approvals (>90 days old), and provides ready-to-broadcast transaction data to revoke them.

### Key Features

- **Multi-Chain Support**: Scans Ethereum, Polygon, Arbitrum, Optimism, Base, BNB Chain, and Avalanche
- **ERC-20 & ERC-721**: Detects both fungible token approvals and NFT approvals
- **Risk Analysis**: Identifies unlimited approvals (>= 2^128) and stale approvals (>90 days)
- **Revocation Data**: Generates transaction data to safely revoke risky approvals
- **x402 Payments**: Integrated micropayment protocol for usage-based billing
- **AP2 Compatible**: Full Agent Payments Protocol (AP2) implementation

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/DeganAI/approval-risk-auditor.git
cd approval-risk-auditor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export PORT=8000
export FREE_MODE=true
export PAYMENT_ADDRESS=0x01D11F7e1a46AbFC6092d7be484895D2d505095c
export BASE_URL=http://localhost:8000
```

4. Run the server:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

5. Visit http://localhost:8000 to see the landing page

### Docker

```bash
docker build -t approval-risk-auditor .
docker run -p 8000:8000 \
  -e FREE_MODE=true \
  -e PAYMENT_ADDRESS=0x01D11F7e1a46AbFC6092d7be484895D2d505095c \
  approval-risk-auditor
```

## API Usage

### Audit Wallet Approvals

**Endpoint**: `POST /approvals/audit`

**Request**:
```json
{
  "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "chains": [1, 137, 42161]
}
```

**Response**:
```json
{
  "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "chains_scanned": [1, 137, 42161],
  "total_approvals": 5,
  "approvals": [
    {
      "type": "ERC20",
      "token_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "owner": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "spender": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
      "value": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
      "current_allowance": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
      "block_number": 15000000,
      "timestamp": 1654000000,
      "tx_hash": "0x...",
      "risk_flags": ["unlimited_approval", "stale_approval"],
      "chain_id": 1,
      "chain_name": "Ethereum",
      "age_days": 120
    }
  ],
  "revoke_tx_data": [
    {
      "to": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "data": "0x095ea7b3000000000000000000000000068b3465833fb72a70ecdf485e0e4c7bd8665fc450000000000000000000000000000000000000000000000000000000000000000",
      "value": "0",
      "chainId": 1
    }
  ],
  "timestamp": "2025-10-31T12:00:00Z"
}
```

### List Supported Chains

**Endpoint**: `GET /chains`

**Response**:
```json
{
  "chains": [
    {"chain_id": 1, "name": "Ethereum", "symbol": "ETH"},
    {"chain_id": 137, "name": "Polygon", "symbol": "MATIC"},
    {"chain_id": 42161, "name": "Arbitrum", "symbol": "ETH"},
    {"chain_id": 10, "name": "Optimism", "symbol": "ETH"},
    {"chain_id": 8453, "name": "Base", "symbol": "ETH"},
    {"chain_id": 56, "name": "BNB Chain", "symbol": "BNB"},
    {"chain_id": 43114, "name": "Avalanche", "symbol": "AVAX"}
  ],
  "total": 7
}
```

### Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "supported_chains": 7,
  "chain_ids": [1, 137, 42161, 10, 8453, 56, 43114],
  "free_mode": true
}
```

## Risk Flags

- **unlimited_approval**: Approval value >= 2^128, allowing unlimited token transfers
- **stale_approval**: Approval older than 90 days that may no longer be needed

## x402 Payment Protocol

This service implements the x402 micropayment protocol for usage-based billing.

**Payment Details**:
- Price: 0.05 USDC per request
- Network: Base
- Token: USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
- Payment Address: 0x01D11F7e1a46AbFC6092d7be484895D2d505095c
- Facilitator: https://facilitator.daydreams.systems

**Endpoints**:
- `/.well-known/agent.json` - AP2 metadata (HTTP 200)
- `/.well-known/x402` - x402 metadata (HTTP 402)
- `/entrypoints/approval-risk-auditor/invoke` - AP2 entrypoint (HTTP 402 without payment)

## Architecture

```
approval-risk-auditor/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with AP2/x402 endpoints
│   ├── approval_auditor.py  # Core approval scanning logic
│   └── chain_config.py      # Multi-chain RPC configuration
├── requirements.txt
├── Dockerfile
├── railway.toml
├── README.md
├── PRODUCTION_SETUP.md
└── test_endpoints.sh
```

## Testing

Run the test script to verify all endpoints:

```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

## Deployment

See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) for detailed Railway deployment instructions.

## Technical Details

### Approval Detection

1. **ERC-20 Approvals**: Scans for `Approval(address indexed owner, address indexed spender, uint256 value)` events
2. **ERC-721 Approvals**: Scans for `ApprovalForAll(address indexed owner, address indexed operator, bool approved)` events
3. **Current Allowance**: Queries `allowance(owner, spender)` to get current approval values
4. **Risk Analysis**: Checks for unlimited approvals (>= 2^128) and stale approvals (>90 days old)

### Revocation

- **ERC-20**: Calls `approve(spender, 0)` to revoke
- **ERC-721**: Calls `setApprovalForAll(operator, false)` to revoke

## Acceptance Criteria

- ✅ Matches Etherscan approval data for top tokens
- ✅ Identifies unlimited and stale approvals
- ✅ Provides valid revocation transaction data
- ✅ Deployed on Railway with x402 payment integration
- ✅ Registered on x402scan

## Built With

- **FastAPI** - Web framework
- **Web3.py** - Ethereum interaction
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server
- **Gunicorn** - Production server

## Author

**DeganAI** (Ian B - hashmonkey@degenai.us)

Bounty #5 submission for Daydreams AI Agent Bounties

## License

MIT License
