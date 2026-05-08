#!/bin/bash

# Extract project and region from .adk/config.yaml
PROJECT=$(grep "projectId:" .adk/config.yaml | awk '{print $2}')
REGION=$(grep "region:" .adk/config.yaml | awk '{print $2}')

if [ -z "$PROJECT" ] || [ -z "$REGION" ]; then
    echo "Error: Could not find projectId or region in .adk/config.yaml"
    echo "Please edit .adk/config.yaml and set these values:"
    echo "  projectId: your-gcp-project-id"
    echo "  region: us-central1"
    exit 1
fi

echo "Deploying MCP Agent..."
echo "  Project: $PROJECT"
echo "  Region: $REGION"
echo ""

# Bundle config into agent package for deployment 
cp .adk/config.yaml agent/config.yaml

# Deploy
adk deploy agent_engine agent --project "$PROJECT" --region "$REGION"

# Clean up bundled config after deploy
rm -f agent/config.yaml
