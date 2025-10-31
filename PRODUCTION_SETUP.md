# Production Setup Guide - Approval Risk Auditor

This guide walks through deploying Approval Risk Auditor to Railway and registering it on x402scan.

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app)
- Base wallet with USDC for testing (optional)

## Step 1: GitHub Repository Setup

1. Create a new GitHub repository:
   - Go to https://github.com/new
   - Repository name: `approval-risk-auditor`
   - Description: "Flag unlimited or stale ERC-20/NFT approvals and build revoke calls"
   - Visibility: Public
   - Initialize: No (we'll push existing code)

2. Push your local code:
```bash
cd /path/to/approval-risk-auditor
git remote add origin https://github.com/DeganAI/approval-risk-auditor.git
git branch -M main
git push -u origin main
```

## Step 2: Railway Deployment

1. **Create New Project**:
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `approval-risk-auditor` repository
   - Click "Deploy Now"

2. **Configure Environment Variables**:

   Navigate to your project → Variables tab and add:

   ```
   PORT=8000
   FREE_MODE=false
   PAYMENT_ADDRESS=0x01D11F7e1a46AbFC6092d7be484895D2d505095c
   BASE_URL=https://approval-risk-auditor-production.up.railway.app
   ```

   **Important Notes**:
   - Set `FREE_MODE=false` for production (requires x402 payments)
   - Set `FREE_MODE=true` for testing (bypasses payment verification)
   - `BASE_URL` should match your Railway domain

3. **Configure Build Settings**:

   Railway should auto-detect the `railway.toml` configuration:
   - Builder: DOCKERFILE
   - Start Command: gunicorn with uvicorn workers
   - Health Check: `/health`
   - Timeout: 30 seconds

4. **Generate Domain**:
   - Go to Settings → Networking
   - Click "Generate Domain"
   - Note your domain (e.g., `approval-risk-auditor-production.up.railway.app`)
   - Update `BASE_URL` environment variable with this domain

5. **Trigger Deployment**:
   - Railway will automatically deploy on push to main
   - Wait 2-3 minutes for build and deployment
   - Check logs for any errors

## Step 3: Verify Deployment

Test all critical endpoints:

### 1. Landing Page (HTTP 200)
```bash
curl -I https://approval-risk-auditor-production.up.railway.app/
# Should return: HTTP/2 200
```

### 2. Health Check (HTTP 200)
```bash
curl https://approval-risk-auditor-production.up.railway.app/health
# Should return: {"status": "healthy", ...}
```

### 3. AP2 Metadata (HTTP 200)
```bash
curl -I https://approval-risk-auditor-production.up.railway.app/.well-known/agent.json
# Should return: HTTP/2 200
```

### 4. x402 Metadata (HTTP 402)
```bash
curl -I https://approval-risk-auditor-production.up.railway.app/.well-known/x402
# Should return: HTTP/2 402
```

### 5. AP2 Entrypoint (HTTP 402)
```bash
curl -I https://approval-risk-auditor-production.up.railway.app/entrypoints/approval-risk-auditor/invoke
# Should return: HTTP/2 402
```

### 6. Validate x402 Response
```bash
curl -s https://approval-risk-auditor-production.up.railway.app/.well-known/x402 | jq
```

**Expected output**:
```json
{
  "x402Version": 1,
  "accepts": [
    {
      "scheme": "exact",
      "network": "base",
      "maxAmountRequired": "50000",
      "resource": "https://approval-risk-auditor-production.up.railway.app/entrypoints/approval-risk-auditor/invoke",
      "description": "Audit wallet for risky ERC-20/NFT approvals and generate revocation transactions",
      "mimeType": "application/json",
      "payTo": "0x01D11F7e1a46AbFC6092d7be484895D2d505095c",
      "maxTimeoutSeconds": 30,
      "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    }
  ]
}
```

**Critical Validation**:
- ✅ All fields present: `scheme`, `network`, `maxAmountRequired`, `resource`, `description`, `mimeType`, `payTo`, `maxTimeoutSeconds`, `asset`
- ✅ `network` is `base`
- ✅ `asset` is Base USDC: `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- ✅ `payTo` is payment address: `0x01D11F7e1a46AbFC6092d7be484895D2d505095c`

## Step 4: Register on x402scan

1. **Navigate to Registration**:
   - Go to https://www.x402scan.com/resources/register

2. **Enter Entrypoint URL**:
   ```
   https://approval-risk-auditor-production.up.railway.app/entrypoints/approval-risk-auditor/invoke
   ```

3. **Leave Headers Blank**:
   - No custom headers needed

4. **Click "Add"**:
   - Should see "Resource Added" confirmation
   - Your service will appear on https://www.x402scan.com

5. **Verify Registration**:
   - Search for "Approval Risk Auditor" on x402scan
   - Verify all metadata is correct

## Step 5: Test with Payment (Optional)

If you want to test with actual x402 payments:

1. **Get Base USDC**:
   - Bridge ETH to Base
   - Swap for USDC on a Base DEX

2. **Use x402 Client**:
   ```bash
   # Example with x402 payment headers
   curl -X POST https://approval-risk-auditor-production.up.railway.app/entrypoints/approval-risk-auditor/invoke \
     -H "Content-Type: application/json" \
     -H "X-Payment-TxHash: 0x..." \
     -d '{
       "wallet": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
       "chains": [1, 137, 42161]
     }'
   ```

## Step 6: Monitoring and Maintenance

### View Logs
```bash
# In Railway dashboard
Project → Deployments → View Logs
```

### Monitor Health
```bash
# Set up health check monitoring
curl https://approval-risk-auditor-production.up.railway.app/health
```

### Update Deployment
```bash
# Any push to main triggers auto-deploy
git add .
git commit -m "Update"
git push origin main
```

## Environment Variables Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `PORT` | `8000` | Server port (Railway provides this) |
| `FREE_MODE` | `false` | Enable payment verification (`true` for testing) |
| `PAYMENT_ADDRESS` | `0x01D11F7e1a46AbFC6092d7be484895D2d505095c` | Base wallet for x402 payments |
| `BASE_URL` | `https://approval-risk-auditor-production.up.railway.app` | Your Railway domain |

