"""
Chain configuration for multi-chain approval scanning
"""

CHAIN_CONFIG = {
    1: {
        "name": "Ethereum",
        "symbol": "ETH",
        "rpc": "https://eth.llamarpc.com",
        "explorer": "https://etherscan.io",
    },
    137: {
        "name": "Polygon",
        "symbol": "MATIC",
        "rpc": "https://polygon.llamarpc.com",
        "explorer": "https://polygonscan.com",
    },
    42161: {
        "name": "Arbitrum",
        "symbol": "ETH",
        "rpc": "https://arbitrum.llamarpc.com",
        "explorer": "https://arbiscan.io",
    },
    10: {
        "name": "Optimism",
        "symbol": "ETH",
        "rpc": "https://optimism.llamarpc.com",
        "explorer": "https://optimistic.etherscan.io",
    },
    8453: {
        "name": "Base",
        "symbol": "ETH",
        "rpc": "https://base.llamarpc.com",
        "explorer": "https://basescan.org",
    },
    56: {
        "name": "BNB Chain",
        "symbol": "BNB",
        "rpc": "https://binance.llamarpc.com",
        "explorer": "https://bscscan.com",
    },
    43114: {
        "name": "Avalanche",
        "symbol": "AVAX",
        "rpc": "https://avalanche.public-rpc.com",
        "explorer": "https://snowtrace.io",
    },
}

# ERC-20 Approval event signature
# event Approval(address indexed owner, address indexed spender, uint256 value)
ERC20_APPROVAL_TOPIC = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"

# ERC-721 ApprovalForAll event signature
# event ApprovalForAll(address indexed owner, address indexed operator, bool approved)
ERC721_APPROVALFORALL_TOPIC = "0x17307eab39ab6107e8899845ad3d59bd9653f200f220920489ca2b5937696c31"

# Threshold for unlimited approval (2^128)
UNLIMITED_APPROVAL_THRESHOLD = 2**128

# Stale approval threshold (90 days in seconds)
STALE_APPROVAL_DAYS = 90
STALE_APPROVAL_SECONDS = STALE_APPROVAL_DAYS * 24 * 60 * 60

# ERC-20 allowance function signature
ERC20_ALLOWANCE_FUNCTION = "0xdd62ed3e"  # allowance(address,address)
