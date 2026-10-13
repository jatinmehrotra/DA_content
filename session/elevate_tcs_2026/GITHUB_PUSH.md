# Source code into AWS Transform - what we actually use

TL;DR: for this talk, **.NET uses Direct Upload (a zip), not a GitHub connector.**
Keep this file for reference, but you do NOT need to push repos for the demos.

## Why not the GitHub connector
In setup, we created an AWS CodeConnections GitHub connection (`tcs-transform`) and it
showed **Available** - but AWS Transform still FAILED to validate its ARN
("Dynamic import failed" / connector ARN failing to validate). Root cause: the IAM
role AWS Transform uses was missing `codeconnections:UseConnection`
(formerly `codestar-connections:UseConnection`). That is an account/IAM policy fix,
not something to debug live. So we switched to Direct Upload.

## What each demo actually uses for source
- demo1_assessments - upload `server_inventory.csv` directly in the Assessments job
- demo3_atx_java    - LOCAL repo; atx runs on the folder on disk (no push needed)
- demo4_dotnet      - **Direct Upload**: drag `demo4_dotnet.zip` into the chat
- demo5_mainframe   - walkthrough (needs Neptune); zip exists but is not the stage path

## The 4 source-code options AWS Transform offers (for reference)
1. Code Connection - AWS CodeConnections (GitHub/GitLab/Bitbucket/Azure Repos)
2. PAT - personal access token stored in AWS Secrets Manager
3. S3 - a code zip in an S3 bucket
4. Direct Upload - drag a zip into the chat   <- we use this

## If you ever want the GitHub connector to work (post-event)
Grant the AWS Transform execution role `codeconnections:UseConnection` on the
connection ARN, in the same Region as the job (us-east-1). The connection ARN from
setup was:
  arn:aws:codeconnections:us-east-1:345063271679:connection/7b75ceef-ca05-4561-bf2f-7d9e5bbf5d4a

## Making the demo zips (already created)
demo4_dotnet.zip and demo5_mainframe.zip are already in this folder. To regenerate,
zip the folder contents with a top-level folder inside the archive and exclude build
output (bin/, obj/, .vs/, target/, .git/).
