# Mail Triage CLI

Inbox triage and delegated mail actions for the Midtown toy chest.

Project site: <https://midtown-technology-group.github.io/mail-triage/>

## Required Scope

- `Mail.ReadBasic`

This toy uses the shared `MTG Shared Microsoft Auth` app registration unchanged.

## Write Bundles

- own mailbox triage + mutate: `Mail.ReadWrite`
- own mailbox triage + send: `Mail.ReadWrite`, `Mail.Send`
- own + shared mail triage + send: `Mail.ReadWrite`, `Mail.Send`, `Mail.ReadWrite.Shared`, `Mail.Send.Shared`

We are intentionally keeping folder-management scopes like `MailboxFolder.ReadWrite` out of the baseline until a concrete toy needs them.

## Environment

```powershell
$env:MAIL_TRIAGE_CLIENT_ID='e02be6f7-063a-46a6-b2cc-109d5f51055c'
$env:MAIL_TRIAGE_TENANT_ID='a3599b15-c39c-4b41-a219-7e24dd5b5190'
$env:MAIL_TRIAGE_SCOPES='Mail.ReadBasic'
$env:MAIL_TRIAGE_AUTH_MODE='wam'
$env:MAIL_TRIAGE_ALLOW_BROKER='true'
```

## Usage

```powershell
.\invoke.ps1 inbox --unread-only --limit 10
.\invoke.ps1 senders --limit 25
.\invoke.ps1 --output json inbox
.\invoke.ps1 read AAMk... --mailbox me
.\invoke.ps1 move AAMk... --to archive
.\invoke.ps1 send --to person@example.com --subject "Test" --body "Hello"
.\invoke.ps1 send --to person@example.com --subject "Shared test" --body "Hello" --mailbox shared@example.com
```

## Commands

- `inbox`: List recent messages with sender, received time, and read state.
- `senders`: Summarize the busiest senders in the selected inbox slice.
- `read` / `unread`: Mark specific messages as read or unread.
- `move`: Move specific messages into another folder.
- `delete`: Delete specific messages.
- `send`: Send a message from your mailbox or a shared mailbox you can access.

## Project Site

This repo includes a lightweight GitHub Pages site in `docs/`.

## License

GPL-3.0-or-later.
