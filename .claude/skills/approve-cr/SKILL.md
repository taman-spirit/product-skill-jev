---
name: approve-cr
description: Move a CR through the approval board and trigger a PRD version update if approved. Use when user says "approve CR-NNN", "reject CR-NNN", or a decision has been made by the approval board.
---

# Approve/Reject CR

## Approve

Note: Read `_system/active-project.md` to get the current project folder name (e.g., my-projects/PROJ-001-ai-alignment).
If this file does not exist, ask the user: "Which project are you working on?"
All file paths below use [ACTIVE_PROJECT] as the project folder name.

1. Move CR file from `[ACTIVE_PROJECT]/cr/approval-board/` to `[ACTIVE_PROJECT]/cr/approved/`
2. Record the approval decision, board members, and any conditions in the CR file
3. Check if the approval creates new tag conflicts with other PRDs in the current sprint
   - If yes: output conflict warning before proceeding
4. Ask: "CR-NNN is approved. PRD-[X] needs to be updated to v[Y]. Shall I draft the new version?"
5. After PM confirms: trigger the `update-prd` skill
6. Update `[ACTIVE_PROJECT]/cr/cr-log.md`: status "approved - PRD updated to vX.Y"

## Reject

1. Move CR file from `[ACTIVE_PROJECT]/cr/approval-board/` to `[ACTIVE_PROJECT]/cr/rejected/`
2. Record the rejection rationale in the CR file
3. Notify PM: what was rejected and why, and whether it can be resubmitted with changes
4. Update `[ACTIVE_PROJECT]/cr/cr-log.md`: status "rejected"

## Checklist (approve)

- [ ] CR file moved to [ACTIVE_PROJECT]/cr/approved/
- [ ] Approval recorded with date, board members, conditions
- [ ] New tag conflict check run for current sprint
- [ ] PRD updated to new version
- [ ] [ACTIVE_PROJECT]/cr/cr-log.md updated
- [ ] Project milestone updated in [ACTIVE_PROJECT]/
