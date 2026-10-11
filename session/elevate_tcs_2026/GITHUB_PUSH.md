# Pushing the demo repos to GitHub

Two repos need to be on GitHub so the AWS Transform console/CLI can connect:
- demo3_atx_java   (the ATX anchor demo)
- demo4_dotnet     (the .NET modernization demo)

demo1_assessments (CSV upload) and demo5_mainframe (folder upload) do NOT need a
repo - you upload them directly in the console.

## Option A - GitHub CLI (fastest, if `gh` is installed)
Run from each repo folder:

    cd demo3_atx_java
    git init
    git add .
    git commit -m "AWS Transform demo - Java 8 app for version-upgrade"
    gh repo create elevate-tcs-atx-java --private --source=. --push

    cd ../demo4_dotnet
    git init
    git add .
    git commit -m "AWS Transform demo - .NET Framework 4.7.2 app"
    gh repo create elevate-tcs-dotnet --private --source=. --push

## Option B - plain git (create the empty repo on github.com first)
    cd demo3_atx_java
    git init
    git add .
    git commit -m "AWS Transform demo - Java 8 app for version-upgrade"
    git branch -M main
    git remote add origin https://github.com/<you>/elevate-tcs-atx-java.git
    git push -u origin main

    # repeat for demo4_dotnet with its own remote URL

## Notes
- Private repos are fine - connect them via your GitHub account in the console.
- Each repo has a .gitignore so build output (target/, bin/, obj/) stays out.
- Secret scan run on 2026-10-12: both repos clean (the 12-digit match in
  OrderApp.sln is just a Visual Studio project GUID, not an AWS account ID).
