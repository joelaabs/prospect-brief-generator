# Prospect-Brief Tool — Instructions for Claude

You are helping a territory sales rep (industrial safety products, Michigan) research
target companies and draft outreach. Claude reads this file automatically at the start of
every session in this folder.

## Key files
- `my_offer.md` — what the rep sells, who buys it, and common customer problems. READ THIS
  FIRST before writing any brief or email. If it still contains "FILL IN", stop and ask the rep
  to complete it.
- `companies.csv` — input list (company, website, industry, city_state, notes).
- `briefs/` — one Markdown brief per company, named `briefs/<company-slug>.md`
  (lowercase, hyphens, e.g. `briefs/acme-manufacturing.md`).
- `contacts.csv` — one row per contact found (see columns below).
- `research_log.csv` — one row per company researched.
- `outreach.csv` — emails ready for Outlook mail merge.
- `tracker.csv` — sent / replied / meeting tracking. The rep edits this by hand.

## NON-NEGOTIABLE RULES
1. **Never invent facts.** Every fact in a brief needs a source link. If you can't verify
   something, write `unknown`.
2. **Never invent or guess email addresses or phone numbers as if they were real.**
   - Only list an email/phone as `verified` if you saw it on a web page (give the URL).
   - If you can infer the company's email pattern (e.g. first.last@acme.com) from at least
     one real published address, you may fill `email_guess`, and mark `email_status` as
     `pattern-guess — verify before sending`. Never put a guess in the `email` column.
   - If a named person can't be found for a role, leave name blank and list the role as a
     "title to target".
3. Person names must come from a public source (company site, press release, news article,
   public directory). Cite the URL. Don't scrape behind logins.
4. Keep claims about the rep's products limited to what is in `my_offer.md`.
5. When a company has more than ~3 facts you're unsure of, set confidence to Low.

## Brief template (use exactly these headings)
```
# <Company name>
**Website:** | **Industry:** | **Location(s):** | **Researched:** <date> | **Confidence:** High/Medium/Low
**Account tier (estimate):** A / B / C — one line on the basis (headcount, plants, tasks)

## 1. Company snapshot
What they do, approximate size (employees/revenue if public), locations, ownership.
Hand hazards in their work (cutting, welding, heat, vibration, cold/wet, chemicals, oil).

## 1b. Recommended Tegera products
1–3 styles or categories from my_offer.md matched to their hazards, one line each on why.

## 2. Contact info
- Main office phone:            (source)
- General email:                (source)
- Purchasing / procurement manager: name, title, email, phone, status  (source)
- Safety / EHS manager:         name, title, email, phone, status  (source)
- Other useful titles to target if names not found:

## 3. News & callouts (last ~24 months)
- Growth: expansions, new facilities, hiring, acquisitions, big contracts
- Community support & local sponsorships (teams, charities, events in the area)
- Leadership changes
Each bullet: one line + date + source link.

## 4. Likely pain points
3–5 pain points, each tied to evidence (news, job posts, industry, site content) AND to
something in my_offer.md. Label each "evidence-based" or "industry-typical (inferred)".

## 5. Three openers
1–2 sentences each, specific to this company.

## 6. Five discovery questions

## 7. Sources & unknowns
Numbered list of every URL used. Then a list of what you could not verify.
```

## contacts.csv columns
company, contact_type (office / purchasing / safety / other), name, title, email,
email_guess, email_status (verified / pattern-guess — verify before sending / not found),
phone, source_url, date_found

## companies.csv columns
company, website, industry, city_state, notes, employees_est, tier_est, source_url
(The last three are optional; /find fills them.)

## research_log.csv columns
company, date, sources_used (count), confidence, notes

## Email rules (for /emails)
- First email under 120 words, one clear ask (a 15-minute call), plain text, no hype words.
- Version A = pain-point-led. Version B = news/trigger-led (growth, sponsorship, community).
  Alternate A, B, A, B down the list.
- Follow-up 1 (day 3) under 70 words; follow-up 2 (day 7) under 50 words, polite close-out.
- Personalize per contact: purchasing angle = cost, supply reliability, simplicity of
  ordering. Safety angle = compliance, incidents, training, PPE/program fit. Office/general
  email = ask to be routed to the right person.
- Never reference anything not in the brief.
- Sign-off placeholder: {{signature}}.

## outreach.csv columns (Outlook mail merge)
company, first_name, last_name, title, email, email_status, contact_type, industry,
email_version, subject, body, followup_1_subject, followup_1_body, followup_2_subject,
followup_2_body, brief_file

## tracker.csv columns
company, contact_name, title, email, industry, brief_file, email_version, sent_date,
followup_1_date, followup_2_date, replied, reply_type, meeting_booked, notes
(Dates as YYYY-MM-DD. reply_type: positive / not now / not a fit / referral.)
