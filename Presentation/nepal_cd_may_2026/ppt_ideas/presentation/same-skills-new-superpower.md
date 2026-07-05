# Same Skills, New Superpower: Building Cloud Infrastructure with Code

## Presentation Structure
- **Talk:** 15–20 minutes (Slides 1–20)
- **Demo:** 10–15 minutes (Slides 21–24)
- **Total:** ~30 minutes

---

## Slide 1: Title Slide

**On Slide:**
> **Same Skills, New Superpower**
> Building Cloud Infrastructure with Code
>
> [Your Name] | Developer Advocate, AWS
> [Event Name] | [Date]

**Speaker Notes:**
Welcome everyone. Before we jump in — quick show of hands. How many of you have deployed something to the cloud? [hands up] Great. How many of you did it by clicking through a web console? [laughs] Yeah, me too. And how many of you would love it if setting up infrastructure was as easy as pushing code? That's what the next 30 minutes are about. Let's go.

---

## Slide 2: About Me

**On Slide:**
> **[Your Name]**
> Developer Advocate, AWS
>
> - [X] years building on AWS
> - Previously: [Your background — e.g., full-stack dev, platform engineer, startup CTO]
> - Built & deployed infrastructure for [context — e.g., production workloads, startups, enterprise teams]
> - [Optional: community involvement, open source, blog, YouTube]
>
> *I've clicked through the console. I've written the YAML. I've done it all three ways.*

**Speaker Notes:**
Quick intro — I'm [name], Developer Advocate at AWS. Before this role, I was [your background — e.g., a full-stack developer / platform engineer / etc.]. I've been building on AWS for [X] years. I've set up infrastructure by hand, I've written thousands of lines of CloudFormation, I've used CDK and Terraform in production. So what I'm sharing today isn't theory — it's what I've lived. And I started exactly where you might be right now — knowing how to write code but not knowing how to get it into the cloud reliably. That's what today is about.

---

## Slide 3: Agenda

**On Slide:**
> **You'll walk away knowing:**
> What IaC is, when to use CloudFormation vs CDK vs Terraform, and how to get started today.
>
> 1. Why Infrastructure as Code matters (5 min)
> 2. CloudFormation, CDK & Terraform — explained (10 min)
> 3. Live demo — same task, three tools, built with Kiro (10–12 min)
> 4. How to choose + Q&A (3 min)
>
> 💡 *No deep AWS knowledge required. If you can read code, you're good.*

**Speaker Notes:**
Here's what you'll get out of the next 30 minutes: you'll understand what Infrastructure as Code is, you'll know the difference between CloudFormation, CDK, and Terraform — and when to reach for each — and you'll see how to get started today. First, I'll show you why IaC exists through a scenario you'll probably recognize. Then we'll look at the three tools. Then the fun part — a live demo where I use Kiro, an AI-powered IDE from AWS, to generate and deploy infrastructure using all three. We'll wrap with how to choose and your questions. And just so we're clear — you don't need deep AWS knowledge for this. If you can read code, you'll follow along fine.

---

## Slide 4: The Scenario (Hook)

**On Slide:**
> You built an app. It works locally.
> Now you need:
> - A server
> - A database
> - Networking
> - Permissions
>
> 🖱️ *Click... click... click...*

**Speaker Notes:**
Let's start with something familiar. You've built your app. It runs great on your machine. Now you need to get it into the cloud. So you log into the console, you create a server, you set up a database, you configure networking, you attach permissions. Lots of clicking. And it works! ...for now.

---

## Slide 5: The Problem — Day 2

**On Slide:**
> "Can you set up the same thing for staging?"
>
> "What changed since last week?"
>
> "Who deleted the security group?"

**Speaker Notes:**
Then day 2 happens. Your manager asks for a staging environment. A teammate asks what changed. Something breaks and nobody knows who touched what. Sound familiar? This is the exact same problem we solved in application development years ago. We solved it with version control, code review, and automation. Infrastructure just hasn't caught up yet — until now.

---

## Slide 6: What You Already Know

