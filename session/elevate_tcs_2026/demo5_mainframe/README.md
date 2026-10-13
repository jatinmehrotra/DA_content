# Demo 5 - Mainframe analysis (WALKTHROUGH - not live)

A tiny COBOL codebase: one program, one copybook, one JCL job. AWS Transform analyzes
it - dependency graph, complexity, and business-logic extraction into plain-English docs.

## IMPORTANT: this is a WALKTHROUGH, not a live run
In setup we found the mainframe agent does NOT start with a simple zip upload like .NET.
It first asks for an objective (assess-and-reimagine / reimagine / custom) and then
requires you to **configure an Amazon Neptune cluster** in your account to store
artifacts about the legacy system. Standing up Neptune is real infra work - not a
live-demo thing the night before.

So: present this as a narrated walkthrough (like VMware). Be honest with the audience -
"this one needs a Neptune cluster behind it, so here's a real example rather than a
live run." The breadth point still lands.

(A zip of this codebase was prepared at `../demo5_mainframe.zip` in case you ever wire
up Neptune and want to upload it - but it is NOT the stage path.)

## Files
- `src/ORDERRPT.cbl`  - COBOL program that totals orders and flags large ones
- `copybook/ORDREC.cpy` - record layout (copybook)
- `jcl/ORDERRPT.jcl`  - JCL job that runs the program

## What to narrate
- The dependency graph: program -> copybook -> JCL (real edges to show).
- Complexity assessment.
- Business logic extracted into readable English (the large-order flagging rule).

## The line
"Remember that 2am COBOL job I was scared of? This is where the agent reads it
and tells me, in plain English, what it actually does."

Do NOT promise a finished Java app - the refactor is long-running. Lean on the
dependency graph; it looks great on screen.
