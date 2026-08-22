# Talking Points - Slide by Slide

> **Session**: Designing Production-Ready OpenClaw on AWS  
> **Demo integration**: Strands Agent on AgentCore (Refund Agent demo)

---

## Slide 1: Housekeeping (Skip in most events)

- Internal slide. Don't share the deck. Use for public/company events.

---

## Slide 2: Session Description (Hidden - for event listing only)

- L300-L400 session
- Three developer benefits: architecture decisions, secure agent systems, cost optimization

---

## Slide 3: Title Slide

**Talking point:**
> "Today we're going to take OpenClaw from a developer toy to a production-grade system. Many of you have already played with it locally. But running it at scale? That's a completely different game. This session is about making it secure, reliable, and cost-effective on AWS."

---

## Slide 4: Agenda

**Talking points:**
1. Why OpenClaw is moving into production (adoption is accelerating)
2. What actually breaks when you go to production (the hard truths)
3. Deployment patterns on AWS (4 paths)
4. Deep dives into isolation, security, observability, and cost

> "We'll move fast. There are 3 live demos. By the end, you'll know exactly which architecture to pick for your use case."

---

## Slide 5: Section Divider - Why OpenClaw Is Moving into Production

> "Let's start with WHY. Why is everyone suddenly deploying this thing?"

---

## Slide 6: OpenClaw Is Taking Off

**Talking points:**
- 230K+ GitHub stars, one of the fastest-growing OSS projects
- Not just chat - it's tool execution: email, web search, code execution, platform integrations
- 10,000+ community skills (App Store-like ecosystem)
- 15+ supported channels

> "OpenClaw is not a chatbot. It's an agent runtime. It combines LLM reasoning with real tool execution - calling APIs, running code, orchestrating workflows. That's what makes it powerful. That's also what makes it dangerous if you don't control it."

---

## Slide 7: Section Divider - What Breaks at Scale

> "So it works great on your laptop. You show your manager a demo. They say 'ship it.' And then reality hits."

---

## Slide 8: Challenges in Production Deployment

**Talking points (4 personas, 4 problems):**

| Persona | Problem | Quote |
|---------|---------|-------|
| Fintech (KYC data) | Isolation | "Customer A's data must never be visible to Customer B. Container isolation shares a kernel." |
| Large enterprise (200+ agents) | Security | "Marketing users can call finance APIs. We can't control 1000+ plugins." |
| AI product company (10K executions/day) | Observability | "We don't know which agent called which tool. When incidents happen, we can't trace them." |
| Fast-growing startup (limited budget) | Cost | "EC2 runs 24/7 but agents are mostly idle waiting on LLM responses. We're paying for nothing." |

> "These four dimensions - isolation, security, observability, cost - are the lens we'll use for the rest of this talk. Every architecture decision maps back to these."

**Demo tie-in:** "By the end, I'll show you a live demo where a $2000 refund is blocked by Cedar policy before the agent even sees it. That's the security story in action."

---

## Slide 9: Section Divider - Deployment Patterns on AWS

> "Now let's talk solutions. There are 4 deployment paths. You'll pick one based on where you are in your journey."

---

## Slide 10: Deployment Options (Path A through D)

**Talking points:**

| Path | Who | What |
|------|-----|------|
| A: Local Dev | Individual devs | $0, exploration, debugging |
| B: Rapid Cloud | Small teams | Lightsail/MyClaw, PoC validation |
| C: Self-Managed | Platform eng teams | EC2/ECS/EKS, full control, heavy ops |
| D: Fully Managed (RECOMMENDED) | Production teams | AgentCore, built-in security, low ops |

> "Most of you will start with Path A - that's fine. Path B lets you validate in the cloud quickly. But for production? The real decision is between C and D. Full control vs. fully managed. Let's compare them."

**Demo tie-in:** "In my demo, I'll deploy a simple Strands agent to Path D in one command. And here's the key point - AgentCore isn't just for OpenClaw. It works with Strands, LangGraph, Google ADK, OpenAI Agents. Any framework."

