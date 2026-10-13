# Demo 4 - Windows / .NET modernization (LIVE via Direct Upload)

A tiny .NET Framework 4.7.2 console app. AWS Transform for .NET assesses it and ports
it to cross-platform .NET 8+ that runs on Linux in a container. Assessment PROVEN
WORKING in setup (via Direct Upload).

## USE DIRECT UPLOAD - not the GitHub connector
In setup, the GitHub CodeConnections connector showed "Available" but the ARN FAILED
to validate inside AWS Transform (across multiple connectors). Root cause: the IAM
role AWS Transform uses lacks `codeconnections:UseConnection` (an account/IAM fix,
not worth doing live). So the reliable path is **Direct Upload**:
- A ready zip exists at: `../demo4_dotnet.zip`
  (contains the .sln, .csproj, Program.cs, App.config, AssemblyInfo.cs; build junk excluded)

## Steps on stage
1. `aws login`
2. In the AWS Transform web app, create a job -> **Windows modernization** ->
   **.NET modernization agent**.
3. At "Connect source code", choose **Direct Upload** and drag in `demo4_dotnet.zip`.
   (If the chat offers "Try Direct Upload instead", that's the button.)
4. Discovery + assessment runs. Expected result (from setup):
   **net472 (legacy .NET Framework), Moderate complexity, 1 project, 34 LOC.**
5. To continue: choose "Transform moderate repos (1)" / "All eligible repositories".
   It generates the plan, pauses for approval (human-in-the-loop), then ports to .NET 8.
6. Show: assessment report -> transformation plan -> transformed code on the
   Artifacts tab. Transformed code is written to a NEW branch (original untouched).
7. Call out: TargetFrameworkVersion v4.7.2 -> net8.0, old `.csproj` -> SDK-style,
   `ConfigurationManager` -> `Microsoft.Extensions.Configuration`.

## Good to know
- The full transform takes several minutes. For stage: either kick it off and talk
  over it, or pre-run it and show the finished artifacts. The ASSESSMENT (step 4) is
  the proven, fast part - that alone makes the point.
- The 4 source-code options are: Code Connection (CodeConnections), PAT (token in
  Secrets Manager), S3 zip, and Direct Upload. We use Direct Upload.

## The line
"The input is just your source code. Off Windows licensing, onto Linux containers."

Scoped to .NET-only (no SQL Server) so it stays fast.
