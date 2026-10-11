# Demo 4 - Windows / .NET modernization (LIVE, small repo)

A tiny .NET Framework 4.7.2 console app. AWS Transform for .NET assesses it and
ports it to cross-platform .NET 8+ that runs on Linux in a container.

## Steps on stage
1. `aws login`
2. AWS Transform console -> Windows / .NET modernization -> new job
3. Connect this repo (push to GitHub first, or upload)
4. Show: assessment report -> transformation plan -> conversion to .NET 8+
5. Call out: TargetFrameworkVersion v4.7.2 -> net8.0, ConfigurationManager ->
   Microsoft.Extensions.Configuration, old .csproj -> SDK-style project

## The line
"The input is just your source code. Off Windows licensing, onto Linux containers."

Scoped to .NET-only (no SQL Server) so it stays fast. Keep a pre-built completed
job open in another tab as a fallback.