**On Slide:**
> As developers, you already:
> - Write code in files
> - Use version control (git)
> - Review changes (pull requests)
> - Automate repetitive tasks (CI/CD)
>
> **What if infrastructure worked the same way?**

**Speaker Notes:**
Here's the thing — you already know how to solve this. You write code in files. You track changes with git. You review each other's work through pull requests. You automate with CI/CD. What if your infrastructure worked exactly the same way? That's Infrastructure as Code. It's not a new skill — it's your existing skills applied to a new domain.

---

## Slide 7: Infrastructure as Code — One Sentence

**On Slide:**
> **Infrastructure as Code (IaC):**
> Define your cloud resources in files, deploy them with a command.

**Speaker Notes:**
Infrastructure as Code in one sentence: you define your cloud resources in files, and deploy them with a command. That's it. Instead of clicking through a console, you describe what you want in a file — a server, a database, a network — and a tool creates it for you. Reproducibly. Every single time.

---

## Slide 8: Why IaC Matters

**On Slide:**
> | Without IaC | With IaC |
> |---|---|
> | Manual setup | Automated |
> | "It was working yesterday" | Git blame |
> | Snowflake environments | Identical copies |
> | Documentation gets stale | Code IS the documentation |

**Speaker Notes:**
Let me make this concrete. Without IaC, setup is manual and error-prone. With IaC, it's automated and repeatable. Without IaC, when something breaks you're guessing. With IaC, you git blame and see exactly what changed. Without IaC, every environment is a unique snowflake. With IaC, staging is a carbon copy of production. And the best part — your code IS your documentation. It never gets stale because it's what's actually deployed.

---

## Slide 9: Three Tools, One Goal

**On Slide:**
> **AWS CloudFormation** — YAML/JSON templates
> **AWS CDK** — Your programming language (TypeScript, Python, Java...)
> **Terraform** — HCL, multi-cloud
>
> All three: file → deploy → infrastructure exists

**Speaker Notes:**
On AWS, you have three main options for IaC. CloudFormation uses YAML or JSON templates — it's AWS-native and has been around the longest. AWS CDK lets you use your actual programming language — TypeScript, Python, Java, Go — and generates CloudFormation under the hood. And Terraform uses its own language called HCL and works across multiple cloud providers. All three follow the same core idea: you write a file, you run a command, infrastructure exists.

---

## Slide 10: Section Divider — CloudFormation

**On Slide:**
> **AWS CloudFormation**
> The OG of AWS IaC
>
> 📄 YAML/JSON → ☁️ AWS Resources

**Speaker Notes:**
Let's start with CloudFormation — the original. It's been around since 2011 and it's AWS's native provisioning engine. CDK, SAM, and Service Catalog all generate CloudFormation templates under the hood — so understanding it gives you a foundation for everything else.

---

## Slide 11: CloudFormation — How It Works

**On Slide:**
> 1. You write a **template** (YAML or JSON)
> 2. You submit it to CloudFormation
> 3. CloudFormation creates a **stack** (your resources)
> 4. Change the template → update the stack
> 5. Delete the stack → resources cleaned up
>
> ```yaml
> Resources:
>   MyBucket:
>     Type: AWS::S3::Bucket
> ```

**Speaker Notes:**
The mental model is simple. You write a template — that's your file describing what you want. You submit it to CloudFormation, and it creates what's called a stack — that's your collection of resources. Want to change something? Update the template, submit again. Done with everything? Delete the stack and all resources get cleaned up. No orphaned resources. Here's the simplest possible example — an S3 bucket in 3 lines of YAML.

---

## Slide 12: CloudFormation — Strengths & Trade-offs

**On Slide:**
> ✅ Native to AWS — no extra tools
> ✅ Handles rollback automatically
> ✅ Tracks every resource it creates
>
> ⚠️ YAML can get verbo
> ⚠️ No loops, limited logic
> ⚠️ Learning curve for complex templates

**Speaker Notes:**
CloudFormation's biggest strength is that it's native — nothing extra to install, AWS manages the state for you, and if something fails mid-deploy it rolls back automatically. The trade-off is that YAML gets verbose fast. You can't write a for-loop. For simple infrastructure it's great. For complex setups with lots of repetition, you'll feel the friction. And that's exactly why CDK was created.

