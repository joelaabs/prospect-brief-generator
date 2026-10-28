---
description: Research companies from companies.csv and write briefs + contacts
argument-hint: [number of companies or a company name] (default 3)
---
Read CLAUDE.md and my_offer.md first. Follow every rule in CLAUDE.md.

Which companies: $ARGUMENTS
- If a number is given, take that many companies from companies.csv that do NOT already
  have a brief in briefs/.
- If a company name is given, do just that company.
- If nothing is given, do the next 3 companies.

For each company, one at a time:
1. Read the company website (home, about, contact, leadership/team, news/press, careers).
2. Web search for: "<company> purchasing manager", "<company> safety manager" / "EHS manager",
   "<company> expansion", "<company> sponsorship" / "<company> community", and recent news
   (last 24 months), including local news in their city.
   Contact-finding tricks that work: Michigan EGLE air-quality inspection reports
   (search "<company> EGLE" or "<city> SRN staff report") often name the EHS manager and
   plant staff; company job postings name the hiring roles; chamber of commerce listings
   give main phones; ISM chapter job files reveal purchasing teams.
   Also pull the company's rows from michigan_sites_plant_level.csv (OSHA data) for site
   addresses, headcount and injury numbers. Injury numbers are INTERNAL ONLY: use them in
   the brief's pain points, never quote them in emails.
3. Write briefs/<company-slug>.md using the template in CLAUDE.md.
4. Append contacts to contacts.csv (create the file with headers if missing).
5. Append one row to research_log.csv.

When finished, show me a short table: company, confidence, named contacts found
(purchasing / safety), verified emails found, and anything I should check by hand.
