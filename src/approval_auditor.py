"""
Core approval auditor logic for detecting and analyzing token approvals
"""
from web3 import Web3
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from src.chain_config import (
    CHAIN_CONFIG,
    ERC20_APPROVAL_TOPIC,
    ERC721_APPROVALFORALL_TOPIC,
    UNLIMITED_APPROVAL_THRESHOLD,
    STALE_APPROVAL_SECONDS,
)

logger = logging.getLogger(__name__)


class ApprovalAuditor:
    """Audits ERC-20 and ERC-721 approvals for a wallet"""

    def __init__(self):
        self.web3_connections = {}

    def get_web3(self, chain_id: int) -> Web3:
        """Get or create Web3 connection for a chain"""
        if chain_id not in self.web3_connections:
            if chain_id not in CHAIN_CONFIG:
                raise ValueError(f"Chain {chain_id} not supported")

            rpc_url = CHAIN_CONFIG[chain_id]["rpc"]
            self.web3_connections[chain_id] = Web3(Web3.HTTPProvider(rpc_url))

        return self.web3_connections[chain_id]

    def scan_approval_events(
        self, chain_id: int, wallet: str, from_block: int = 0, to_block: str = "latest"
    ) -> List[Dict]:
        """
        Scan for Approval and ApprovalForAll events for a wallet

        Args:
            chain_id: Blockchain chain ID
            wallet: Wallet address to audit
            from_block: Starting block number
            to_block: Ending block number or 'latest'

        Returns:
            List of approval events with metadata
        """
        try:
            w3 = self.get_web3(chain_id)
            wallet_address = Web3.to_checksum_address(wallet)

            # Get current block for timestamp calculations
            current_block = w3.eth.block_number

            # Limit scan to recent blocks to avoid timeouts (last 100k blocks)
            if from_block == 0:
                from_block = max(0, current_block - 100000)

            logger.info(
                f"Scanning approvals for {wallet_address} on chain {chain_id} "
                f"from block {from_block} to {to_block}"
            )

            # Scan for ERC-20 Approval events
            erc20_filter = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "topics": [
                    ERC20_APPROVAL_TOPIC,
                    Web3.to_hex(text=wallet_address.lower()).ljust(66, "0"),
                ],
            }

            erc20_events = []
            try:
                erc20_logs = w3.eth.get_logs(erc20_filter)
                for log in erc20_logs:
                    erc20_events.append(self._parse_erc20_approval(w3, log))
            except Exception as e:
                logger.warning(f"Error fetching ERC-20 approvals: {e}")

            # Scan for ERC-721 ApprovalForAll events
            erc721_filter = {
                "fromBlock": from_block,
                "toBlock": to_block,
                "topics": [
                    ERC721_APPROVALFORALL_TOPIC,
                    Web3.to_hex(text=wallet_address.lower()).ljust(66, "0"),
                ],
            }

            erc721_events = []
            try:
                erc721_logs = w3.eth.get_logs(erc721_filter)
                for log in erc721_logs:
                    erc721_events.append(self._parse_erc721_approval(w3, log))
            except Exception as e:
                logger.warning(f"Error fetching ERC-721 approvals: {e}")

            all_events = erc20_events + erc721_events
            logger.info(
                f"Found {len(erc20_events)} ERC-20 and {len(erc721_events)} ERC-721 approvals"
            )

            return all_events

        except Exception as e:
            logger.error(f"Error scanning approval events: {e}")
            return []

    def _parse_erc20_approval(self, w3: Web3, log) -> Dict:
        """Parse an ERC-20 Approval event"""
        token_address = log["address"]
        owner = "0x" + log["topics"][1].hex()[-40:]
        spender = "0x" + log["topics"][2].hex()[-40:]
        value = int(log["data"].hex(), 16)
        block_number = log["blockNumber"]
        tx_hash = log["transactionHash"].hex()

        # Get block timestamp
        try:
            block = w3.eth.get_block(block_number)
            timestamp = block["timestamp"]
        except Exception:
            timestamp = 0

        return {
            "type": "ERC20",
            "token_address": Web3.to_checksum_address(token_address),
            "owner": Web3.to_checksum_address(owner),
            "spender": Web3.to_checksum_address(spender),
            "value": str(value),
            "block_number": block_number,
            "timestamp": timestamp,
            "tx_hash": tx_hash,
        }

    def _parse_erc721_approval(self, w3: Web3, log) -> Dict:
        """Parse an ERC-721 ApprovalForAll event"""
        token_address = log["address"]
        owner = "0x" + log["topics"][1].hex()[-40:]
        operator = "0x" + log["topics"][2].hex()[-40:]
        approved = bool(int(log["data"].hex(), 16))
        block_number = log["blockNumber"]
        tx_hash = log["transactionHash"].hex()

        # Get block timestamp
        try:
            block = w3.eth.get_block(block_number)
            timestamp = block["timestamp"]
        except Exception:
            timestamp = 0

        return {
            "type": "ERC721",
            "token_address": Web3.to_checksum_address(token_address),
            "owner": Web3.to_checksum_address(owner),
            "operator": Web3.to_checksum_address(operator),
            "approved": approved,
            "block_number": block_number,
            "timestamp": timestamp,
            "tx_hash": tx_hash,
        }

    def get_current_allowance(
        self, chain_id: int, token_address: str, owner: str, spender: str
    ) -> Optional[int]:
        """
        Get current allowance for an ERC-20 token

        Args:
            chain_id: Chain ID
            token_address: Token contract address
            owner: Owner address
            spender: Spender address

        Returns:
            Current allowance as integer, or None if call fails
        """
        try:
            w3 = self.get_web3(chain_id)

            # Build allowance(address,address) call
            function_signature = Web3.keccak(text="allowance(address,address)")[:4]
            owner_padded = owner[2:].lower().rjust(64, "0")
            spender_padded = spender[2:].lower().rjust(64, "0")
            call_data = function_signature.hex() + owner_padded + spender_padded

            result = w3.eth.call(
                {
                    "to": Web3.to_checksum_address(token_address),
                    "data": call_data,
                }
            )

            allowance = int(result.hex(), 16)
            return allowance

        except Exception as e:
            logger.warning(
                f"Error getting allowance for {token_address} on chain {chain_id}: {e}"
            )
            return None

    def analyze_approval_risks(
        self, approvals: List[Dict], chain_id: int
    ) -> List[Dict]:
        """
        Analyze approvals for risk factors

        Args:
            approvals: List of approval events
            chain_id: Chain ID

        Returns:
            List of approvals with risk analysis
        """
        analyzed = []
        current_time = datetime.utcnow().timestamp()

        for approval in approvals:
            risk_flags = []

            # Skip revoked approvals (ERC-20 with value 0, ERC-721 with approved=False)
            if approval["type"] == "ERC20" and int(approval["value"]) == 0:
                continue
            if approval["type"] == "ERC721" and not approval.get("approved", True):
                continue

            # For ERC-20, get current allowance
            if approval["type"] == "ERC20":
                current_allowance = self.get_current_allowance(
                    chain_id,
                    approval["token_address"],
                    approval["owner"],
                    approval["spender"],
                )

                if current_allowance is not None:
                    approval["current_allowance"] = str(current_allowance)

                    # Skip if current allowance is 0 (already revoked)
                    if current_allowance == 0:
                        continue

                    # Check for unlimited approval
                    if current_allowance >= UNLIMITED_APPROVAL_THRESHOLD:
                        risk_flags.append("unlimited_approval")
                else:
                    approval["current_allowance"] = "unknown"

            # Check for stale approval (>90 days old)
            if approval["timestamp"] > 0:
                age_seconds = current_time - approval["timestamp"]
                if age_seconds > STALE_APPROVAL_SECONDS:
                    risk_flags.append("stale_approval")
                    approval["age_days"] = int(age_seconds / (24 * 60 * 60))

            approval["risk_flags"] = risk_flags
            analyzed.append(approval)

        return analyzed

    def build_revoke_transaction(
        self, approval: Dict, chain_id: int
    ) -> Optional[Dict]:
        """
        Build transaction data to revoke an approval

        Args:
            approval: Approval to revoke
            chain_id: Chain ID

        Returns:
            Transaction data dict or None
        """
        try:
            if approval["type"] == "ERC20":
                # approve(spender, 0)
                function_signature = Web3.keccak(text="approve(address,uint256)")[:4]
                spender_padded = approval["spender"][2:].lower().rjust(64, "0")
                amount_padded = "0".rjust(64, "0")
                data = function_signature.hex() + spender_padded + amount_padded

                return {
                    "to": approval["token_address"],
                    "from": approval["owner"],
                    "data": data,
                    "value": "0",
                    "chainId": chain_id,
                }

            elif approval["type"] == "ERC721":
                # setApprovalForAll(operator, false)
                function_signature = Web3.keccak(text="setApprovalForAll(address,bool)")[
                    :4
                ]
                operator_padded = approval["operator"][2:].lower().rjust(64, "0")
                approved_padded = "0".rjust(64, "0")  # false
                data = function_signature.hex() + operator_padded + approved_padded

                return {
                    "to": approval["token_address"],
                    "from": approval["owner"],
                    "data": data,
                    "value": "0",
                    "chainId": chain_id,
                }

        except Exception as e:
            logger.error(f"Error building revoke transaction: {e}")
            return None

    def audit_wallet(
        self, wallet: str, chains: List[int], from_block: int = 0
    ) -> Dict:
        """
        Complete audit of a wallet across multiple chains

        Args:
            wallet: Wallet address to audit
            chains: List of chain IDs to scan
            from_block: Starting block (0 for auto)

        Returns:
            Complete audit report with approvals, risks, and revoke data
        """
        all_approvals = []
        revoke_transactions = []

        for chain_id in chains:
            if chain_id not in CHAIN_CONFIG:
                logger.warning(f"Chain {chain_id} not supported, skipping")
                continue

            # Scan for approvals
            approvals = self.scan_approval_events(chain_id, wallet, from_block)

            # Analyze risks
            analyzed = self.analyze_approval_risks(approvals, chain_id)

            # Build revoke transactions for risky approvals
            for approval in analyzed:
                if approval.get("risk_flags"):
                    approval["chain_id"] = chain_id
                    approval["chain_name"] = CHAIN_CONFIG[chain_id]["name"]

                    revoke_tx = self.build_revoke_transaction(approval, chain_id)
                    if revoke_tx:
                        revoke_transactions.append(revoke_tx)

                    all_approvals.append(approval)

        return {
            "wallet": wallet,
            "chains_scanned": chains,
            "total_approvals": len(all_approvals),
            "approvals": all_approvals,
            "revoke_tx_data": revoke_transactions,
        }
