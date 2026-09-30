---
subject_key: networking-tracker
wiki_id: subj-networking-tracker
topic: Projects
source_count: 1
generated_by: gemma4:e4b-it-q4_K_M
generated: '2026-09-30'
reviewed: true
---
# Secure Networking Tracker

Billy developed the Secure Networking Tracker, a private, per-user contact list designed for networking purposes, initially for CS Berkeley. The project implementation heavily relied on enforcing user scoping using Postgres Row Level Security, ensuring data isolation between users.

## Key ideas
- The contact list is private and scoped to the signed-in user, enforced by Postgres Row Level Security. ([[raw/github/Assignment-1/README.md|Assignment-1 / README]])
- The application includes functionality for user sign up, sign in, and sign out. ([[raw/github/Assignment-1/README.md|Assignment-1 / README]])
- Users can create, edit, and delete contacts, with changes persisting upon page refresh. ([[raw/github/Assignment-1/README.md|Assignment-1 / README]])
- The system validates input, showing errors when required fields like name are left blank. ([[raw/github/Assignment-1/README.md|Assignment-1 / README]])
- The design guarantees that two separate user accounts can be viewed side-by-side, each showing only its own contacts. ([[raw/github/Assignment-1/README.md|Assignment-1 / README]])

## Related
- [[Career Networking]]: The app tracks networking contacts; the personal development notes explain why and how to build that network.
- [[Custom LLM Training]]: Both are Billy's GitHub software projects, documented through their READMEs.

## Sources
- [[raw/github/Assignment-1/README.md|Assignment-1 / README]]

## My Notes