---

## Slide 11: Dimension 1 - Isolation (Firecracker microVMs)

**Talking points:**
- Containers share a kernel (namespace/cgroup isolation) - larger attack surface, container escape risks (CVE-2024-21626)
- AgentCore uses Firecracker microVMs - hardware-virtualized isolation (KVM-based)
- Each session: dedicated CPU, memory, filesystem
- ~5s cold start, 8hr max session, automatic teardown, zero residual state

> "If you're running multi-tenant workloads - multiple customers, multiple departments - container isolation is not enough. Firecracker gives you hardware-level boundaries. Each user gets their own VM. When the session ends, it's destroyed. No state leaks between tenants. Ever."

---

## Slide 12: Demo - Production-Ready Isolation

**Demo talking point:**
> "Let me show you this in action. Two OpenClaw sessions running on AgentCore. User A has secrets. User B tries to access them. Watch what happens."

Show the GitHub sample: `https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock`

---

## Slide 13: Dimension 2 - Security (Self-Hosted vs AgentCore)

**Talking points:**

Self-hosted requires building 5 subsystems:
1. Policy Engine (2-4 weeks)
2. Identity Integration (2-3 weeks)
3. API Gateway (3-6 weeks)
4. Audit System (2-3 weeks)
5. Credential Management (1-2 weeks)

Total: **2.5-4.5 months**, 1-2 engineers full-time

AgentCore provides all of this **built-in**, configured in hours:
- Cedar-based policy (no code)
- Native identity (SSO out of the box)
- Managed Gateway
- Native observability
- Integrated Secrets Manager

> "I've talked to teams that spent 4 months building a policy layer. AgentCore gives you Cedar policies out of the box. You describe the rule in English, it generates the Cedar code. Done in minutes."

**Demo tie-in:** "This is exactly what I'll show in my demo. One command to generate a policy from natural language. 'Only allow refunds under $1000.' That's it."

---

## Slide 14: Scenario Deep Dive - Preventing Unauthorized Access

**Talking points (the story):**
- Large enterprise: 200+ agents across departments
- Marketing user's agent tries to call a Finance API (GetBudget)
- Without governance: access is allowed, detected only in audit after the fact
- With AgentCore Policy:
  1. Identity resolution (who is calling?)
  2. Policy evaluation (is this allowed?)
  3. Gateway enforcement (block in real time)
  4. Observability & audit (log the denial)

**Cedar policy example:**
```
forbid(principal in Group::"Marketing", action == Action::"GetBudget", resource == Tool::"FinanceAPI");
```

> "The key word here is REAL TIME. Not 'we'll find it in the audit logs next week.' The Gateway blocks it before the tool ever executes. The agent never sees the data. This is deterministic enforcement - outside the agent code, immune to prompt injection."

**Demo tie-in:** "In my demo, this is exactly the $2000 refund scenario. The curl request hits the Gateway, Cedar evaluates it, and the response comes back: DENIED. The Lambda never fires."

---

## Slide 15: Demo - Enterprise Access Control

**Demo talking point:**
> "Let me show you AgentCore Policy in action with the Refund Agent."

**Live demo flow:**
1. Show the Cedar policy (natural language generated)
2. curl with $500 - ALLOWED (response: "Refund processed")
3. curl with $2000 - DENIED ("Tool Execution Denied: policy enforcement")
4. "The agent never saw the $2000 request. The Gateway killed it."

---

## Slide 16: Dimension 3 - Observability

**Talking points:**

| Self-managed | AgentCore |
|---|---|
| Fragmented CloudWatch logs | Native end-to-end tracing |
| Custom benchmarks + manual evaluation | Built-in evaluation & scoring |
| No correlation between agent steps | Full trace: reasoning → tool call → policy → execution |

> "More than 53% of enterprise users grant privileged access to OpenClaw within the first month. The challenge isn't just adoption - it's the lack of governance, audit, and runtime visibility."

