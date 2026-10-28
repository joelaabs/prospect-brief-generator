---
description: List who is due for a follow-up today (reads tracker.csv)
---
Read tracker.csv. Today's date is the current date.

For any row where sent_date is filled in but followup_1_date is blank, set
followup_1_date = sent_date + 3 business days. If followup_2_date is blank, set it to
sent_date + 7 business days. Save tracker.csv (change only those blank date cells).

Then show me a table of contacts where replied is not "Y" AND followup_1_date or
followup_2_date is today or earlier and that follow-up hasn't been noted as sent in notes.
Columns: company, contact_name, email, which follow-up (1 or 2), due date.
Pull the matching follow-up subject and body from outreach.csv under the table so I can copy
it. If nobody is due, say so in one line.
