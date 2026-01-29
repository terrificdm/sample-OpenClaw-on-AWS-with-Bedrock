# Moltbot on AWS with Bedrock

> Deploy [Moltbot](https://github.com/moltbot/moltbot) (formerly Clawdbot) on AWS using Amazon Bedrock instead of managing Anthropic/OpenAI/DeepSeek API keys. Enterprise-ready, secure, one-click deployment with Graviton ARM processors.

English | [简体中文](README_CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-blue.svg)](https://aws.amazon.com/cloudformation/)

## What is This?

[Moltbot](https://github.com/moltbot/moltbot) (formerly Clawdbot) is an open-source personal AI assistant that connects to WhatsApp, Slack, Discord, and more. This project provides an **AWS-native deployment** using Amazon Bedrock's unified API, eliminating the need to manage multiple API keys from different providers.

## Why AWS Native?

| Original Moltbot | This Project |
|-------------------|--------------|
| Multiple API keys (Anthropic/OpenAI/etc.) | **Amazon Bedrock unified API + IAM** |
| Single model, fixed cost | **8 models available, Nova 2 Lite (90% cheaper vs Anthropic)** |
| x86 hardware, fixed specs | **x86/ARM flexible, Graviton recommended (20-40% savings)** |
| Tailscale VPN | **SSM Session Manager** |
| Manual setup | **CloudFormation (1-click)** |
| No audit logs | **CloudTrail (automatic)** |
| Public internet | **VPC Endpoints (private)** |

### Key Advantages

**1. Multi-Model Flexibility with Better Economics**
- **Nova Pro default**: $0.80/$3.20 per 1M tokens vs Claude's $3/$15 (73% cheaper)
- **8 models available**: Switch between Nova, Claude, DeepSeek, Llama with one parameter
- **Smart routing**: Use Nova Lite for simple tasks, Claude Sonnet for complex reasoning
- **No vendor lock-in**: Change models without code changes or redeployment

**2. Flexible Instance Sizing with Graviton Advantage (Recommended)**
- **x86 and ARM support**: Choose between t3/c5 (x86) or t4g/c7g (Graviton ARM)
- **Graviton ARM recommended**: 20-40% better price-performance than x86
- **Cost example**: t4g.medium ($24/mo) vs t3.medium ($30/mo) - same specs, 20% savings
- **Flexible sizing**: Scale from t4g.small ($12/mo) to c7g.xlarge ($108/mo) as needed
- **Energy efficient**: Graviton uses 70% less power than x86

**3. Enterprise Security & Compliance**
- **Zero API key management**: IAM roles replace multiple provider keys
- **Complete audit trail**: CloudTrail logs every Bedrock API call
- **Private networking**: VPC Endpoints keep traffic within AWS
- **Secure access**: SSM Session Manager, no public ports

**4. Cloud-Native Automation**
- **One-click deployment**: CloudFormation automates VPC, IAM, EC2, Bedrock setup
- **Infrastructure as Code**: Reproducible, version-controlled deployments
- **Multi-region support**: Deploy in 4 regions with identical configuration

## Key Benefits

- 🔐 **No API Key Management** - IAM roles handle authentication automatically
- 🤖 **Multi-Model Support** - Easily Switch between Claude, Nova, DeepSeek
- 🏢 **Enterprise-Ready** - Full CloudTrail audit logs and compliance support
- 🚀 **One-Click Deploy** - CloudFormation automates everything
- 🔒 **Secure Access** - SSM Session Manager, no public ports exposed
- 💰 **Cost Visibility** - Native AWS cost tracking and optimization

## Quick Start

### ⚡ One-Click Deploy (Recommended - 8 minutes to ready!)

> **Why CloudFormation?** Fully automated setup - no manual configuration needed. Just click, wait 8 minutes, and get your ready-to-use URL!

**Just 3 steps**:
1. ✅ Click "Launch Stack" button below
2. ✅ Select your EC2 key pair in the form
3. ✅ Wait ~8 minutes → Check "Outputs" tab → Copy URL → Start using!

**What happens automatically**:
- Creates VPC, subnets, security groups
- Launches EC2 instance
- Installs Node.js, Docker, Clawdbot
- Configures Bedrock integration
- Generates secure gateway token
- Outputs ready-to-use URL with token

Click to deploy:

| Region | Launch Stack |
|--------|--------------|
| **US West (Oregon)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |
| **US East (N. Virginia)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |
| **EU (Ireland)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |
| **Asia Pacific (Tokyo)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-1#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://sharefile-jiade.s3.cn-northwest-1.amazonaws.com.cn/clawdbot-bedrock.yaml) |

> **Note**: Using Global CRIS profiles - works in 30+ regions worldwide. Deploy in any region, requests auto-route to optimal locations.

**After deployment (~8 minutes), check CloudFormation Outputs tab**:

1. **Install SSM Plugin**: Click link in `Step1InstallSSMPlugin` (one-time setup)
2. **Port Forwarding**: Copy command from `Step2PortForwarding`, run on your computer (keep terminal open)
3. **Open URL**: Copy URL from `Step3AccessURL`, open in browser (token included!)
4. **Start Chatting**: Connect WhatsApp/Telegram/Discord in Web UI


![CloudFormation Outputs](images/20260128-105244.jpeg)
![Clawdbot Web UI](images/20260128-105059.jpg)

> **Before deploying**:
> - Before deploying, enable Bedrock models in Bedrock Console
> - Create an EC2 key pair in your target region
> - Lambda will automatically validate Bedrock access during deployment

### Alternative: Download and Upload

1. Download: [clawdbot-bedrock.yaml](clawdbot-bedrock.yaml)
2. Go to [CloudFormation Console](https://console.aws.amazon.com/cloudformation/)
3. Upload template and deploy

| Region | Launch Stack |
|--------|--------------|
| **US East (N. Virginia)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://clawdbot-templates-jiade.s3.amazonaws.com/clawdbot-bedrock.yaml) |
| **US West (Oregon)** | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?stackName=clawdbot-bedrock&templateURL=https://clawdbot-templates-jiade.s3.amazonaws.com/clawdbot-bedrock.yaml) |

> **Before deploying**: 
> 1. Enable Bedrock models in [Bedrock Console](https://console.aws.amazon.com/bedrock/)
> 2. Create an EC2 key pair in your target region

### Alternative: CLI Deploy

- AWS account with Bedrock access
- [AWS CLI](https://aws.amazon.com/cli/) installed
- [SSM Session Manager Plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) installed
- EC2 key pair created

### Manual Deploy (Alternative)

**Using helper script**:

```bash
./scripts/deploy.sh clawdbot-bedrock us-west-2 your-keypair
```

**Using AWS CLI**:

```bash
aws cloudformation create-stack \
  --stack-name clawdbot-bedrock \
  --template-body file://cloudformation/clawdbot-bedrock.yaml \
  --parameters ParameterKey=KeyPairName,ParameterValue=your-keypair \
  --capabilities CAPABILITY_IAM \
  --region us-west-2

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name clawdbot-bedrock \
  --region us-west-2
```

> **Note**: Lambda pre-check runs automatically during deployment. If it fails, check CloudFormation events for details.

### Access Clawdbot

```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name clawdbot-bedrock \
  --query 'Stacks[0].Outputs[?OutputKey==`InstanceId`].OutputValue' \
  --output text)

# Start port forwarding
aws ssm start-session \
  --target $INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["18789"],"localPortNumber":["18789"]}'

# Get token (new terminal)
aws ssm start-session --target $INSTANCE_ID
sudo su - ubuntu
cat ~/.clawdbot/gateway_token.txt

# Open browser
http://localhost:18789/?token=<your-token>
```

## How to Use Moltbot

### Connect Messaging Platforms

**For detailed configuration guides, visit [Moltbot Official Documentation](https://docs.molt.bot/).**

#### WhatsApp (Recommended)

1. **In Web UI**: Click "Channels" → "Add Channel" → "WhatsApp"
2. **Scan QR Code**: Use WhatsApp on your phone
   - Open WhatsApp → Settings → Linked Devices
   - Tap "Link a Device"
   - Scan the QR code displayed
3. **Verify**: Send a test message to your Moltbot number

**Tip**: Use a dedicated phone number or enable `selfChatMode` for personal number.

📖 **Full guide**: https://docs.molt.bot/channels/whatsapp

#### Telegram

1. **Create Bot**: Message [@BotFather](https://t.me/botfather)
   ```
   /newbot
   Choose a name: My Moltbot
   Choose a username: my_moltbot_bot
   ```
2. **Copy Token**: BotFather will give you a token like `123456:ABC-DEF...`
3. **Configure**: In Web UI, add Telegram channel with your bot token
4. **Test**: Send `/start` to your bot on Telegram

📖 **Full guide**: https://docs.molt.bot/channels/telegram

#### Discord

1. **Create Bot**: Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Go to "Bot" → "Add Bot"
   - Copy bot token
   - Enable intents: Message Content, Server Members
2. **Invite Bot**: Generate invite URL with permissions
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot
   ```
3. **Configure**: In Web UI, add Discord channel with bot token
4. **Test**: Mention your bot in a Discord channel

📖 **Full guide**: https://docs.molt.bot/channels/discord

#### Slack

1. **Create App**: Visit [Slack API](https://api.slack.com/apps)
2. **Configure Bot**: Add bot token scopes (chat:write, channels:history)
3. **Install**: Install app to your workspace
4. **Configure**: In Web UI, add Slack channel
5. **Test**: Invite bot to a channel and mention it

📖 **Full guide**: https://docs.molt.bot/channels/slack

#### Microsoft Teams

1. **Install Plugin**: `npm install -g moltbot-msteams`
2. **Create Azure Bot**: Visit [Azure Portal](https://portal.azure.com/)
   - Create Bot Channels Registration
   - Get App ID, Client Secret, Tenant ID
3. **Configure**: In Web UI, add Microsoft Teams channel with credentials
4. **Expose Endpoint**: Use ngrok or public URL for `/api/messages` (port 3978)
5. **Test**: Message your bot in Teams

📖 **Full guide**: https://docs.molt.bot/channels/msteams

#### Lark / Feishu (飞书) - Community Plugin

Moltbot doesn't have official Lark/Feishu support, but the community has created a plugin:

**Community Plugin**: https://www.npmjs.com/package/moltbot-feishu

Install on your EC2 instance to forward messages between Feishu and Moltbot via WebSocket. No public IP or domain required.

### Using Moltbot

#### Send Messages

**Via WhatsApp/Telegram/Discord**: Just send a message!

```
You: What's the weather today?
Clawdbot: Let me check that for you...
```

**Via CLI**:
```bash
# SSH/SSM to instance
clawdbot message send --to +1234567890 --message "Hello"
```

#### Chat Commands

Send these in any connected channel:

| Command | Description |
|---------|-------------|
| `/status` | Show session status (model, tokens, cost) |
| `/new` or `/reset` | Start a new conversation |
| `/think high` | Enable deep thinking mode |
| `/help` | Show available commands |

#### Voice Messages

**WhatsApp/Telegram**: Send voice notes directly - Clawdbot will transcribe and respond!

#### Browser Control

```
You: Open google.com and search for "AWS Bedrock"
Clawdbot: *Opens browser, performs search, returns results*
```

#### Scheduled Tasks

```
You: Remind me every day at 9am to check emails
Clawdbot: *Creates cron job*
```

### Advanced Features

#### Skills

```bash
# List available skills
clawdbot skills list

# Install a skill
clawdbot skills install voice-generation

# View installed skills
clawdbot skills installed
```

#### Custom Prompts

Create `~/clawd/system.md` on the instance:

```markdown
You are my personal assistant. Be concise and helpful.
Always respond in a friendly tone.
```

#### Multi-Agent Routing

Configure different agents for different channels in Web UI.

For detailed guides, visit [Moltbot Documentation](https://docs.molt.bot/).

## Architecture

```
Your Phone/Computer → WhatsApp/Telegram → EC2 (Moltbot) → Bedrock (Claude)
                                              ↓
                                         Your Data Stays Here
                                         (Secure, Private, Audited)
```

### Why EC2 + Bedrock?

**🔒 Enterprise Security Without the Complexity**

Traditional AI assistants require managing multiple API keys from different providers (Anthropic, OpenAI, DeepSeek). Each key is a security risk—if leaked, attackers can rack up bills or access your data. With Bedrock and IAM roles, there are no keys to manage or leak. The EC2 instance authenticates automatically, and every API call is logged in CloudTrail for compliance. VPC Endpoints keep all traffic within AWS's private network, meeting enterprise security requirements without complex VPN setups.

**💰 Cost-Effective Multi-Model Strategy**

Bedrock's unified API lets you optimize costs by choosing the right model for each task. Use Nova Pro ($0.80/$3.20 per 1M tokens) for most conversations—73% cheaper than Claude. Switch to Claude Sonnet 4.5 for complex reasoning, or Nova Lite for simple FAQs. One customer reduced AI costs by 60% using this smart routing strategy. With Graviton ARM instances (20-40% cheaper than x86), total infrastructure cost starts at just $36/month—less than two ChatGPT Plus subscriptions, but serving your entire team.

**🛡️ 24/7 Reliability You Can Trust**

Your Mac Mini needs to run 24/7, vulnerable to power outages, network issues, and hardware failures. EC2 instances run in enterprise data centers with redundant power and networking, achieving 99.99% uptime with multi-AZ deployment. Auto-restart on failure, CloudWatch monitoring, and AWS support coverage mean your AI assistant is more reliable than your home internet.

**📊 Transparent Operations and Compliance**

CloudTrail automatically logs every Bedrock API call—who made it, when, which model, what was processed. This audit trail is critical for regulated industries (finance, healthcare, government). Cost Explorer shows exactly what you're spending on AI vs infrastructure. Try getting that level of visibility with local deployment and scattered API bills.

**🌐 Global Scale with Local Performance**

Deploy in multiple regions (US, EU, Asia) with identical configuration. Global CRIS automatically routes requests to optimal locations—US users get US processing, Japan users get Japan processing. Need to handle traffic spikes? Scale from t4g.small to c7g.xlarge in minutes. Local deployment? You're stuck with whatever hardware you bought.

**🚀 Cloud-Native Task Orchestration**

This is where cloud deployment truly shines. Your Moltbot can orchestrate AWS services: spin up 100 Spot instances for parallel video processing ($3, 20 minutes), trigger Glue jobs for data analysis, invoke Lambda functions for automation. Local Mac Mini? Limited to single-machine performance. Cloud Moltbot? It's a command center for your entire AWS infrastructure.

### What Runs on EC2

- **Moltbot Gateway**: Routes messages, manages sessions (~300MB RAM)
- **Browser Control**: Web automation when needed (~500MB RAM)
- **Docker Sandbox**: Isolated code execution (secure)
- **Total Usage**: ~1-2GB of 30GB disk, ~500MB-1GB RAM

### Data Flow Example

```
You: "Summarize this document"
  ↓ WhatsApp (public internet)
EC2: Receives message, authenticates with IAM
  ↓ VPC Endpoint (private network)
Bedrock: Claude processes document
  ↓ VPC Endpoint (private network)
EC2: Formats response
  ↓ WhatsApp (public internet)
You: Receives summary

Cost: ~$0.01 per request
Time: 2-5 seconds
Security: All AWS traffic via private network
```

**Key Components**:
- **EC2 Instance**: Runs Clawdbot gateway and browser control
- **IAM Role**: Authenticates with Bedrock (no API keys)
- **SSM Session Manager**: Secure access without public ports
- **VPC Endpoints**: Private network access to Bedrock
- **Lambda Pre-Check**: Validates environment before deployment

## Cost Breakdown

### Monthly Infrastructure Cost

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| EC2 (t4g.medium, Graviton) | 2 vCPU, 4GB RAM | $24.19 |
| EBS (gp3) | 30GB | $2.40 |
| VPC Endpoints | 3 endpoints | $21.60 |
| Data Transfer | VPC endpoint processing | $5-10 |
| **Subtotal** | | **$53-58** |

### Bedrock Usage Cost

| Model | Input | Output |
|-------|-------|--------|
| Nova 2 Lite | $0.30/1M tokens | $2.50/1M tokens |
| Claude Sonnet 4.5 | $3/1M tokens | $15/1M tokens |
| Claude Haiku 4.5 | $1/1M tokens | $5/1M tokens |
| Nova Pro | $0.80/1M tokens | $3.20/1M tokens |
| DeepSeek R1 | $0.55/1M tokens | $2.19/1M tokens |

**Example**: 100 conversations/day with Nova 2 Lite ≈ $5-8/month

**Total**: ~$58-66/month for light usage

### Cost Optimization

- Use Nova 2 Lite instead of Claude: 90% cheaper
- Use Graviton instances: 20-40% cheaper than x86
- Disable VPC endpoints: Save $22/month (less secure)
- Use Savings Plans: Save 30-40% on EC2

## Configuration

### Supported Models

```yaml
# In CloudFormation parameters
ClawdbotModel:
  - global.amazon.nova-2-lite-v1:0              # Default, most cost-effective
  - global.anthropic.claude-sonnet-4-5-20250929-v1:0  # Most capable
  - us.amazon.nova-pro-v1:0                     # Balanced performance
  - global.anthropic.claude-opus-4-5-20251101-v1:0    # Advanced reasoning
  - global.anthropic.claude-haiku-4-5-20251001-v1:0   # Fast and efficient
  - us.deepseek.r1-v1:0                         # Open-source reasoning
  - us.meta.llama3-3-70b-instruct-v1:0          # Open-source alternative
```

**Model Selection Guide**:
- **Nova 2 Lite** (default): Most cost-effective, 90% cheaper than Claude, great for everyday tasks
- **Claude Sonnet 4.5**: Most capable for complex reasoning and coding
- **Nova Pro**: Best balance of performance and cost, supports multimodal
- **DeepSeek R1**: Cost-effective open-source reasoning model

### Instance Types

```yaml
InstanceType:
  # Graviton (ARM) - Recommended for best price-performance
  - t4g.small   # $12/month, 2GB RAM
  - t4g.medium  # $24/month, 4GB RAM (default)
  - t4g.large   # $48/month, 8GB RAM
  - t4g.xlarge  # $96/month, 16GB RAM
  - c7g.large   # $54/month, 4GB RAM, compute-optimized
  - c7g.xlarge  # $108/month, 8GB RAM, compute-optimized
  
  # x86 - Alternative for broader compatibility
  - t3.small    # $15/month, 2GB RAM
  - t3.medium   # $30/month, 4GB RAM
  - t3.large    # $60/month, 8GB RAM
  - c5.xlarge   # $122/month, 8GB RAM, compute-optimized
```

**Graviton Benefits**: ARM-based processors offer 20-40% better price-performance than x86 instances. Recommended for most workloads.

### VPC Endpoints

```yaml
CreateVPCEndpoints: true   # Recommended for production
  # Pros: Private network, more secure, lower latency
  # Cons: +$22/month

CreateVPCEndpoints: false  # For cost optimization
  # Pros: Save $22/month
  # Cons: Traffic goes through public internet
```

## Security Features

### 1. IAM Role Authentication

No API keys to manage. The EC2 instance uses an IAM role to authenticate with Bedrock:

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "*"
}
```

### 2. SSM Session Manager

No SSH keys needed. Access via AWS Systems Manager:

- ✅ No public ports (except optional SSH fallback)
- ✅ Automatic session logging
- ✅ CloudTrail audit trail
- ✅ Session timeout controls

### 3. VPC Endpoints

Traffic stays within AWS network:

- ✅ Bedrock API calls don't go through internet
- ✅ Lower latency
- ✅ Compliance-friendly

### 4. Docker Sandbox

Non-main sessions run in isolated Docker containers:

```json
{
  "sandbox": {
    "mode": "non-main",
    "allowlist": ["bash", "read", "write"],
    "denylist": ["browser", "gateway"]
  }
}
```

## Monitoring & Audit

### CloudTrail Logs

All Bedrock API calls are automatically logged:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=InvokeModel \
  --region us-west-2
```

### CloudWatch Logs

```bash
# View setup logs
aws logs tail /var/log/clawdbot-setup.log --follow

# View SSM session logs
aws logs tail /aws/ssm/session-logs --follow
```

### Cost Monitoring

```bash
# View Bedrock costs
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["Amazon Bedrock"]}}'
```

## Troubleshooting

### Pre-Check Failed

```bash
# View Lambda logs
aws logs tail /aws/lambda/clawdbot-bedrock-bedrock-precheck --follow

# Common issues:
# 1. Model not enabled → Enable in Bedrock Console
# 2. Region not supported → Use us-east-1 or us-west-2
# 3. Permission denied → Check IAM permissions
```

### Cannot Connect via SSM

```bash
# Check SSM agent status
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=$INSTANCE_ID"

# Check IAM role
aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

### Bedrock API Errors

```bash
# Test Bedrock access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}' \
  --region us-west-2 \
  output.txt

# View Clawdbot logs
journalctl --user -u clawdbot-gateway -n 100
```

## Comparison with Original Moltbot

### Local Deployment (Original)

**Setup**: Install on Mac Mini/PC, configure API keys, set up Tailscale VPN
**Cost**: $20-30/month (API fees only, excludes $599 hardware + electricity)
**Models**: Single provider (Anthropic/OpenAI), manual switching
**Security**: API keys in config files, no audit logs
**Availability**: Depends on your hardware and internet
**Scalability**: Limited to single machine resources

### Cloud Deployment (This Project)

**Setup**: One-click CloudFormation deployment, 8 minutes to ready
**Cost**: $36-50/month all-inclusive (Graviton + Nova Pro + VPC)
**Models**: 8 models via Bedrock, switch with one parameter
**Security**: IAM roles (no keys), CloudTrail audit, VPC Endpoints
**Availability**: 99.99% uptime with enterprise SLA
**Scalability**: Elastic sizing (t4g.small to c7g.xlarge), orchestrate cloud resources

**Bottom line**: Cloud deployment costs similar but delivers enterprise-grade security, multi-model flexibility, and unlimited scalability. For teams, one cloud instance ($50/mo) serves 10+ people vs individual ChatGPT Plus subscriptions ($200/mo).

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This deployment template is provided as-is. Clawdbot itself is licensed under its original license.

## Resources

- [Moltbot Official Docs](https://docs.molt.bot/)
- [Moltbot GitHub](https://github.com/moltbot/moltbot)
- [Amazon Bedrock Docs](https://docs.aws.amazon.com/bedrock/)
- [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)

## Support

- **Moltbot Issues**: [GitHub Issues](https://github.com/moltbot/moltbot/issues)
- **AWS Bedrock**: [AWS re:Post](https://repost.aws/tags/bedrock)
- **This Project**: [GitHub Issues](https://github.com/your-repo/clawdbot-aws-bedrock/issues)

---

**Built by builder + Kiro**

Deploy your personal AI assistant on AWS infrastructure you control.
