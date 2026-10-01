# Mail Triage

Windows-first Python/Typer operator CLI for delegated Microsoft 365 mailbox inspection and actions. `src/mail_triage_cli/` owns CLI/service/repository behavior; `tests/` contains corresponding unit tests. Read [README.md](README.md) for auth/scopes, command semantics, and MSI distribution; [GITHUB_WORKFLOW.md](GITHUB_WORKFLOW.md) describes a concrete notification-follow-up use case.

## Development checks

Use Python 3.10+ and an isolated environment: `python -m pip install -e ".[dev]"`, then `python -m pytest`. These commands follow the declared development dependency and pytest configuration, with current tests under `tests/`; a test CI lane was not found in the inspected workflows. Verify pagination, output serialization, selected-mailbox targeting, and Graph errors through mocked repository/service seams rather than real mail mutation.

## Operator boundaries

Default scope is `Mail.ReadBasic`; the shared Microsoft auth app registration stays unchanged. Preserve shared WAM token-cache reuse and account selection. Scope bundles for write/send/shared-mailbox operations are explicit in README; do not expand baseline consent to folder-management scopes without a concrete need.

`inbox` and `senders` inspect mail. `read`/`unread`, `read-matching`, `move`, `delete`, and `send` mutate mail or deliver messages; in particular, `read-matching` is not a read-only listing command. Keep exact mailbox/message IDs and bounded pagination explicit in requests and previews. Sending mail requires direct authorization; a sample workflow or fixture is not authorization.

Never write tokens, message bodies, or customer mailbox contents into source fixtures/logs. Use stable synthetic data and verify `--output json` remains machine-readable. A successful local test does not prove live mailbox access or delivery. Tagged MSI publishing/per-machine installation changes distribution or host state and requires the corresponding release procedure; preserve `invoke.ps1` as the Windows operator entrypoint.
