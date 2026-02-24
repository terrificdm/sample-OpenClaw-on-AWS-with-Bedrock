# OpenClaw on AWS with Bedrock AgentCore — Multi-Tenant Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Status](https://img.shields.io/badge/Status-In%20Development%20%26%20Testing-yellow.svg)]()

> ⚠️ **Work in Progress** — This project is currently under active development and testing. Core infrastructure and Agent Container are functional; the Gateway routing integration and Authorization Agent channel delivery are not yet wired up end-to-end. Contributions and feedback welcome.

## TL;DR

OpenClaw is a single-user AI assistant. We turned it into a multi-user platform on AWS.

Here's how it works:

1. **Each user gets their own isolated runtime.** When a message arrives, the EC2 Gateway identifies the user (`tenant_id`), then calls AWS AgentCore Runtime with `sessionId = tenant_id`. AWS spins up a separate microVM for each user — they can't touch each other's data or processes.

2. **openclaw runs as a subprocess inside a Docker container.** Python is the entry point. Before forwarding the message to openclaw, Python injects the user's permission profile into the system prompt — telling the LLM which tools it's allowed to use. After openclaw responds, Python scans the response for any unauthorized tool usage and logs violations to CloudWatch.

3. **Sensitive operations go through a human.** A dedicated Authorization Agent (another AgentCore session) receives permission requests, formats them as natural-language notifications, and sends them to an admin via WhatsApp or Telegram. The admin replies to approve or reject. Unanswered requests auto-reject after 30 minutes.

4. **Infrastructure is one CloudFormation stack.** EC2 Gateway + ECR + SSM (permission profiles) + CloudWatch. AgentCore Runtime is created separately after pushing the Docker image.

---

## What This Project Does

OpenClaw is an open-source personal AI assistant that connects to WhatsApp, Telegram, Discord, and more. It runs as a single-user Node.js process.

This project wraps openclaw in a multi-tenant serverless platform — **without modifying openclaw itself**.

### What openclaw provides (unchanged)

- Messaging channel integrations: WhatsApp, Telegram, Discord, Slack
- Tool execution: web_search, shell, browser, file, code_execution
- Per-session memory: Markdown + SQLite in `/tmp/openclaw/sessions/`
- Heartbeat and cron via built-in `CronService`
- OpenAI-compatible HTTP API: `POST /v1/chat/completions`

### What this project adds

| Capability | openclaw alone | This project |
|---|---|---|
| Users | Single user | Multiple tenants, fully isolated |
| Execution | Local process | Serverless microVM per tenant (AgentCore Runtime) |
| Tool permissions | None | Per-tenant SSM profiles injected into system prompt |
| Response audit | None | Post-execution scan for unauthorized tool usage |
| Memory poisoning defense | None | Injection pattern detection before writing to memory |
| Input validation | None | Message truncation, tool name and path validation |
| Cross-container memory | Lost on restart | Optional cloud persistence via AgentCore Memory |
| Observability | Local logs | Structured CloudWatch JSON logs per tenant |
| Infrastructure | Manual | CloudFormation (EC2 + ECR + SSM + CloudWatch) |

---

## Architecture