## Troubleshooting

### 502 Bad Gateway
- Check Railway logs for startup errors
- Verify `railway.toml` configuration
- Ensure health check endpoint is responding

### 402 Not Returned
- Verify `FREE_MODE` is set correctly
- Check x402 metadata endpoint response
- Validate all required fields in x402 response

### RPC Timeouts
- RPC endpoints may rate limit or timeout
- Consider implementing retry logic
- Use fallback RPC providers if needed

### x402scan Registration Failed
- Ensure entrypoint returns HTTP 402 on GET/HEAD
- Validate all required fields in x402 response
- Check that URL is publicly accessible

## Security Notes

1. **Payment Address**: Keep private keys for `PAYMENT_ADDRESS` secure
2. **RPC Endpoints**: Monitor for rate limiting and abuse
3. **Input Validation**: All inputs are validated via Pydantic models
4. **Error Handling**: Sensitive error details are not exposed to clients

## Support

For issues or questions:
- GitHub Issues: https://github.com/DeganAI/approval-risk-auditor/issues
- Email: hashmonkey@degenai.us
- Daydreams Discord: https://discord.gg/daydreams

## Next Steps

After successful deployment:

1. ✅ Verify all endpoints return correct status codes
2. ✅ Test approval audit functionality
3. ✅ Register on x402scan
4. ✅ Submit bounty PR to https://github.com/daydreamsai/agent-bounties
5. ✅ Monitor for production issues

## Bounty Submission

Create `submissions/approval-risk-auditor.md` in the agent-bounties repo:

```markdown
# Approval Risk Auditor - Bounty #5 Submission

## Agent Information
**Name:** Approval Risk Auditor
**Description:** Flag unlimited or stale ERC-20/NFT approvals and build revoke calls
**Live Endpoint:** https://approval-risk-auditor-production.up.railway.app/entrypoints/approval-risk-auditor/invoke

## Acceptance Criteria
- ✅ Matches Etherscan approval data for top tokens
- ✅ Identifies unlimited and stale approvals
- ✅ Provides valid revocation transaction data
- ✅ Deployed on Railway and reachable via x402

## Implementation Details
- Technology: Python, FastAPI, Web3.py
- Deployment: Railway
- Payment: x402 via daydreams facilitator
- Network: Base
- Pricing: 0.05 USDC per request

## Testing
Service is live and registered on x402scan:
https://www.x402scan.com

## Repository
https://github.com/DeganAI/approval-risk-auditor

## Wallet Information
**Payment Address (ETH/Base):** 0x01D11F7e1a46AbFC6092d7be484895D2d505095c
**Solana Wallet:** Hnf7qnwdHYtSqj7PjjLjokUq4qaHR4qtHLedW7XDaNDG
```

Submit as PR to: https://github.com/daydreamsai/agent-bounties
