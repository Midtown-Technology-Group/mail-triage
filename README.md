# Mail Triage CLI

Read-only inbox triage for the Midtown toy chest.

Project site: <https://midtown-technology-group.github.io/mail-triage/>

## Required Scope

- `Mail.ReadBasic`

This toy uses the shared `MTG Shared Microsoft Auth` app registration unchanged.

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
```

## Commands

- `inbox`: List recent messages with sender, received time, and read state.
- `senders`: Summarize the busiest senders in the selected inbox slice.

## Project Site

This repo includes a lightweight GitHub Pages site in `docs/`.
