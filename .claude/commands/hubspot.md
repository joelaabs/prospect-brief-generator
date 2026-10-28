---
description: Export contacts.csv into a HubSpot-ready import file
---
Read contacts.csv, companies.csv, and tracker.csv. Create exports/hubspot_contacts.csv
(make the exports/ folder if missing) with these exact column headers, which HubSpot's
import tool recognizes automatically:

First Name, Last Name, Email, Phone Number, Job Title, Company Name, Company Domain Name,
City, State/Region, Industry, Lifecycle Stage, Lead Status, Email Version, Brief File, Email Status

Rules:
- One row per person contact. Skip "office" rows that have no person name, but list them
  for me after.
- Email: use the verified email only. If there is only a guess, leave Email blank and put
  the guess text in Email Status so I don't import an unverified address.
- Company Domain Name: the website with no https:// or www. (this links the contact to the
  right company in HubSpot).
- Lifecycle Stage = Lead. Lead Status = New (or Attempted to contact if sent_date is filled
  in tracker.csv; Connected if replied = Y).

Finish by telling me: rows exported, rows skipped and why, and the exact HubSpot clicks to
import it (Contacts > Import > Start an import > File from computer > One file > One object
> Contacts > upload > map columns; create custom properties for Email Version, Brief File,
and Email Status when HubSpot asks).
