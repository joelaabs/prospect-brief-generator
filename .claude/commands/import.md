---
description: Turn my existing company research (pasted or in a file) into briefs + contacts, without re-researching
argument-hint: [file name in this folder, e.g. my_research.docx or my_research.csv]
---
Read CLAUDE.md and my_offer.md first. Follow every rule in CLAUDE.md.

My existing research is in: $ARGUMENTS
(If blank, ask me to paste it or drop the file into this folder.)

For each company in that material:
1. Add a row to companies.csv if it's not already there.
2. Write briefs/<company-slug>.md using the CLAUDE.md template, using ONLY what is in my
   material. Do not search the web in this step. Anything the template asks for that my
   material doesn't have: write "unknown — run /research <company> to fill".
3. Add contacts to contacts.csv. Emails and phones from my material count as
   email_status "from my notes — verify" unless my notes show a source link.
4. Add a row to research_log.csv with notes "imported from my notes".

When finished, show me a table: company, what's complete, what's missing (contacts,
news/callouts, pain points). Then suggest which companies most need /research.