```
YOUR USERS
  │  WhatsApp / Telegram / Discord
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  EC2 INSTANCE  (always-on, ~$35/month)                          │
│                                                                  │
│  openclaw Gateway process  (Node.js, port 18789)                │
│  • Receives messages from WhatsApp / Telegram / Discord         │
│  • Provides web UI for configuration                            │
│                                                                  │
│  gateway/tenant_router.py  (integration layer — see note)       │
│  • derive_tenant_id(channel, user_id)                           │
│  • get_permission_profile(tenant_id)  ← reads SSM              │
│  • invoke_agent_runtime(sessionId=tenant_id, payload)           │
└──────────────────────────────┬──────────────────────────────────┘
                               │  invokeAgentRuntime API call
                               │  sessionId = tenant_id
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENTCORE RUNTIME  (serverless, pay-per-use)                   │
│  Each tenant gets an isolated microVM                           │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  AGENT CONTAINER  (Docker image in ECR)                   │  │
│  │                                                           │  │
│  │  server.py  (Python HTTP wrapper, port 8080)              │  │
│  │  1. validate_message()  ← safety.py                      │  │
│  │  2. _build_system_prompt(tenant_id)                       │  │
│  │     → reads SSM permission profile                        │  │
│  │     → injects "Allowed tools: [...]" into system prompt   │  │
│  │  3. POST /v1/chat/completions → openclaw subprocess       │  │
│  │     user = "agentcore:{tenant_id}"  ← SessionKey          │  │
│  │  4. _audit_response()  ← scans response for blocked tools │  │
│  │     → logs violations to CloudWatch                       │  │
│  │                                                           │  │
│  │  openclaw subprocess  (Node.js, port 18789)               │  │
│  │  • Executes tools, manages session memory                 │  │
│  │  • Session files: /tmp/openclaw/sessions/                 │  │
│  │    agentcore:{tenant_id}/memory/memory.md                 │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │  PermissionRequest (when audit detects violation)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  AUTHORIZATION AGENT  (separate AgentCore Runtime session)      │
│  session_id = "auth-agent-{stack_name}"                         │
│                                                                  │
│  auth-agent/server.py  → handler.py → approval_executor.py     │
│  • Formats risk-assessed approval notification                  │
│  • Sends to Human Approver via WhatsApp/Telegram (logged)       │
│  • 30-minute auto-reject timer                                  │
│  • /pending approvals command                                   │
│  • Reads system prompt from SSM on every request (hot-reload)  │
│  • approve_temporary → issues ApprovalToken (max 24h)          │
│  • approve_persistent → updates SSM permission profile         │
└─────────────────────────────────────────────────────────────────┘

AWS SUPPORTING SERVICES
  SSM Parameter Store
    /openclaw/{stack}/tenants/{tenant_id}/permissions  ← per-tenant tool allowlist
    /openclaw/{stack}/auth-agent/system-prompt         ← hot-reloadable
    /openclaw/{stack}/gateway-token                    ← Gateway auth token

  CloudWatch Logs  /openclaw/{stack}/agents
    log_stream = tenant_{tenant_id}  (one stream per tenant)
    event_type: agent_invocation | permission_denied | approval_decision

  ECR Repository  {stack}-multitenancy-agent
```

### Permission enforcement approach

openclaw is a black box — Python cannot intercept its internal tool calls. Two complementary mechanisms are used:

- **Plan A (soft enforcement)**: The tenant's allowed tools list is injected into the system prompt before every request. The LLM knows its boundaries and refuses unauthorized tools.
- **Plan E (audit)**: After openclaw responds, the response text is scanned for blocked tool names. Violations are logged to CloudWatch with `event_type=permission_denied`.

This is not a hard block, but it covers the vast majority of cases. For hard enforcement, the architecture would need to switch to AgentCore Gateway (MCP mode).

### Security model