**Demo tie-in:** "After invoking through the runtime, you see the full trace in the AgentCore console - every reasoning step, every tool call, every policy decision. Zero custom instrumentation."

---

## Slide 17: Demo - End-to-End Tracing

**Demo talking point:**
> "Let me invoke the agent through the runtime and show you the trace."

```bash
agentcore invoke --prompt "Process a refund of 500 dollars for order ORD-5001, reason: wrong item shipped" --stream
```

Then show the trace in the AgentCore console.

---

## Slide 18: Dimension 4 - Cost

**Talking points (3 scenarios):**

| Scenario | EC2 Cost | AgentCore Cost | Savings |
|----------|----------|---------------|---------|
| 24/7 assistants (support, ops) | $30.58/user/mo | $9.03/user/mo | **64%** |
| Long-running sessions (code review, analysis) | $55.11/user/mo | $7.96/user/mo | **83%** |
| Short bursty interactions (CI, monitoring) | $18.31/user/mo | $2.65/user/mo | **83%** |

> "The reason is simple. EC2 runs 24/7. Your agent is active maybe 30% of the time - the rest it's waiting on LLM responses. You're paying for idle compute. AgentCore is pay-per-use: CPU hours + memory hours. When the agent isn't running, you pay nothing."

---

## Slide 19: Comparison Table (All 4 Paths)

**Talking point:**
> "Here's the full picture. If you take one screenshot today, make it this slide. The key tradeoff: Path C gives maximum control but costs 3-5 engineers and months of work. Path D gives you 90% of the capability in hours, fully managed."

Highlight the key differentiators:
- Governance: "Fully self-built (3-5 engineers effort)" vs "Built-in (Identity + Policy + Gateway)"
- Isolation: "Depends on implementation" vs "Per-user microVMs (hardware isolation)"
- Billing: "Always-on (fixed cost)" vs "Pay-per-use (CPU / memory / runtime)"

---

## Slide 20: Section Divider - Choosing the Right Architecture

> "So how do you choose? Let me make it simple."

---

## Slide 21: Demo - OpenClaw End-to-End Experience

**Demo talking point:**
> "Here's what the full user experience looks like. User logs in, starts using OpenClaw on AgentCore. Everything we talked about - isolation, policy, observability, cost - happens transparently."

---

## Slide 22: Production-Ready OpenClaw Requires...

**Summary talking points (tie it all together):**

1. **Isolation** - Hardware-level with Firecracker microVMs. Zero residual state.
2. **Security** - Identity + Policy + Gateway integrated. No custom security engineering.
3. **Observability** - Native end-to-end tracing. Real-time visibility.
4. **Cost** - Up to 83% savings. Pay-per-use aligned with actual workload.
5. **Flexibility** - Persistent Agent Memory (~200ms retrieval), skills ecosystem retained, S3-backed storage.

> "These are not optional features. These are requirements for any production agent system. AgentCore gives you all five out of the box."

**Final demo callback:** "And remember - this isn't just for OpenClaw. The Refund Agent I showed you runs on Strands. You could swap in LangGraph, Google ADK, or OpenAI Agents. The platform doesn't care. It secures ANY agent."

---

## Slide 23: AWS Builder Center

> "Scan this QR code to access more content, find events, and connect with others working on this."

---

## Slide 24: Thanks

> "Thanks everyone. The demo code is on GitHub - I'll drop the link in the chat. Happy to take questions."

Share: `https://github.com/<your-repo>/openclaw-agentcore-demo`

---

## Demo Integration Summary

| When in talk | What to show | Duration |
|---|---|---|
| Slide 12 | Isolation demo (pre-recorded or live) | 1 min |
| Slide 15 | **YOUR DEMO**: Refund Agent + Cedar policy (curl $500 allowed, $2000 denied) | 2-3 min |
| Slide 17 | Observability: `agentcore invoke` + show trace in console | 1-2 min |
| Slide 21 | End-to-end experience (pre-recorded or live) | 1 min |

**Total demo time: 5-7 minutes across 24 slides**
