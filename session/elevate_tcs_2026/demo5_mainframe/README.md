# Demo 5 - Mainframe analysis (LIVE - analysis only)

A tiny COBOL codebase: one program, one copybook, one JCL job. AWS Transform
analyzes it - dependency graph, complexity, and business-logic extraction into
plain-English docs. The full COBOL->Java refactor is long-running, so show the
ANALYSIS live and describe the refactor.

## Files
- `src/ORDERRPT.cbl`  - COBOL program that totals orders and flags large ones
- `copybook/ORDREC.cpy` - record layout (copybook)
- `jcl/ORDERRPT.jcl`  - JCL job that runs the program

## Steps on stage
1. `aws login`
2. AWS Transform console -> Mainframe -> new analysis job
3. Upload this folder
4. Show: the dependency graph (program -> copybook -> JCL), complexity assessment,
   and the business logic extracted into readable English

## The line
"Remember that 2am COBOL job I was scared of? This is where the agent reads it
and tells me, in plain English, what it actually does."

Do NOT promise a finished Java app live - the refactor takes too long. Lean on
the dependency graph; it looks great on screen.
