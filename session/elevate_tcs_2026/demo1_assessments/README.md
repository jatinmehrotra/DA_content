# Demo 1 - Assessments (LIVE)

**What to show:** upload this inventory, let AWS Transform produce right-sizing + a TCO
business case, then generate the executive deliverables (PPT + PDF + XLS).

## Where this runs
NOT the Service management page. Open the **Web application URL** shown on
AWS Transform > Service management, sign in (IAM-only access is enabled), and
work inside the web app. Workspace used for this talk: **elevate-tcs**.

## Steps on stage
1. `aws login`
2. In the web app, create a job and start a **Migration assessment** (chat-driven -
   you just type that you want an assessment).
3. Upload `server_inventory.csv`. The agent auto-detects the format.
4. It discovers the estate (for this file: **10 servers, 10 storage volumes,
   10 relationships**) and shows a discovery summary.
5. HUMAN-IN-THE-LOOP: it configures a scenario (EC2 config, Reserved Instances,
   shared tenancy, sustainability) and asks **"Ready to proceed with this scenario?"**
   -> answer **yes**. Point this out: "it checks with me before running - that's the
   human in the loop."
6. It generates the business case (EC2 compute + EBS storage assessment, right-sizing, TCO).
7. Ask ONE live chat question for effect, e.g. "Why that instance for db-prod-01?"
   or "What if I use Graviton where supported?"
8. Generate deliverables: it produces a downloadable ZIP
   (`Initial_Migration_Assessment_<timestamp>.zip`) containing the exec **PPT**,
   the **PDF** report, and an **XLS** of discovered data with target mappings.
   Click **Download all**.

## Good to know (learned in setup)
- There is also an `error_file.csv` in the output - it flags rows with incomplete /
  unparsed data. Normal for a tiny sample. If asked: "it lists rows with data-quality
  gaps so you can clean them up."
- Assessments also detect SQL Server and Apache Kafka clusters (Kafka -> Amazon MSK
  Express), not just servers - good breadth answer if asked.
- Peek inside the downloaded zip BEFORE the talk so you know what's in it; don't open
  it for the first time live.

## The line
"Before you migrate anything, this answers: should I, and what will it cost - and it
builds the leadership deck for you. I have mixed feelings about my own job security."

10 servers, mixed Windows/RHEL, prod + dev. Small on purpose so it processes fast.
