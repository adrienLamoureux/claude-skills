# Stop blocks

Read by every skill of this kit at its stops. Use the Where examples your skill gives.

## Resume block

At every stop (done, waiting for the user, or blocked), write `<DIR>/resume.md` yourself,
replacing the old one, so a later session and the focus-kit inbox know where the run stands:

```
# Resume — <slug>
- Where: <step, from the Where examples your skill gives>
- Did: <one line: what this turn finished>
- Needs: <what the user must do or decide, or nothing>
```

Show it only when the stop has no decision card; the card already says what is needed.

## Decision card

Every stop that waits for the user's choice ends with these five lines, then the question.
One decision per card; a progress note that needs no answer gets no card.

```
Decide: <the choice, in one line>
Recommend: <option> — <one reason>
If wrong: <what breaks and when it would show; name the top unverified risk>
Undo cost: <none, nothing written yet | revert the branch | re-run round n | one-way: why>
On "ok": <exactly what happens next if the user just says ok>
```

The undo cost tells the user where to spend attention: a cheap undo needs a glance, a one-way
step needs a read. Never hide a risk to make the card shorter.
