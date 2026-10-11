# Demo 3 - Custom code transform (ANCHOR, LIVE)

A tiny Java 8 app. The AWS Transform CLI (atx) upgrades it to a modern Java LTS
(17/21), producing a clean, readable diff - the money shot of the talk.

## Steps on stage
1. `aws login`
2. `atx` (interactive mode)
3. Pick the built-in Java version upgrade transform (Java 8 -> 17 or 21)
4. Point it at this repo
5. Show the before/after diff: java.util.Date -> java.time, Iterator loop -> stream/for-each,
   string concat -> String.format or text block, explicit types -> var

## The line
"Natural language in, modern code out. No Stack Overflow tab open."

Keep it tiny so it finishes while you are still talking. This is the one that
cannot fail - rehearse it, and run `aws login` first.