Based on [Microsoft's OpenClaw security guidance](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk):

- **Credential exposure**: AgentCore Runtime microVM isolation — each tenant runs in a separate VM with no shared filesystem
- **Memory poisoning**: `safety.py` checks session summaries for injection patterns before writing to AgentCore Memory
- **Malicious skill execution**: `install_skill`, `load_extension`, `eval` are in `ALWAYS_BLOCKED_TOOLS` — always included in the blocked list in the system prompt
- **Input validation**: Messages truncated at 32,000 chars; tool names validated as `[a-zA-Z0-9_]+`; resource paths checked for null bytes and path traversal

OpenClaw's [security policy](https://github.com/openclaw/openclaw/security) explicitly states it does not model one gateway as a multi-tenant adversarial boundary. This project fills that gap.

---

## Repository Structure

```
sample-Moltbot-on-AWS-with-Bedrock/
│
├── agent-container/                     # Docker image deployed to AgentCore Runtime
│   ├── Dockerfile                       # Multi-stage: openclaw binary + Python 3.12 slim
│   ├── openclaw.json                    # openclaw config: chatCompletions enabled, aws-sdk auth
│   ├── requirements.txt                 # requests, boto3
│   ├── server.py                        # HTTP wrapper: /ping + /invocations (Plan A + E)
│   ├── permissions.py                   # SSM profile read/write; check_tool_permission; send_permission_request
│   ├── safety.py                        # Input validation + memory poisoning detection
│   ├── identity.py                      # ApprovalToken: issue, validate, revoke (max 24h TTL)
│   ├── memory.py                        # AgentCore Memory: load on start, save on end (optional)
│   ├── observability.py                 # Structured CloudWatch JSON logs
│   └── PERMISSION_SETUP_PROMPT.md       # Paste into SOUL.md for self-service onboarding
│
├── auth-agent/                          # Authorization Agent (separate AgentCore session)
│   ├── server.py                        # HTTP entry point: /ping + /invocations
│   ├── permission_request.py            # PermissionRequest dataclass
│   ├── handler.py                       # Approval notifications, 30-min timer, /pending approvals
│   └── approval_executor.py             # Execute approve/reject; update SSM; log to CloudWatch
│
├── src/utils/
│   └── agentcore.ts                     # deriveSessionKey(), formatInvocationResponse()
│
├── clawdbot-bedrock-agentcore-multitenancy.yaml  # CloudFormation: EC2 + ECR + SSM + CloudWatch
├── setup-enterprise-profiles.sh                  # Configure SSM profiles for enterprise roles
└── README_AGENTCORE.md                           # This file
```

**Where each piece of code runs:**

| Code | Where it runs | How it gets there |
|---|---|---|
| `agent-container/*.py` | Inside AgentCore Runtime microVM | Built into Docker image, pushed to ECR |
| `auth-agent/*.py` | Inside AgentCore Runtime (separate session) | Requires separate Docker image or second entry point |
| `gateway/tenant_router.py` | On EC2 (integration layer) | Not yet wired into openclaw Gateway — see note below |
| `src/utils/agentcore.ts` | Reference implementation | SessionKey logic already implemented in server.py |

> `gateway/tenant_router.py` provides `derive_tenant_id()`, `get_permission_profile()`, and `invoke_agent()`. These need to be called from a Python HTTP service on EC2 that openclaw routes messages to via webhook. This integration is not yet wired up.

---

## Enterprise Permission Profiles

Run `setup-enterprise-profiles.sh` after deployment to configure role-based access:

| Role | Tools | Use case |
|---|---|---|
| `finance-agent` | web_search, shell (read-only), file | SAP financial database queries |
| `web-agent` | All tools | Website development and deployment |
| `erp-agent` | web_search, shell, file, file_write | ERP read/write operations |
| `readonly-agent` | web_search only | General staff assistant |
| `auth-agent` | Unrestricted | Handles permission approvals |

```bash
STACK_NAME=openclaw-multitenancy REGION=us-east-1 bash setup-enterprise-profiles.sh
```

---

## Step-by-Step Deployment

### Prerequisites

- AWS CLI configured with permissions for: CloudFormation, EC2, VPC, IAM, ECR, Bedrock AgentCore, SSM, CloudWatch
- Docker installed locally
- EC2 Key Pair in your target region
- Bedrock model access enabled (Nova 2 Lite or Claude Sonnet)

### Phase 1 — Deploy AWS infrastructure

```bash
git clone <repo-url>
cd sample-Moltbot-on-AWS-with-Bedrock

aws cloudformation create-stack \
  --stack-name openclaw-multitenancy \
  --template-body file://clawdbot-bedrock-agentcore-multitenancy.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --parameters \
    ParameterKey=KeyPairName,ParameterValue=your-key-pair \
    ParameterKey=OpenClawModel,ParameterValue=global.amazon.nova-2-lite-v1:0 \
    ParameterKey=AuthAgentChannelType,ParameterValue=whatsapp

aws cloudformation wait stack-create-complete \
  --stack-name openclaw-multitenancy --region us-east-1
```

### Phase 2 — Build and push the Agent Container

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name openclaw-multitenancy --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`MultitenancyEcrRepositoryUri`].OutputValue' \
  --output text)

aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Build from repo root (Dockerfile uses paths relative to repo root)
docker build --platform linux/arm64 -f agent-container/Dockerfile -t $ECR_URI:latest .
docker push $ECR_URI:latest
```

### Phase 3 — Create the AgentCore Runtime

```bash
EXECUTION_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name openclaw-multitenancy --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`AgentContainerExecutionRoleArn`].OutputValue' \
  --output text)

