# MCP Agent Deployment Guide

Deploy your MCP Agent to Google Vertex AI

## Prerequisites

Before starting, ensure you have:

- A Google Cloud Platform (GCP) account
- An active GCP project
- Billing enabled on your project
- Google Cloud SDK (gcloud) installed
- Python 3.11 or higher installed

### Downloads:
- Google Cloud SDK: https://cloud.google.com/sdk/docs/install
- Python: https://www.python.org/downloads/

## Step 1: Verify Required Permissions

Your Google account must have the following IAM roles:

- Agent Platform User

### Check Permissions

1. Open Google Cloud Console
2. Go to IAM & Admin → IAM
3. Find your email
4. Verify the required roles are assigned

If any role is missing, contact your GCP administrator.

## Step 2: Verify Installations

Run the following commands:

```bash
gcloud --version
python3 --version
git --version
```

If both return versions, continue else install the required dependencies.

## Step 3: Clone the Project Repository

Clone the project code from Git:

```bash
git clone https://github.com/precize/mcp-client.git
```

Navigate into the cloned directory:

```bash
cd mcp-client/vertex-ai-agent/
```

## Step 4: Create Virtual Environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```bash
python3 -m venv .venv
.venv\Scripts\activate
```

You should now see `(.venv)` in your terminal.

## Step 5: Install Google Application Development Kit (ADK)

```bash
python3 -m pip install google-adk
```

Verify installation:

```bash
adk --version
```

## Step 6: Configure Deployment Settings

Update the file with below details`.adk/config.yaml`:

```yaml
spec:
  projectId: your-gcp-project-id
  region: us-central1
  displayName: your-agent-display-name
  agent:
    model: your-vertexai-model
```

- **`projectId`** — your GCP project ID
- **`region`** — Vertex AI Agent Engine region to deploy the agent. Use `us-central1` unless you need a specific location.
- **`displayName`** — name shown in the Vertex AI console.
- **`model`** — your GCP Model ID

Supported Agent Engine regions:

```text
us-central1, us-east4, us-west1,
europe-west1, europe-west2, europe-west3, europe-west4, europe-west6, europe-west8, europe-southwest1,
asia-east1, asia-east2, asia-northeast1, asia-northeast3, asia-south1, asia-southeast1, asia-southeast2,
australia-southeast2, northamerica-northeast2, southamerica-east1
```


### Choosing a Model

Use a **Vertex AI Gemini model**. Here are the available options:

| Model | Best For |
|---|---|
| `gemini-2.5-pro` | Most capable, complex reasoning and long context |
| `gemini-2.0-flash` | Best balance of speed and capability (recommended) |
| `gemini-2.0-flash-lite` | Fastest and most cost-efficient, simple tasks |

> **Note:** All models must be available in your selected region. Check availability at [Vertex AI Model Garden](https://cloud.google.com/vertex-ai/generative-ai/docs/model-garden/available-models).

Save the file after updating.

## Step 7: Configure MCP Server

Edit: `agent/mcp-config.json`

Update with your MCP server details:

```json
{
  "servers": [
    {
      "name": "your-mcp-server",
      "url": "https://your-mcp-server-url",
      "auth_token": "your-auth-token",
      "enabled": true
    }
  ]
}
```

**Note:** Get `url` and `auth_token` from precize Dashboard

Save the file.

## Step 8: Configure Application Default Credentials

Run:

```bash
gcloud auth application-default login
```

Then set your project:

```bash
gcloud config set project your-gcp-project-id
```

## Step 9: Deploy the Agent

Run:

```bash
./deploy.sh
```

Deployment usually takes 3–5 minutes.

## Access Your Agent

After deployment:

1. Open Google Cloud Console
2. Go to Vertex AI → Agent → Deployments
3. Open your deployed agent
4. Click Open Playground
5. Start using with your MCP Agent
