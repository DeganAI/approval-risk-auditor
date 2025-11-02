"""
Approval Risk Auditor - Flag unlimited or stale token approvals

x402 micropayment-enabled approval auditing service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
import logging

from src.approval_auditor import ApprovalAuditor
from src.chain_config import CHAIN_CONFIG
from src.x402_middleware_dual import X402Middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Approval Risk Auditor",
    description="Flag unlimited or stale ERC-20/NFT approvals and build revoke calls",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration
payment_address = os.getenv("PAYMENT_ADDRESS", "0x01D11F7e1a46AbFC6092d7be484895D2d505095c")
base_url = os.getenv("BASE_URL", "https://approval-risk-auditor-production.up.railway.app")
free_mode = os.getenv("FREE_MODE", "false").lower() == "true"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# x402 Payment Verification Middleware
app.add_middleware(
    X402Middleware,
    payment_address=payment_address,
    base_url=base_url,
    facilitator_urls=[
        "https://facilitator.daydreams.systems",
        "https://api.cdp.coinbase.com/platform/v2/x402/facilitator"
    ],
    free_mode=free_mode,
)

logger.info(f"Running in {'FREE' if free_mode else 'PAID'} mode")

# Initialize auditor
auditor = ApprovalAuditor()


# Request/Response Models
class AuditRequest(BaseModel):
    """Request for approval audit"""

    wallet: str = Field(
        ...,
        description="Wallet address to audit",
        example="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    )
    chains: List[int] = Field(
        ...,
        description="List of chain IDs to scan",
        example=[1, 137, 42161],
    )


class ApprovalInfo(BaseModel):
    """Information about a single approval"""

    type: str
    token_address: str
    owner: str
    spender: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    current_allowance: Optional[str] = None
    approved: Optional[bool] = None
    block_number: int
    timestamp: int
    tx_hash: str
    risk_flags: List[str]
    chain_id: int
    chain_name: str
    age_days: Optional[int] = None


class RevokeTransaction(BaseModel):
    """Transaction data to revoke an approval"""

    to: str
    from_field: str = Field(..., alias="from")
    data: str
    value: str
    chainId: int

    class Config:
        populate_by_name = True


class AuditResponse(BaseModel):
    """Response with audit results"""

    wallet: str
    chains_scanned: List[int]
    total_approvals: int
    approvals: List[Dict]
    revoke_tx_data: List[Dict]
    timestamp: str


# Landing Page
@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def root():
    """Landing page"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Approval Risk Auditor</title>
        <meta name="description" content="Flag unlimited or stale ERC-20/NFT approvals and build revoke calls via x402 micropayments">
        <meta property="og:title" content="Approval Risk Auditor">
        <meta property="og:description" content="Flag unlimited or stale ERC-20/NFT approvals and build revoke calls via x402 micropayments">
        <meta property="og:image" content="https://approval-risk-auditor-production.up.railway.app/favicon.ico">
        <link rel="icon" type="image/x-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔒</text></svg>">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
                color: #e2e8f0;
                line-height: 1.6;
                min-height: 100vh;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            header {{
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2));
                border: 2px solid rgba(239, 68, 68, 0.3);
                border-radius: 15px;
                padding: 40px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }}
            h1 {{
                color: #ef4444;
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .subtitle {{
                color: #fca5a5;
                font-size: 1.2em;
                margin-bottom: 15px;
            }}
            .badge {{
                display: inline-block;
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid #ef4444;
                color: #ef4444;
                padding: 6px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-right: 10px;
                margin-top: 10px;
            }}
            .section {{
                background: rgba(30, 41, 59, 0.6);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }}
            h2 {{
                color: #ef4444;
                margin-bottom: 20px;
                font-size: 1.8em;
                border-bottom: 2px solid rgba(239, 68, 68, 0.3);
                padding-bottom: 10px;
            }}
            .endpoint {{
                background: rgba(15, 23, 42, 0.6);
                border-left: 4px solid #ef4444;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }}
            .method {{
                display: inline-block;
                background: #ef4444;
                color: #0f172a;
                padding: 5px 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 0.85em;
                margin-right: 10px;
            }}
            code {{
                background: rgba(0, 0, 0, 0.3);
                color: #fca5a5;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Courier New', monospace;
            }}
            pre {{
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 6px;
                padding: 15px;
                overflow-x: auto;
                margin: 10px 0;
            }}
            pre code {{
                background: none;
                padding: 0;
                display: block;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .card {{
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 10px;
                padding: 20px;
                transition: transform 0.3s;
            }}
            .card:hover {{
                transform: translateY(-4px);
                border-color: rgba(239, 68, 68, 0.4);
            }}
            .card h4 {{
                color: #ef4444;
                margin-bottom: 10px;
            }}
            .warning {{
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
            }}
            .warning h3 {{
                color: #ef4444;
                margin-bottom: 10px;
            }}
            a {{
                color: #ef4444;
                text-decoration: none;
                border-bottom: 1px solid transparent;
                transition: border-color 0.3s;
            }}
            a:hover {{
                border-bottom-color: #ef4444;
            }}
            footer {{
                text-align: center;
                padding: 30px;
                color: #94a3b8;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Approval Risk Auditor</h1>
                <p class="subtitle">Flag Unlimited or Stale Token Approvals</p>
                <p>Detect risky ERC-20 and NFT approvals across 7 chains and generate revocation transactions</p>
                <div>
                    <span class="badge">Live & Ready</span>
                    <span class="badge">Multi-Chain</span>
                    <span class="badge">x402 Payments</span>
                    <span class="badge">ERC-20 & ERC-721</span>
                </div>
            </header>

            <div class="section">
                <h2>What is Approval Risk Auditor?</h2>
                <p>
                    Approval Risk Auditor scans your wallet for dangerous token approvals that could be exploited by malicious contracts.
                    It identifies unlimited approvals, stale approvals (>90 days old), and provides transaction data to revoke them safely.
                </p>

                <div class="warning">
                    <h3>Why Audit Your Approvals?</h3>
                    <p>
                        Token approvals grant contracts permission to spend your tokens. Unlimited approvals or approvals
                        to compromised contracts can drain your wallet. Regular audits help maintain security.
                    </p>
                </div>

                <div class="grid">
                    <div class="card">
                        <h4>Unlimited Approvals</h4>
                        <p>Detects approvals with values >= 2^128, which allow unlimited token transfers.</p>
                    </div>
                    <div class="card">
                        <h4>Stale Approvals</h4>
                        <p>Flags approvals older than 90 days that may no longer be needed.</p>
                    </div>
                    <div class="card">
                        <h4>Revoke Transactions</h4>
                        <p>Generates ready-to-broadcast transaction data to revoke risky approvals.</p>
                    </div>
                    <div class="card">
                        <h4>Multi-Chain Support</h4>
                        <p>Scans 7 major chains: Ethereum, Polygon, Arbitrum, Optimism, Base, BSC, Avalanche.</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>API Endpoints</h2>

                <div class="endpoint">
                    <h3><span class="method">POST</span>/approvals/audit</h3>
                    <p>Audit a wallet for risky token approvals across multiple chains</p>
                    <pre><code>curl -X POST https://approval-risk-auditor-production.up.railway.app/approvals/audit \\
  -H "Content-Type: application/json" \\
  -d '{{
    "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "chains": [1, 137, 42161]
  }}'</code></pre>
                </div>

                <div class="endpoint">
                    <h3><span class="method">GET</span>/chains</h3>
                    <p>List all supported blockchain networks</p>
                </div>

                <div class="endpoint">
                    <h3><span class="method">GET</span>/health</h3>
                    <p>Health check and operational status</p>
                </div>
            </div>

            <div class="section">
                <h2>Risk Flags</h2>
                <div class="grid">
                    <div class="card">
                        <h4>unlimited_approval</h4>
                        <p>Approval value >= 2^128, allowing unlimited token transfers</p>
                    </div>
                    <div class="card">
                        <h4>stale_approval</h4>
                        <p>Approval older than 90 days, may no longer be needed</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>x402 Micropayments</h2>
                <p>This service uses the <strong>x402 payment protocol</strong> for usage-based billing.</p>
                <div class="grid">
                    <div class="card">
                        <h4>Payment Details</h4>
                        <p><strong>Price:</strong> 0.05 USDC per request</p>
                        <p><strong>Address:</strong> <code>{payment_address}</code></p>
                        <p><strong>Network:</strong> Base</p>
                    </div>
                    <div class="card">
                        <h4>Status</h4>
                        <p><em>{"Currently in FREE MODE for testing" if free_mode else "Payment verification active"}</em></p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>Supported Networks</h2>
                <div class="grid">
                    <div class="card"><h4>Ethereum</h4><p>Chain ID: 1</p></div>
                    <div class="card"><h4>Polygon</h4><p>Chain ID: 137</p></div>
                    <div class="card"><h4>Arbitrum</h4><p>Chain ID: 42161</p></div>
                    <div class="card"><h4>Optimism</h4><p>Chain ID: 10</p></div>
                    <div class="card"><h4>Base</h4><p>Chain ID: 8453</p></div>
                    <div class="card"><h4>BNB Chain</h4><p>Chain ID: 56</p></div>
                    <div class="card"><h4>Avalanche</h4><p>Chain ID: 43114</p></div>
                </div>
            </div>

            <div class="section">
                <h2>Documentation</h2>
                <p>Interactive API documentation:</p>
                <div style="margin: 20px 0;">
                    <a href="/docs" style="display: inline-block; background: rgba(239, 68, 68, 0.2); padding: 10px 20px; border-radius: 5px; margin-right: 10px;">Swagger UI</a>
                    <a href="/redoc" style="display: inline-block; background: rgba(239, 68, 68, 0.2); padding: 10px 20px; border-radius: 5px;">ReDoc</a>
                </div>
            </div>

            <footer>
                <p><strong>Built by DeganAI</strong></p>
                <p>Bounty #5 Submission for Daydreams AI Agent Bounties</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# AP2 (Agent Payments Protocol) Metadata
@app.get("/.well-known/agent.json")
@app.head("/.well-known/agent.json")
async def agent_metadata():
    """AP2 metadata - returns HTTP 200"""
    base_url = os.getenv("BASE_URL", "https://approval-risk-auditor-production.up.railway.app")

    agent_json = {
        "name": "Approval Risk Auditor",
        "description": "Flag unlimited or stale ERC-20/NFT approvals and build revoke calls. Scans 7 chains to detect risky token approvals.",
        "url": base_url.replace("https://", "http://") + "/",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True,
            "extensions": [
                {
                    "uri": "https://github.com/google-agentic-commerce/ap2/tree/v0.1",
                    "description": "Agent Payments Protocol (AP2)",
                    "required": True,
                    "params": {"roles": ["merchant"]},
                }
            ],
        },
        "defaultInputModes": ["application/json"],
        "defaultOutputModes": ["application/json", "text/plain"],
        "skills": [
            {
                "id": "approval-risk-auditor",
                "name": "approval-risk-auditor",
                "description": "Audit wallet for risky token approvals and generate revocation transactions",
                "inputModes": ["application/json"],
                "outputModes": ["application/json"],
                "streaming": False,
                "x_input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "wallet": {
                            "description": "Wallet address to audit",
                            "type": "string",
                        },
                        "chains": {
                            "description": "List of chain IDs to scan",
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": ["wallet", "chains"],
                    "additionalProperties": False,
                },
                "x_output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "wallet": {"type": "string"},
                        "chains_scanned": {"type": "array"},
                        "total_approvals": {"type": "integer"},
                        "approvals": {"type": "array"},
                        "revoke_tx_data": {"type": "array"},
                    },
                    "required": ["wallet", "chains_scanned", "total_approvals", "approvals", "revoke_tx_data"],
                    "additionalProperties": False,
                },
            }
        ],
        "supportsAuthenticatedExtendedCard": False,
        "entrypoints": {
            "approval-risk-auditor": {
                "description": "Audit wallet for risky token approvals",
                "streaming": False,
                "input_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "wallet": {"description": "Wallet address", "type": "string"},
                        "chains": {"description": "Chain IDs", "type": "array", "items": {"type": "integer"}},
                    },
                    "required": ["wallet", "chains"],
                    "additionalProperties": False,
                },
                "output_schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "properties": {
                        "wallet": {"type": "string"},
                        "chains_scanned": {"type": "array"},
                        "total_approvals": {"type": "integer"},
                        "approvals": {"type": "array"},
                        "revoke_tx_data": {"type": "array"},
                    },
                    "additionalProperties": False,
                },
                "pricing": {"invoke": "0.05 USDC"},
            }
        },
        "payments": [
            {
                "method": "x402",
                "payee": payment_address,
                "network": "base",
                "endpoint": "https://facilitator.daydreams.systems",
                "priceModel": {"default": "0.05"},
                "extensions": {
                    "x402": {"facilitatorUrl": "https://facilitator.daydreams.systems"}
                },
            }
        ],
    }

    return JSONResponse(content=agent_json, status_code=200)


