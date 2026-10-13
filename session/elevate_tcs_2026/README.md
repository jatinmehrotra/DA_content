# AWS Transform - Elevate TCS 2026 - Demo Kit

Demo inputs + speaker notes for the 45-min AWS Transform talk (Tue, Oct 13, 2026).
AWS-run event, audience assumed NEW to AWS Transform. Keep demos small on purpose -
the goal is to show WHAT AWS Transform does, not run production-scale jobs on stage.

## Before ANY demo
Run `aws login` first (caches creds to ~/.aws; the CLI/console pick them up).

## Files
- `SPEAKER_NOTES.md`  - per-slide narration + Q&A prep (companion to the deck)
- `AWS Transform Talk.pptx` - the 17-slide deck
- `demo1_assessments/` - inventory CSV for the Assessments demo
- `demo3_atx_java/`    - Java 8 app for the ATX anchor demo
- `demo4_dotnet/` + `demo4_dotnet.zip` - .NET Framework app (upload the zip)
- `demo5_mainframe/` + `demo5_mainframe.zip` - COBOL codebase (walkthrough)
- `GITHUB_PUSH.md`    - git notes (optional; Direct Upload is the chosen path)

## Demo line-up (5 stops - matches the deck)
1. demo1_assessments/  - LIVE - upload inventory -> TCO + exec deck (PROVEN)
2. (console + chat)    - LIVE - no files, just drive the web app
3. demo3_atx_java/     - LIVE - ANCHOR - atx upgrades Java 8 -> 17 (PROVEN, builds clean)
4. demo4_dotnet/       - LIVE via DIRECT UPLOAD - .NET Framework 4.7.2 -> .NET 8 (assessment PROVEN)
5. demo5_mainframe/    - WALKTHROUGH - needs an Amazon Neptune cluster, so narrate a real example

VMware and continuous modernization are NOT demoed - they stay on the deck's "five
areas" map and recap as capabilities AWS Transform also offers.

## Key gotchas learned in setup
- **Jobs run in the web app**, not the Service management page. Open the Web
  application URL from Service management and sign in (IAM-only access enabled).
- **.NET: use Direct Upload, not GitHub.** The CodeConnections connector showed
  "Available" but its ARN failed to validate in AWS Transform (missing IAM
  `codeconnections:UseConnection`). Direct Upload (drag the zip) is reliable.
- **Mainframe needs Amazon Neptune** - not a quick zip upload - so it's a walkthrough.
- **ATX (Java) needs JDK 17 + Maven locally** (installed via Homebrew). It commits
  results to a new `atx-result-staging-*` branch off `master`; reset to `master` to
  re-run fresh. Fallback diff saved in `demo3_atx_java/UPGRADE_DIFF.txt`.

## Fallback plan
For demos 3 and 4, keep a pre-run completed result handy in another tab in case a live
run is slow. Never let a slow job stall the talk.

Each demo folder has its own README with on-stage steps, the line to say, and gotchas.
