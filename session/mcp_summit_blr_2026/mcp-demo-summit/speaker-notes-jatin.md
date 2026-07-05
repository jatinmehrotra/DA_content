# Speaker Notes — Jatin Mehrotra

## Talk: "You Built an MCP Server — Now What?"
### MCP Dev Summit Bengaluru 2026

---

## Slide 1: Title Slide (JATIN)

> "Hey everyone! I'm Jatin Mehrotra, Developer Advocate at AWS, and together with Varsha Das we're going to talk about something every MCP developer faces — you've built your MCP server, it works locally... now what? How do you get it to production? Let's find out."

---

## Slides 2–11: (VARSHA PRESENTS)

*Varsha covers: The Magic Moment, Production challenges, Transport, Identity, Governance, Observability, Two Paths to Production, Managed Runtime, Architecture diagram.*

---

## Slide 12: DEMO TIME — 30 lines to production in 5 minutes (JATIN)

> "Alright, enough slides. Let me show you this live. We're going to take a 30-line MCP server and get it to production — with auth, policy, and traces — in about 5 minutes. Let's switch to the terminal."

---

## Slide 13: Demo Step 1 — The Server (JATIN)

> "Here's our server. 30 lines of Python. Three tools — search_docs, get_oncall, create_incident. Plus one dangerous one — delete_incident. We'll use that to demo policy blocking later."

> "Notice: no auth code, no tracing code, no policy logic. Just pure business logic. The decorator and docstring IS the tool schema — agents discover these automatically via MCP's tools/list protocol."

> *[Video shows: server.py code, then MCP Inspector connecting and listing tools]*

> "Works locally. Every tool is callable. Including delete. That's the problem we're solving."

---

## Slide 14: Demo Step 2 — Deploy to AgentCore (JATIN)

> "One command: `agentcore deploy`. No Dockerfile, no Kubernetes, no load balancer config."

> *[Video shows: deploy.sh running, CDK deploying, status showing READY]*

> "What just happened? AgentCore packaged our server.py, deployed it as a managed runtime, set up IAM auth, and auto-instrumented it with OpenTelemetry for traces. Zero infra code from us."

---

## Slide 15: DEMO PART 1 — Kiro + CDK deployment (JATIN)

> "Here you can see Kiro helping us scaffold the project, configure the CDK, and deploy — all from the IDE. The entire deployment is driven by a deploy.sh script that handles project creation, resource configuration, and deployment in one shot."

> *[Video plays showing the Kiro terminal output]*

---

## Slide 16: Demo Step 3 — Tools Discovered via Gateway (JATIN)

> "Now the tools are discoverable through the Gateway. Watch — we call tools/list on the Gateway endpoint..."

> *[Video shows: tools/list response with 4 tools]*

> "Three tools plus the built-in search utility. Zero schema registration. We added a tool, redeployed, and it's discoverable. That's the MCP protocol at work."

---

## Slide 17: Demo Step 4 — Multi-Tool in Action (JATIN)

> "Now watch search_docs being called through the gateway. This goes through IAM auth first..."

> *[Video shows: SigV4-authenticated tool call returning results]*

> "The request went: credentials → Gateway (IAM verified) → Cedar Policy (checked) → Runtime (server.py) → response back. All traced automatically."

> "And without credentials? Watch..."

> *[Video shows: 401 Unauthorized]*

> "That's IAM auth protecting your MCP server. No API keys, no tokens — just SigV4."

---

## Slide 18: DEMO PART 2 — Cedar Policy in Action (JATIN)

> "Now the fun part. We have a delete_incident tool deployed. In production, we don't want ANYONE calling it. Not even if an AI agent hallucinates and tries."

> "We wrote a Cedar policy — one line — that says 'forbid this action on this gateway.' The tool exists, agents can see it... but the moment they try to call it..."

---

## Slide 19: DEMO PART 2 — Console screenshot (JATIN)

> "Here's the policy in the console. Two policies: allow_all permits everything, block_delete forbids delete_incident. Forbid wins — that's Cedar's semantics."

---

## Slide 20: Demo Step 5 — Cedar Policy Blocks It (JATIN)

> *[Video shows: delete_incident tool call → "Tool Execution Denied"]*

> "Tool Execution Denied. Policy evaluation denied due to block_delete."

> "The tool function was never called. The server never saw the request. The Gateway intercepted it, evaluated the Cedar policy, and said no. This is governance at the platform layer — not in your application code."

> "Think about what that means: you can deploy tools today, and your security team can add policies tomorrow. No code changes. No redeployment."

---

## Slide 21: DEMO PART 3 — Observability (JATIN)

> "Last thing — every tool call we just made? Traced. Let me show you CloudWatch."

---

## Slide 22: DEMO PART 3 — Console screenshot (JATIN)

> "133 total invocations, 3K ms average latency, 0.75% error rate. All automatic. We didn't add a single line of tracing code — AgentCore auto-instruments with OpenTelemetry."

> "You can see per-tool latency, error rates, and drill into individual traces. This is what production debugging looks like for MCP servers."

---

## Slide 23: What We Just Did (JATIN)

> "Let's recap. Four steps:
> 1. Server code — 30 lines, pure MCP
> 2. Deploy — one command, managed runtime
> 3. Gateway — tool discovery via MCP protocol, IAM auth
> 4. Cedar policy — governance without touching code
>
> We went from localhost to production-grade MCP in under 5 minutes. No containers, no Kubernetes, no custom auth middleware, no tracing SDK setup."

---

## Slide 24: Production Readiness Checklist (JATIN)

> "Here's your checklist when you go home tonight:
> - Transport: switch from stdio to Streamable HTTP ✓
> - Auth: add IAM via the Gateway ✓
> - Gateway: route and govern tool access ✓
> - Cedar Policy: define what's allowed and what's blocked ✓
> - Observability: trace every tool call ✓
> - Versioning: update without breaking clients ✓
>
> AgentCore gives you all of this. Your job? Write the 30 lines of business logic."

---

## Slide 25: Your Next Step (JATIN)

> "Your next step: deploy your first MCP server today. The demo repo is on GitHub — scan the QR code. It has the server, the deploy script, and the test suite. Everything you need to go from zero to production."

> "And if you get stuck, find us at the AWS booth. We're happy to help."

---

## Slide 26: Try it Out Now! (JATIN)

> "Here's the QR code for the GitHub repo. Clone it, follow the README, and you'll have a production MCP server in 10 minutes."

---

## Slides 27–28: Follow Our Work (JATIN + VARSHA)

> "Follow us — LinkedIn, blogs, YouTube. We're building more content around MCP and AgentCore. Thanks for being here!"

---

## Slide 29: Thank You (JATIN)

> "Thank you, Bengaluru! Go build something amazing with MCP. We can't wait to see what you create."

---

## Tips for delivery:

- **Video demos**: The demo is pre-recorded and embedded in slides. Narrate over the video — don't read the terminal output, explain what's happening conceptually.
- **Pacing**: Let the video play, then add your commentary in the pauses. Don't talk over the key terminal output moments.
- **Key moment**: The policy denial is the "wow" moment. Pause after the video shows it and let it sink in.
- **Energy**: Slide 12 (DEMO TIME) is your energy transition. Build anticipation: "Let me show you what this looks like..."
- **Fallback**: Videos are pre-recorded so no risk of failure. If video doesn't play, describe what it shows and move on.