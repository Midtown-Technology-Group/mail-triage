# Mail Triage

Windows-first Python/Typer operator CLI for delegated Microsoft 365 mailbox inspection and actions. `src/mail_triage_cli/` owns CLI/service/repository behavior; `tests/` contains corresponding unit tests. `invoke.ps1` additionally requires `MTG_SHARED_AUTH_SRC` pointing to the shared auth `src` directory, or a sibling `mtg-microsoft-auth/src` checkout. Read [README.md](README.md) for auth/scopes, command semantics, and MSI distribution; [GITHUB_WORKFLOW.md](GITHUB_WORKFLOW.md) describes a concrete notification-follow-up use case.

## Development checks

Use Python 3.10+ and an isolated environment: `python -m pip install -e ".[dev]"`, then `python -m pytest`. These commands follow the declared development dependency and pytest configuration, with current tests under `tests/`; a test CI lane was not found in the inspected workflows. For unit tests, verify pagination, output serialization, mailbox targeting, and Graph errors through mocked repository/service seams and synthetic fixtures. The separate operator acceptance in `GITHUB_WORKFLOW.md` asks for three real-inbox batches; perform those only with explicit mailbox/mutation authorization, and report them separately from unit tests.

## Operator boundaries

Default scope is `Mail.ReadBasic`; the shared Microsoft auth app registration stays unchanged. Preserve shared WAM token-cache reuse and account selection. Scope bundles for write/send/shared-mailbox operations are explicit in README; do not expand baseline consent to folder-management scopes without a concrete need.

`inbox` and `senders` inspect mail. `read`/`unread`, `read-matching`, `move`, `delete`, and `send` mutate mail or deliver messages; in particular, `read-matching` is not a read-only listing command. Keep exact mailbox/message IDs and bounded pagination explicit in requests and previews. Sending mail requires direct authorization; a sample workflow or fixture is not authorization.

Never write tokens, message bodies, or customer mailbox contents into source fixtures/logs. Use stable synthetic data and verify `--output json` remains machine-readable. A successful local test does not prove live mailbox access or delivery. Tagged MSI publishing/per-machine installation changes distribution or host state and requires the corresponding release procedure; preserve `invoke.ps1` as the Windows operator entrypoint.

## Secret gate before publication

Before publishing the current PR branch, commit the complete candidate and run
`python3 -I scripts/secret_gate.py --base origin/main` (native Windows: `python -I`). Require exit 0;
missing tooling/authentication, scan errors and skipped scans block publication.
Then run the existing repository gates. Repeat after changing outgoing commits.
Push exactly the scanned HEAD. This PR scan covers the current branch against its
fetched intended base; other refs, multi-ref pushes and rewritten history require
`--pre-push` with Git's complete ref-update stream. Stop if any pushed ref is
uncovered. See [secret scanning](SECRET-SCANNING.md) for base selection, new branches,
pre-push input and prerequisites. Preserve GitGuardian App, CI and Gitleaks checks.

For a non-default PR target, fetch its destination and pass that exact ref to
`--base`; the remote default is not a substitute for a release/maintenance base.

The secret gate requires Python 3.11+ and approved ggshield >=1.56.1,<2.
