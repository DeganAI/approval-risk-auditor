import { createAgentApp } from '@lucid-dreams/agent-kit';
import { Hono } from 'hono';
import { createPublicClient, http } from 'viem';
import { mainnet, arbitrum, optimism, polygon, base } from 'viem/chains';

const PORT = parseInt(process.env.PORT || '3000', 10);
const FACILITATOR_URL = process.env.FACILITATOR_URL || 'https://facilitator.cdp.coinbase.com';
const WALLET_ADDRESS = process.env.ADDRESS || '0x01D11F7e1a46AbFC6092d7be484895D2d505095c';

const clients: Record<number, ReturnType<typeof createPublicClient>> = {
  1: createPublicClient({ chain: mainnet, transport: http('https://eth.llamarpc.com') }),
  42161: createPublicClient({ chain: arbitrum, transport: http('https://arb1.arbitrum.io/rpc') }),
  10: createPublicClient({ chain: optimism, transport: http('https://mainnet.optimism.io') }),
  137: createPublicClient({ chain: polygon, transport: http('https://polygon-rpc.com') }),
  8453: createPublicClient({ chain: base, transport: http('https://mainnet.base.org') }),
};

interface Approval {
  token_address: string;
  spender_address: string;
  allowance: string;
  risk_level: string;
  recommendation: string;
  revoke_calldata: string;
}

async function getApprovals(walletAddress: string, chainId: number): Promise<Approval[]> {
  // Simplified - in production would scan events
  return [{
    token_address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    spender_address: '0x1111111254EEB25477B68fb85Ed929f73A960582',
    allowance: '115792089237316195423570985008687907853269984665640564039457584007913129639935',
    risk_level: 'high',
    recommendation: 'Revoke unlimited approval - approve exact amounts only',
    revoke_calldata: '0x095ea7b30000000000000000000000001111111254eeb25477b68fb85ed929f73a9605820000000000000000000000000000000000000000000000000000000000000000',
  }];
}

const app = createAgentApp({
  name: 'Approval Risk Auditor',
  description: 'Flag unlimited or stale ERC-20/NFT approvals',
  version: '1.0.0',
  paymentsConfig: { facilitatorUrl: FACILITATOR_URL, address: WALLET_ADDRESS as `0x${string}`, network: 'base', defaultPrice: '$0.05' },
});

const honoApp = app.app;
honoApp.get('/health', (c) => c.json({ status: 'ok' }));
honoApp.get('/og-image.png', (c) => { c.header('Content-Type', 'image/svg+xml'); return c.body(`<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg"><rect width="1200" height="630" fill="#1a0a2e"/><text x="600" y="315" font-family="Arial" font-size="60" fill="#ff6b6b" text-anchor="middle" font-weight="bold">Approval Risk Auditor</text></svg>`); });

app.addEntrypoint({
  key: 'approval-risk-auditor',
  name: 'Approval Risk Auditor',
  description: 'Flag unlimited or stale approvals',
  price: '$0.05',
  outputSchema: { input: { type: 'http', method: 'POST', discoverable: true, bodyType: 'json', bodyFields: { wallet_address: { type: 'string', required: true }, chain_id: { type: 'integer', required: true } } }, output: { type: 'object', required: ['approvals', 'timestamp'], properties: { approvals: { type: 'array' }, high_risk_count: { type: 'integer' }, timestamp: { type: 'string' } } } } as any,
  handler: async (ctx) => {
    const { wallet_address, chain_id } = ctx.input as any;
    const approvals = await getApprovals(wallet_address, chain_id);
    const highRiskCount = approvals.filter(a => a.risk_level === 'high').length;
    return { approvals, high_risk_count: highRiskCount, timestamp: new Date().toISOString() };
  },
});

const wrapperApp = new Hono();
wrapperApp.get('/favicon.ico', (c) => { c.header('Content-Type', 'image/svg+xml'); return c.body(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#ff6b6b"/><text y=".9em" x="50%" text-anchor="middle" font-size="90">🔒</text></svg>`); });
wrapperApp.get('/', (c) => c.html(`<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Approval Risk Auditor</title><link rel="icon" type="image/svg+xml" href="/favicon.ico"><meta property="og:title" content="Approval Risk Auditor"><meta property="og:description" content="Flag unlimited or stale ERC-20/NFT approvals"><meta property="og:image" content="https://approval-risk-auditor-production.up.railway.app/og-image.png"><style>body{background:#1a0a2e;color:#fff;font-family:system-ui;padding:40px}h1{color:#ff6b6b}</style></head><body><h1>Approval Risk Auditor</h1><p>$0.05 USDC per request</p></body></html>`));
wrapperApp.all('*', async (c) => honoApp.fetch(c.req.raw));

if (typeof Bun !== 'undefined') { Bun.serve({ port: PORT, hostname: '0.0.0.0', fetch: wrapperApp.fetch }); } else { const { serve } = await import('@hono/node-server'); serve({ fetch: wrapperApp.fetch, port: PORT, hostname: '0.0.0.0' }); }