RUNTIME_ID=$(aws bedrock-agentcore create-agent-runtime \
  --agent-runtime-name "openclaw-multitenancy-runtime" \
  --agent-runtime-artifact '{"containerConfiguration":{"containerUri":"'$ECR_URI':latest"}}' \
  --role-arn "$EXECUTION_ROLE_ARN" \
  --network-configuration '{"networkMode":"PUBLIC"}' \
  --environment-variables "STACK_NAME=openclaw-multitenancy,AWS_REGION=$REGION,BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --region $REGION \
  --query 'agentRuntimeId' --output text)

aws ssm put-parameter \
  --name "/openclaw/openclaw-multitenancy/runtime-id" \
  --value "$RUNTIME_ID" --type String --overwrite --region $REGION
```

### Phase 4 — Configure the Gateway on EC2

```bash
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name openclaw-multitenancy --region $REGION \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

aws ssm start-session --target $INSTANCE_ID --region $REGION
```

On the EC2 instance:
```bash
RUNTIME_ID=$(aws ssm get-parameter \
  --name "/openclaw/openclaw-multitenancy/runtime-id" \
  --region us-east-1 --query 'Parameter.Value' --output text)

python3 -c "
import json
c = json.load(open('/home/ubuntu/.openclaw/openclaw.json'))
c['agentcore'] = {'enabled': True, 'runtimeId': '$RUNTIME_ID', 'region': 'us-east-1'}
json.dump(c, open('/home/ubuntu/.openclaw/openclaw.json', 'w'), indent=2)
"
openclaw daemon restart
```

### Phase 5 — Access the Gateway UI

```bash
# Terminal 1: port forwarding
aws ssm start-session --target $INSTANCE_ID --region $REGION \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["18789"],"localPortNumber":["18789"]}'

# Terminal 2: get token
aws ssm get-parameter \
  --name "/openclaw/openclaw-multitenancy/gateway-token" \
  --region $REGION --with-decryption --query 'Parameter.Value' --output text
```

Open `http://localhost:18789/?token=<TOKEN>` in your browser, then connect WhatsApp/Telegram/Discord via the Channels UI.

### Phase 6 — Configure enterprise profiles (optional)

```bash
STACK_NAME=openclaw-multitenancy REGION=us-east-1 bash setup-enterprise-profiles.sh
```

---

## Day-2 Operations

### Update Authorization Agent behavior (no redeployment)

```bash
aws ssm put-parameter \
  --name "/openclaw/openclaw-multitenancy/auth-agent/system-prompt" \
  --type String --overwrite --value "Your updated instructions..."
```

### View tenant logs

```bash
aws logs filter-log-events \
  --log-group-name "/openclaw/openclaw-multitenancy/agents" \
  --filter-pattern '{ $.log_stream = "tenant_wa__8613800138000" }' \
  --region us-east-1
```

### Update the container image

```bash
docker build --platform linux/arm64 -f agent-container/Dockerfile -t $ECR_URI:latest .
docker push $ECR_URI:latest
# AgentCore Runtime picks up the new image on the next invocation
```

---

## Cost

| Component | Cost |
|---|---|
| EC2 c7g.large (Graviton, always-on) | ~$35/month |
| EBS 30GB gp3 | ~$2.40/month |
| VPC Endpoints (optional) | ~$22/month |
| AgentCore Runtime | Pay-per-invocation |
| ECR storage | ~$0.10/GB/month |
| CloudWatch Logs | Pay-per-GB |
| Bedrock Nova 2 Lite | $0.30/$2.50 per 1M tokens |

Light usage (100 conversations/day): ~$40-60/month total.

---

## Cleanup

```bash
aws bedrock-agentcore delete-agent-runtime --agent-runtime-id $RUNTIME_ID --region us-east-1
aws cloudformation delete-stack --stack-name openclaw-multitenancy --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name openclaw-multitenancy --region us-east-1
```

ECR images and SSM parameters are not deleted automatically.

---

## Resources

- [OpenClaw Documentation](https://docs.openclaw.ai/)
- [Amazon Bedrock AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html)
- [Microsoft OpenClaw Security Guidance](https://www.microsoft.com/en-us/security/blog/2026/02/19/running-openclaw-safely-identity-isolation-runtime-risk)
- [OpenClaw Security Policy](https://github.com/openclaw/openclaw/security)
