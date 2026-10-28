# Prospect Brief Generator

**AI-assisted B2B prospecting for industrial safety sales.** Built by Joe Laabs, a territory sales rep, to
sell safety gloves across Michigan. Built with Claude (Anthropic).

It turns free public OSHA data into a ranked list of every likely buyer in a state, then generates a
call-prep brief, role-specific emails, follow-ups and call scripts for each company. The rep only has to
find a contact's name and email. Everything else is ready.

> Real results on Michigan data: **13,701** workplace sites → **6,385** companies → **5,160** qualified
> targets in three size tiers, each with emails and scripts, and **1,833** call-prep briefs for the top two
> tiers, generated in about 15 seconds.

## The problem
A rep with 5,000+ possible accounts can't hand-research and hand-write outreach for each one. Purchased
lists are expensive and stale, generic emails get ignored, and good research takes 20–30 minutes per company.

## How it works

```
OSHA Form 300A injury data (free, public)
   │  pipeline/build_target_list.py
   │  filter to a state · map NAICS codes to 15 industry groups · glove-fit score
   │  group sites into companies (name + EIN) · size tier A/B/C · priority score
   ▼
master_target_list.csv  +  HubSpot import file
   │  pipeline/build_crm.py
   ▼
Excel CRM: dropdowns · color-coded pipeline status · auto follow-up dates · live dashboard
   │  tool/generate.py + tool/playbooks.py
   ▼
Per company: brief (.md) · safety / purchasing / general-inbox emails · 2 follow-ups ·
             voicemail · call scripts with objection handling · A/B email version
   │
   ├─ Tier A: deep, sourced web research with Claude Code (/research)
   ├─ Tier B: rep adds one named contact → re-run → personalized "Hi <name>" emails
   └─ Tier C: automated template outreach
```

## What's in the repo

| Path | What it does |
| --- | --- |
| `pipeline/build_target_list.py` | OSHA data → ranked company list and HubSpot import file |
| `pipeline/build_crm.py` | Master list → Excel CRM (Companies, Dashboard, How to use, Lists tabs) |
| `tool/generate.py` | CRM → briefs and 13 outreach columns. Never overwrites the rep's edits; re-runnable |
| `tool/playbooks.py` | Industry knowledge for 15 groups: hazards, matched products, pain points, openers, questions |
| `tool/config.py` | Rep name, signature (CAN-SPAM address and opt-out), distributors |
| `CLAUDE.md`, `.claude/commands/` | Rules and slash commands for Claude Code: `/research`, `/generate`, `/emails`, `/followups`, `/weekly`, `/hubspot`, `/find`, `/import` |
| `sample/` | **Fictional** companies, a sample CRM and generated briefs, so you can see the output |

## Quick start (sample data)

```bash
pip install -r requirements.txt
python3 pipeline/build_crm.py --master sample/sample_master_list.csv --out sample/Sample_CRM.xlsx --prefill sample/prefill.json
python3 tool/generate.py --crm sample/Sample_CRM.xlsx --briefs-dir sample/briefs --brief-tiers A,B,C
```
Open `sample/Sample_CRM.xlsx` and `sample/briefs/generated/`.

## Real data

```bash
# 1. Download the Form 300A summary CSV: https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data
python3 pipeline/build_target_list.py --osha ITA_300A_Summary_Data.csv --state MI --out output/
python3 pipeline/build_crm.py --master output/michigan_master_target_list.csv --out CRM.xlsx
python3 tool/generate.py --crm CRM.xlsx --tier A,B
python3 tool/generate.py --crm CRM.xlsx --tier A --region Southeast   # one slice
```

## Design choices
- **Data-first targeting:** OSHA filings give real headcount, location, industry and injury history,
  which is better than a purchased list, and free.
- **Effort matched to value:** large accounts get sourced AI research; small ones get automated templates.
- **Accuracy guardrails:** generated briefs are labeled "industry-typical" until researched. Researched
  briefs cite a source for every fact. Emails are never guessed or invented.
- **Ethics and compliance:** injury data is used for internal context only, never quoted to prospects.
  Emails carry a CAN-SPAM-compliant signature and opt-out line.
- **Works with the tools a rep already has:** Excel for the web, Outlook mail merge, HubSpot free.

## Results
_Coming soon, with real numbers:_ companies contacted · reply rate by version (A/B) · meetings · trials · new accounts.

## Privacy
No real prospect contacts or CRM data are in this repository. Company names in `sample/` are fictional.
OSHA data is public and is downloaded by the user.

## License
MIT
