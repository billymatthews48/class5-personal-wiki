# Optional feature check: explicit memory and drafts in chat

Local, `gemma4:e4b-it-q4_K_M`. Script: [scripts/test_memory_and_drafts.ps1](../../scripts/test_memory_and_drafts.ps1).
Output of the final run: [memory-and-drafts.log](memory-and-drafts.log).

## What the feature does

- `/remember TEXT` appends a dated line to `vault/memory/Chat Memory.md`. Nothing is saved unless I type the command.
- Remembered lines are added to Quill's chat instructions, labelled "user-stated, NOT verified notes".
- `/draft` saves Quill's last reply to `vault/drafts/` as a generated draft.
- Both folders are in the vault for browsing but outside `raw/`. The retrieval index only covers `raw/`, so ask and search
  cannot use them as evidence.

## Two problems this test found, and the fixes

1. **The command was not recognised.**
   - On the first attempt PowerShell prefixed the piped input with a byte-order mark.
   - The line went to Gemma as ordinary chat, and Gemma replied "Okay, I've logged that" although nothing was saved.
   - Fix in `wiki/cli.py`: strip the mark, and reject unknown `/commands` with an error instead of sending them to the model.
2. **A citation with no source.**
   - On the second attempt the memory worked, but Quill wrote "[1]" after the remembered fact although no notes were searched.
   - Fix in `wiki/harness.py`: citation markers are removed from a chat reply when no retrieval happened that turn.
   - The reply streams to the screen before this check, so the live text can still show the marker. The saved transcript
     and the conversation history hold the corrected reply.

## Result of the final run

| Check | Result |
|---|---|
| `/remember` saves the line to `memory/Chat Memory.md` | yes |
| After `/reset`, Quill still answers "What revision method do I prefer?" from memory | yes |
| `/draft` saves the last reply to `drafts/` | yes |
| Unknown command (`/savememory`) is rejected, not sent to Gemma | yes |
| `ask` with the same question returns insufficient evidence (best similarity 0.32 < 0.45) | yes |
| `search` returns only `raw/` passages, not the memory or the draft | yes |
