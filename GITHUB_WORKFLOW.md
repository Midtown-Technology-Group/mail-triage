# GitHub Follow-Up Workflow

Issue #1: [Package the GitHub follow-up workflow into a repeatable daily-driver loop](https://github.com/Midtown-Technology-Group/mail-triage/issues/1)

## The Workflow

A daily operator pattern for clearing GitHub notification mail efficiently:

1. **Inspect** GitHub notification mail in inbox
2. **Decide** — mark read, archive, or create follow-up task
3. **Act** — execute the decision via `mail-triage` and `todo`

## Heuristic: Oldest-First GitHub Notification Cleanup

```powershell
# Step 1: Review oldest GitHub notifications first
.\invoke.ps1 inbox --unread-only --limit 50 |
    Where-Object { $_.sender -like "*github*" -or $_.subject -like "*[GitHub]*" } |
    Sort-Object receivedTime

# Step 2: For each GitHub notification, decide:
#   - Mark read: Bot chatter, already-handled CI, noise
#   - Archive: Reviewed but no action needed
#   - To Do: Requires actual follow-up
```

## Decision Framework

| Type | Pattern | Action |
|------|---------|--------|
| **Bot chatter** | Dependabot, automated checks, notifications with no human action needed | `.\invoke.ps1 read <id>` |
| **Reviewed/No action** | PRs you're not involved in, FYI notifications | `.\invoke.ps1 move <id> --to archive` |
| **Needs follow-up** | Reviews requested, failed CI on your PRs, issues to respond to | Create To Do task |

## Daily Recipe (Scriptable)

```powershell
# morning-cleanup.ps1 — GitHub notification triage

$env:MAIL_TRIAGE_SCOPES = 'Mail.ReadWrite'

# 1. List GitHub notifications
$githubMail = .\invoke.ps1 --output json inbox --unread-only --limit 25 |
    ConvertFrom-Json |
    Where-Object { $_.senderDisplayName -match 'GitHub|noreply@github.com' } |
    Sort-Object receivedDateTime

# 2. Interactive triage
foreach ($msg in $githubMail) {
    Write-Host "`n[$($msg.id)] $($msg.subject)" -ForegroundColor Cyan
    Write-Host "   From: $($msg.senderDisplayName) | $($msg.receivedDateTime)" -ForegroundColor Gray

    $action = Read-Host "[R]ead, [A]rchive, [T]odo, [S]kip?"

    switch ($action.ToLower()) {
        'r' { .\invoke.ps1 read $msg.id; Write-Host "Marked read" -ForegroundColor Green }
        'a' { .\invoke.ps1 move $msg.id --to Archive; Write-Host "Archived" -ForegroundColor Yellow }
        't' {
            # Create follow-up task
            $subject = $msg.subject -replace '^(\[GitHub\]|Re: )+', ''
            .\..\todo\invoke.ps1 add item "GitHub: $subject" --list "Work" --star
            .\invoke.ps1 read $msg.id
            Write-Host "Created To Do + marked read" -ForegroundColor Magenta
        }
        's' { Write-Host "Skipped" -ForegroundColor Gray }
    }
}

Write-Host "`nTriage complete. Check your To Do list for follow-ups." -ForegroundColor Cyan
```

## Acceptance Criteria

- [ ] Define the exact safe heuristic for oldest-first cleanup (documented above)
- [ ] Document when to mark read vs archive vs create To Do (decision table above)
- [ ] Run the loop on real inbox batches at least 3 times
- [ ] Capture friction points and refine commands/docs

## Nice-to-Haves (Future)

- [ ] Compact scriptable command recipe for daily use (see `morning-cleanup.ps1` above)
- [ ] Clearer archive-vs-read guidance for bot chatter vs actionable failures
- [ ] Possible integration: `mail-triage github-triage` subcommand?

## Reporting Results

Add your findings as comments on Issue #1, or open a PR with improvements to:
- This `GITHUB_WORKFLOW.md` document
- README.md with refined usage examples
- New commands or flags if friction shows up
