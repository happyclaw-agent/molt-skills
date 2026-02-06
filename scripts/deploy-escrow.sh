#!/bin/bash
# Deploy Escrow Program to Solana Network
# Usage: ./scripts/deploy-escrow.sh [network]
# Network: localnet, devnet, mainnet-beta (default: devnet)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NETWORK="${1:-devnet}"

echo "🚀 Deploying Escrow Program to $NETWORK"
echo "========================================"

# Check if Anchor is installed
if ! command -v anchor &> /dev/null; then
    echo "❌ Anchor not found. Installing..."
    cargo install anchor-cli --locked
fi

# Navigate to program directory
cd "$PROJECT_DIR/programs/escrow"

# Build the program
echo "📦 Building escrow program..."
anchor build

# Get the program keypair path
PROGRAM_KEYPAIR="$PROJECT_DIR/target/deploy/escrow-keypair.json"

if [ ! -f "$PROGRAM_KEYPAIR" ]; then
    echo "⚠️  Program keypair not found. Creating new keypair..."
    solana-keygen new -o "$PROGRAM_KEYPAIR" --no-bip39-passphrase
fi

# Get the program ID
PROGRAM_ID=$(solana address -k "$PROGRAM_KEYPAIR")
echo "📍 Program ID: $PROGRAM_ID"

# Deploy based on network
case $NETWORK in
    localnet)
        echo "🌐 Deploying to localnet..."
        anchor deploy --provider.cluster localnet
        ;;
    devnet)
        echo "🌐 Deploying to devnet..."
        anchor deploy --provider.cluster devnet
        ;;
    mainnet-beta)
        echo "⚠️  Deploying to MAINNET - this will use real funds!"
        read -p "Continue? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            echo "Deployment cancelled."
            exit 0
        fi
        anchor deploy --provider.cluster mainnet-beta
        ;;
    *)
        echo "❌ Unknown network: $NETWORK"
        echo "Usage: $0 [localnet|devnet|mainnet-beta]"
        exit 1
        ;;
esac

# Save program ID to config
CONFIG_FILE="$PROJECT_DIR/.escrow-config"
echo "💾 Saving config to $CONFIG_FILE"
cat > "$CONFIG_FILE" << EOF
# Escrow Program Configuration
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Network: $NETWORK

PROGRAM_ID=$PROGRAM_ID
NETWORK=$NETWORK
USDC_MINT=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
EOF

# Export for current session
export ESCROW_PROGRAM_ID="$PROGRAM_ID"
export ESCROW_NETWORK="$NETWORK"

echo ""
echo "✅ Deployment complete!"
echo "====================="
echo "Program ID: $PROGRAM_ID"
echo "Network:    $NETWORK"
echo ""
echo "To use in your SDK, set environment variables:"
echo "  export ESCROW_PROGRAM_ID=\"$PROGRAM_ID\""
echo "  export ESCROW_NETWORK=\"$NETWORK\""
