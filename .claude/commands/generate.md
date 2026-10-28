---
description: Generate call-prep briefs, emails and call scripts from the Excel CRM
argument-hint: [filters, e.g. --tier A --region Southeast]
---
Run: `python3 tool/generate.py $ARGUMENTS`

Then tell me how many companies were updated and how many briefs were written, and show me
one generated brief from the selection so I can check it. If CRM.xlsx is missing
from this folder, ask me to download my latest copy from Excel for the web into this folder first.
After it runs, remind me to upload the updated CRM.xlsx back to OneDrive.
