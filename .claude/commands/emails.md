---
description: Write intro emails + 2 follow-ups for every contact that has a brief
argument-hint: [company name] (optional; default = all briefs without emails yet)
---
Read CLAUDE.md, my_offer.md, contacts.csv, and the briefs in briefs/. Follow the
"Email rules" in CLAUDE.md exactly.

Scope: $ARGUMENTS (if blank, every company that has a brief but no rows in outreach.csv yet).

For each company, write one email set per contact in contacts.csv:
- office / general email contact -> a short "please route me to the right person" email
- purchasing contact -> purchasing angle
- safety contact -> safety angle
If a contact has no verified email, still write the email but copy email_status into
outreach.csv so I can see it needs checking. Put email_guess in the email column only if
there is no verified email, and keep email_status as the guess label.

Alternate email_version A / B per company (both contacts at one company get the same version).

Append rows to outreach.csv (create with headers if missing). Then add matching rows to
tracker.csv with sent_date and follow-up dates left blank (create with headers if missing;
never overwrite rows already there).

Finish by printing ONE example email set so I can check tone, plus a count of emails written
and how many need an email address verified.