---

## Slide 13: Section Divider — AWS CDK

**On Slide:**
> **AWS CDK**
> Infrastructure in your language
>
> 🧑‍💻 TypeScript/Python/Java → 📄 CloudFormation → ☁️ AWS

**Speaker Notes:**
Enter the AWS CDK — the Cloud Development Kit. The idea is simple: what if you could define infrastructure using the same language you write your app in?

---

## Slide 14: CDK — How It Works

**On Slide:**
> 1. Write infrastructure in TypeScript, Python, Java, Go, or C#
> 2. CDK **synthesizes** it into a CloudFormation template
> 3. CloudFormation deploys it
>
> ```typescript
> new s3.Bucket(this, 'MyBucket');
> ```

**Speaker Notes:**
CDK sits on top of CloudFormation. You write code in your language — TypeScript, Python, whatever you prefer. CDK compiles that into a CloudFormation template — this step is called synthesis. Then CloudFormation deploys it like normal. So you get the full power of a programming language — loops, conditionals, abstractions, type checking — but CloudFormation still handles the actual deployment. Look at that — one line of TypeScript, and you get an S3 bucket with sensible defaults.

---

## Slide 15: CDK — Strengths & Trade-offs

**On Slide:**
> ✅ Use your existing language — loops, functions, classes
> ✅ High-level constructs (smart defaults)
> ✅ IDE autocomplete & type safety
>
> ⚠️ Adds a layer of abstraction
> ⚠️ Still CloudFormation under the hood (same limits)
> ⚠️ Need to understand what it generates

**Speaker Notes:**
CDK shines when you want to use real programming constructs. Need 10 similar resources? Write a loop. Want reusable patterns? Write a class. Your IDE gives you autocomplete and catches errors before deploy. The trade-off is that it's an abstraction layer. When something goes wrong, you might need to look at the generated CloudFormation to debug. And CloudFormation's limits still apply — like the 500 resource cap per stack. But for most teams, the productivity gain is massive.

---

## Slide 16: Section Divider — Terraform

**On Slide:**
> **Terraform**
> by HashiCorp
>
> One tool, any cloud
>
> 📄 HCL → ☁️ AWS / Azure / GCP / ...

**Speaker Notes:**
Now let's talk about Terraform — built by HashiCorp. Terraform takes a different approach. It's not tied to any single cloud provider.

---

## Slide 17: Terraform — How It Works

**On Slide:**
> 1. Write a `.tf` file in HCL (HashiCorp Configuration Language)
> 2. `terraform plan` — preview what will change
> 3. `terraform apply` — make it happen
> 4. State file tracks what exists
>
> ```hcl
> resource "aws_s3_bucket" "my_bucket" {
>   bucket = "my-unique-bucket"
> }
> ```

**Speaker Notes:**
Terraform uses its own language called HCL — HashiCorp Configuration Language. It's declarative, purpose-built for infrastructure. The workflow has a killer feature: plan before apply. You run terraform plan and it shows you exactly what will be created, changed, or destroyed — before anything happens. Then terraform apply makes it real. Terraform keeps a state file that tracks what it's managing, so it always knows the difference between what you want and what exists.

---

## Slide 18: Terraform — Strengths & Trade-offs

**On Slide:**
> ✅ Multi-cloud — same tool for AWS, Azure, GCP
> ✅ `plan` before `apply` — see changes before they happen
> ✅ Huge ecosystem & community
>
> ⚠️ State file needs to be managed
> ⚠️ New language to learn (HCL)
> ⚠️ Not AWS-native — slight lag on new services

**Speaker Notes:**
Terraform's superpower is multi-cloud. If your team uses AWS and Azure, or might switch later, one tool covers both. The plan command gives you confidence — you see exactly what's about to happen. And the community is enormous — there are providers for almost everything. The trade-offs: you need to manage a state file (usually in S3 or Terraform Cloud). HCL is a new language to learn, though it's simple. And since it's third-party, brand new AWS services might take a few weeks to get Terraform support.

---

## Slide 19: Comparison At a Glance

