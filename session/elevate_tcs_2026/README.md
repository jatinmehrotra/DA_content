# AWS Transform - Elevate TCS 2026 - Demo Kit

Four live demo inputs for the 45-min AWS Transform talk (Tue, Oct 13).
Keep everything small on purpose: the point is to show WHAT AWS Transform does,
not to run a production-scale job on stage.

## Before ANY demo
Run `aws login` first (credentials cache to ~/.aws, boto3/CLI pick them up).

## Demo order (matches the deck)
1. demo1_assessments/   - LIVE - upload inventory, get TCO + exec deck
2. (console + chat)     - LIVE - no files, just drive the console
3. demo3_atx_java/      - LIVE - ANCHOR - atx upgrades Java 8 -> 17/21
4. demo4_dotnet/        - LIVE - .NET Framework 4.7.2 -> .NET 8+
5. demo5_mainframe/     - LIVE (analysis only) - COBOL dependency graph + logic extraction
6. (VMware)             - WALKTHROUGH - pre-recorded, no files
7. (continuous mod)     - LIVE nav - pre-populated dashboard, no files

## Fallback plan
For demos 3/4/5, have a pre-run completed job open in another browser tab in case
a live run is slow. Never let a slow job stall the talk.

## Note
demo1 is a Windows/RHEL inventory; demo3 (Java) and demo4 (.NET) are code repos
you should push to GitHub (or upload) so the console can connect to them.
