# Demo 3 - Custom code transform (ANCHOR, LIVE)

A tiny Java 8 app. The AWS Transform CLI (atx) upgrades it to Java 17, producing a
clean, readable diff - the money shot of the talk. PROVEN WORKING in setup
(mvn clean verify -> BUILD SUCCESS).

## One-time setup (already done on this machine)
- Installed via Homebrew: `brew install openjdk@17 maven`
- Symlinked the JDK + set JAVA_HOME (java 17 + mvn both resolve now)
- Installed the ATX CLI: `curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash`
  (version 3.18.0). Verify: `atx --version`

## Steps on stage
1. `aws login`
2. (Optional) show the starting code so the diff lands later:
   `OrderReport.java` / `Order.java` - note java.util.Date, Iterator loop, string concat.
3. `cd ~/Desktop/DA_content/session/elevate_tcs_2026/demo3_atx_java`
4. `atx` (interactive). Tell it: "Upgrade this Java 8 project to Java 17."
   When it asks, give:
   - Path: `.` (or the full path above)
   - Build command: `mvn clean verify`   (we have Maven + JDK 17 installed)
5. It plans, shows the planned changes, and asks to confirm the target (answer **17**).
   This confirm step IS the human-in-the-loop beat - call it out.
6. It applies the changes, runs `mvn clean verify` (BUILD SUCCESS), and reports COMPLETE.
7. Show the before/after diff - the money shot:
   - pom.xml: `maven.compiler.source/target 8` -> `maven.compiler.release 17`
   - Order.java: `java.util.Date` -> `java.time.LocalDateTime`
   - OrderReport.java: Iterator loop -> enhanced for / `var`, `String.format`, diamond operator

## How ATX leaves the repo (IMPORTANT for a fresh live run)
- ATX commits results to a NEW branch named `atx-result-staging-<timestamp>` off `master`.
  `master` stays at the original Java 8 state.
- To run FRESH on stage: be on `master` first (`git checkout master`;
  `grep -i compiler pom.xml` should show 8).
- Fallback diff is saved at `UPGRADE_DIFF.txt` - if the live run drags, open that
  instead. Generate/refresh it with:
  `git diff master <atx-branch> > UPGRADE_DIFF.txt`
- If you deleted the staging branch for a clean slate, that's fine - a fresh run
  just creates a new one.

## The line
"Natural language in, modern code out. No Stack Overflow tab open, no copying a
2014 answer that's somehow -3 votes but the only one that works."

This is the one that cannot fail - rehearse it, and `aws login` first.