**On Slide:**
> | | CloudFormation | CDK | Terraform |
> |---|---|---|---|
> | Language | YAML/JSON | TypeScript, Python, etc. | HCL |
> | Scope | AWS only | AWS only | Multi-cloud |
> | State | Managed by AWS | Managed by AWS | You manage it |
> | Best for | AWS-native, simple | Devs who want real code | Multi-cloud teams |

**Speaker Notes:**
Here's the quick comparison. CloudFormation is YAML, AWS-only, state managed for you — great for straightforward AWS setups. CDK is your programming language, still AWS-only under the hood, but way more expressive — ideal if you're a developer who thinks in code. Terraform is HCL, works across clouds, but you manage state yourself — best if you're multi-cloud or want one tool for everything. There's no wrong answer here. It depends on your team, your stack, and your preferences.

---

## Slide 20: How to Choose (Decision Tree)

**On Slide (visual flowchart — build this as shapes/arrows in PowerPoint):**

```
                    ┌─────────────────────┐
                    │  Do you need to     │
                    │  support multiple   │
                    │  cloud providers?   │
                    └────────┬────────────┘
                       │           │
                      YES          NO
                       │           │
                       ▼           ▼
              ┌──────────────┐   ┌─────────────────────┐
              │  TERRAFORM   │   │  Do you want to use │
              │              │   │  a real programming │
              │  HCL         │   │  language?          │
              │  Multi-cloud │   └────────┬────────────┘
              │  Plan first  │       │           │
              └──────────────┘      YES          NO
                                     │           │
                                     ▼           ▼
                            ┌──────────────┐  ┌──────────────┐
                            │  AWS CDK     │  │ CLOUDFORMATION│
                            │              │  │              │
                            │  TypeScript  │  │  YAML/JSON   │
                            │  Python/Java │  │  AWS-native  │
                            │  Smart       │  │  Explicit    │
                            │  defaults    │  │  control     │
                            └──────────────┘  └──────────────┘

              💡 You can mix them. Many teams do.
```

**Design notes for PowerPoint:**
- Use 3 rounded rectangles (one per tool) with the tool's color/logo
- Use diamond shapes for the two decision questions
- Connect with arrows labeled YES/NO
- Keep the "💡 You can mix them" as a footnote at the bottom
- Total shapes: 2 diamonds + 3 rectangles + arrows

**Speaker Notes:**
Let me make this simple with a decision tree. First question: do you need multi-cloud? If yes, Terraform — it's the only one here that works across AWS, Azure, and GCP. If no, next question: do you want to write infrastructure in a real programming language with loops, types, and IDE support? If yes, CDK — it's built for developers. If you prefer declarative templates with explicit control over every property, CloudFormation is solid and requires no extra tooling. And the footnote here is real — many teams use more than one. There's no rule that says you pick one forever.

---

## Slide 21: Demo Introduction

**On Slide:**
> **Demo Time** 🚀
>
> One task, three tools, one AI-powered IDE:
> **Create an S3 bucket + a Lambda function**
>
> Using **Kiro** to generate & deploy:
> CloudFormation → CDK → Terraform
>
> 🧠 *Kiro — AI-powered IDE by AWS*
> *Natural language → Code → Deploy — all in one place*

**Speaker Notes:**
Alright, demo time. I'm going to create the same infrastructure three ways — but I'm not writing code from scratch. I'm using Kiro, an AI-powered IDE from AWS. You describe what you want in natural language, Kiro generates the code, and you deploy it right from the same environment. Think of it as pair programming with an AI that knows AWS. Let me switch over.

---

## Slide 22: Demo — CloudFormation with Kiro

**On Slide:**
> **CloudFormation + Kiro**
>
> Prompt → Code → Deploy
>
> *"Create a CloudFormation template with an S3 bucket and a Lambda function"*

**Speaker Notes:**
Okay, I have Kiro open. I'll prompt: "Create a CloudFormation template with an S3 bucket and a Lambda function with Python 3.12 runtime that returns Hello from CFN." There — full YAML template generated. Bucket, Lambda, IAM role, permissions — all correct. I didn't have to remember the resource type syntax or the role trust policy. Now I'll ask Kiro to deploy it. It runs the CLI command in the integrated terminal. Stack created. Prompt to deployed in under a minute.

