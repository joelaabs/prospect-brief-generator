---
description: Find new Michigan target companies in an industry and add them to companies.csv
argument-hint: <industry> [how many] [area]  e.g. "metal stamping 15 Southeast Michigan"
---
Read CLAUDE.md and my_offer.md first.

Request: $ARGUMENTS  (default count 10; default area: all of Michigan)

1. Web search for companies in that industry and area: industry associations and member
   directories, chamber of commerce lists, local business journals' "largest companies"
   lists, news about plants, and company websites. Prefer companies with real operations
   (plants, crews, warehouses) in Michigan.
2. Skip anything already in companies.csv (compare names and websites).
3. For each new company, confirm on its own website that it exists and does that work.
4. Estimate employees only from a cited source (website, news, LinkedIn public page, state
   database); otherwise write unknown. Set tier_est (A/B/C) from my_offer.md, or "unknown".
5. Append rows to companies.csv: company, website, industry, city_state, notes,
   employees_est, tier_est, source_url. Put any useful detail in notes.

Then show me a table of what you added, sorted Tier A first, and how many you skipped as
duplicates. Do not research contacts in this step.