# x402 Protocol Metadata
@app.get("/.well-known/x402")
@app.head("/.well-known/x402")
async def x402_metadata():
    """x402 protocol metadata - returns HTTP 402"""
    base_url = os.getenv("BASE_URL", "https://approval-risk-auditor-production.up.railway.app")

    metadata = {
        "x402Version": 1,
        "accepts": [
            {
                "scheme": "exact",
                "network": "base",
                "maxAmountRequired": "50000",
                "resource": f"{base_url}/entrypoints/approval-risk-auditor/invoke",
                "description": "Audit wallet for risky ERC-20/NFT approvals and generate revocation transactions",
                "mimeType": "application/json",
                "payTo": payment_address,
                "maxTimeoutSeconds": 30,
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            }
        ],
    }

    return JSONResponse(content=metadata, status_code=402)


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint"""
    from fastapi.responses import Response
    svg_content = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🔒</text></svg>'
    return Response(content=svg_content, media_type="image/svg+xml")


# Health Check
@app.get("/health")
async def health():
    """Health check"""
    supported_chains = list(CHAIN_CONFIG.keys())
    return {
        "status": "healthy",
        "supported_chains": len(supported_chains),
        "chain_ids": supported_chains,
        "free_mode": free_mode,
    }


# List Chains
@app.get("/chains")
async def list_chains():
    """List all supported chains"""
    chains = []

    for chain_id, config in CHAIN_CONFIG.items():
        chains.append({
            "chain_id": chain_id,
            "name": config["name"],
            "symbol": config["symbol"],
        })

    return {"chains": chains, "total": len(chains)}


# Main Audit Endpoint
@app.post("/approvals/audit", response_model=AuditResponse)
async def audit_approvals(request: AuditRequest):
    """
    Audit a wallet for risky token approvals

    Scans for:
    - ERC-20 Approval events
    - ERC-721 ApprovalForAll events
    - Current allowances
    - Unlimited approvals (>= 2^128)
    - Stale approvals (>90 days old)

    Returns:
    - List of all risky approvals
    - Risk flags for each approval
    - Transaction data to revoke approvals
    """
    try:
        logger.info(
            f"Audit request: wallet={request.wallet}, chains={request.chains}"
        )

        # Validate chains
        for chain_id in request.chains:
            if chain_id not in CHAIN_CONFIG:
                raise HTTPException(
                    status_code=400,
                    detail=f"Chain {chain_id} not supported. Supported: {list(CHAIN_CONFIG.keys())}",
                )

        # Perform audit
        result = auditor.audit_wallet(
            wallet=request.wallet,
            chains=request.chains,
            from_block=0,
        )

        if not result:
            raise HTTPException(
                status_code=503,
                detail="Failed to audit wallet. RPC may be unavailable.",
            )

        return AuditResponse(
            wallet=result["wallet"],
            chains_scanned=result["chains_scanned"],
            total_approvals=result["total_approvals"],
            approvals=result["approvals"],
            revoke_tx_data=result["revoke_tx_data"],
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


# AP2 Entrypoint - GET/HEAD for x402 discovery
@app.get("/entrypoints/approval-risk-auditor/invoke")
@app.head("/entrypoints/approval-risk-auditor/invoke")
async def entrypoint_audit_get():
    """
    x402 discovery endpoint - returns HTTP 402 for x402scan registration
    """
    base_url = os.getenv("BASE_URL", "https://approval-risk-auditor-production.up.railway.app")

    return JSONResponse(
        status_code=402,
        content={
            "x402Version": 1,
            "accepts": [{
                "scheme": "exact",
                "network": "base",
                "maxAmountRequired": "50000",  # 0.05 USDC (6 decimals)
                "resource": f"{base_url}/entrypoints/approval-risk-auditor/invoke",
                "description": "Approval Risk Auditor - Flag unlimited or stale token approvals",
                "mimeType": "application/json",
                "payTo": payment_address,
                "maxTimeoutSeconds": 30,
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
                "outputSchema": {
                    "input": {
                        "type": "http",
                        "method": "POST",
                        "bodyType": "json",
                        "bodyFields": {
                            "wallet": {
                                "type": "string",
                                "required": True,
                                "description": "Wallet address to audit"
                            },
                            "chains": {
                                "type": "array",
                                "required": True,
                                "description": "List of chain IDs to scan (e.g., [1, 137, 42161])"
                            }
                        }
                    },
                    "output": {
                        "type": "object",
                        "description": "Approval risk audit results with flagged tokens and revoke transactions"
                    }
                }
            }]
        }
    )


# AP2 Entrypoint - POST for actual requests
@app.post(
    "/entrypoints/approval-risk-auditor/invoke",
    summary="Token Approval Risk Auditor",
    description="Scan wallet for risky ERC-20/NFT approvals and generate revoke transactions. Identifies unlimited approvals, stale permissions, and suspicious spenders across 7+ chains with ready-to-broadcast revocation calls.",
    response_description="Approval risks with revoke transaction data"
)
async def entrypoint_audit_post(request: Optional[AuditRequest] = None, x_payment_txhash: Optional[str] = None):
    """
    AP2 (Agent Payments Protocol) compatible entrypoint

    Returns 402 if no payment provided (FREE_MODE overrides this for testing).
    Calls the main /approvals/audit endpoint with the same logic if payment is valid.
    """
    # Return 402 if no request body provided
    if request is None:
        return await entrypoint_audit_get()

    # In FREE_MODE, bypass payment check
    if not free_mode and not x_payment_txhash:
        return await entrypoint_audit_get()

    return await audit_approvals(request)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