---

## Slide 23: Demo — CDK with Kiro

**On Slide:**
> **CDK + Kiro**
>
> Prompt → TypeScript → Synth → Deploy
>
> *"Create a CDK stack with an S3 bucket and a Lambda function"*

**Speaker Notes:**
Same task, CDK. Prompt: "Create a CDK stack in TypeScript with an S3 bucket and a Lambda function that returns Hello from CDK." Notice how much shorter the generated code is — Kiro knows CDK conventions, uses high-level constructs, skips what CDK handles automatically. The IAM role? Implicit. Type safety? Built in. "Deploy this CDK stack." Kiro runs `cdk deploy`, synthesizes to CloudFormation, deploys. Same result, less code, guardrails included.

---

## Slide 24: Demo — Terraform with Kiro

**On Slide:**
> **Terraform + Kiro**
>
> Prompt → HCL → Plan → Apply
>
> *"Create Terraform config with an S3 bucket and a Lambda function"*

**Speaker Notes:**
Finally, Terraform. Same prompt pattern: "Create a Terraform configuration with an S3 bucket and a Lambda function." Kiro generates the HCL — and it's more explicit: IAM role, policy attachment, provider block all included. Kiro knows Terraform requires these. "Run terraform plan." Look — 4 resources will be created, nothing happened yet. "Run terraform apply." Done.

Same task, three tools, all generated and deployed through Kiro. You saw the differences in verbosity, explicitness, and workflow — but in every case, Kiro handled the syntax so you could focus on what you actually need built.

---

## Slide 25: Recap

**On Slide:**
> **You already have the skills.**
>
> - IaC = your dev workflow applied to infrastructure
> - CloudFormation = declarative YAML, AWS-native
> - CDK = your language, smart defaults
> - Terraform = multi-cloud, plan-before-apply
>
> Start with any one. You can't go wrong.

**Speaker Notes:**
Let's wrap up. You already have the skills for this — version control, code review, automation — that's IaC. CloudFormation gives you a solid AWS-native foundation. CDK lets you use the language you already love. Terraform gives you multi-cloud flexibility. And tools like Kiro accelerate your inner development loop — you describe what you need, get working IaC code, and validate it by deploying to a dev or sandbox account in seconds. Once it works, you commit it and let your CI/CD pipeline handle staging and production with proper reviews and gates. Kiro gets you to "ready to commit" faster — it doesn't replace your deployment pipeline. Pick whichever IaC tool feels natural, start small, and you'll never want to go back to clicking.

---

## Slide 26: Resources & Next Steps

**On Slide:**
> **Get started today:**
> - 🔗 kiro.dev — AI-powered IDE
> - 🔗 docs.aws.amazon.com/cloudformation
> - 🔗 docs.aws.amazon.com/cdk
> - 🔗 developer.hashicorp.com/terraform
> - 🔗 cdkworkshop.com
>
> **[Your contact / social links]**
>
> Questions?

**Speaker Notes:**
Here are the links to get started. First — Kiro, the tool you just saw me use. It's free to try and it works with all three IaC tools we covered. The CDK Workshop at cdkworkshop.com is great for hands-on learning. CloudFormation and Terraform docs both have excellent getting-started tutorials. I'll share these slides after the talk. Now — questions? I'd love to hear what you're building and which tool caught your eye.

---

## Timing Guide

| Section | Slides | Time |
|---|---|---|
| Title, About Me, Agenda | 1–3 | 2 min |
| Hook & Problem | 4–6 | 3 min |
| What is IaC | 7–8 | 2 min |
| Three tools overview | 9 | 1 min |
| CloudFormation deep dive | 10–12 | 3 min |
| CDK deep dive | 13–15 | 3 min |
| Terraform deep dive | 16–18 | 3 min |
| Comparison & choosing | 19–20 | 2 min |
| Demo (all three) | 21–24 | 10–12 min |
| Recap & Q&A | 25–26 | 3 min |
| **Total** | | **~30 min** |
