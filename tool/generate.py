#!/usr/bin/env python3
"""Prospect brief & script generator.

Reads the Excel CRM (Companies tab), and for each selected company writes:
  * a call-prep brief (Markdown) in briefs/generated/
  * emails (safety, purchasing, general inbox), 2 follow-ups, voicemail and call opener
    into extra columns of the CRM, ready for copy/paste or Outlook mail merge.

Your own edits in the CRM (contacts, status, notes, dates) are never changed, except that
an empty Email Version is filled in (A/B alternating). Re-run any time: if you've added a
contact name and role, their emails are regenerated with "Hi <first name>,".

Examples
  python3 tool/generate.py                              # every company
  python3 tool/generate.py --tier A --region Southeast  # one slice
  python3 tool/generate.py --company "Ridgeview"        # one company
  python3 tool/generate.py --status "Needs research,Ready to email"
"""
import argparse, datetime as dt, os, re, shutil, statistics, sys
from collections import defaultdict

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

sys.path.insert(0, os.path.dirname(__file__))
from playbooks import PLAYBOOKS, DEFAULT_GROUP
import catalog
import config as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GEN_COLS = [  # (header, width)
    ("Brief File", 30), ("Recommended Styles", 34), ("Call Opener", 50),
    ("Safety Email Subject", 28), ("Safety Email Body", 60),
    ("Purchasing Email Subject", 28), ("Purchasing Email Body", 60),
    ("General Inbox Email Subject", 28), ("General Inbox Email Body", 60),
    ("Follow-up 1 Body", 50), ("Follow-up 2 Body", 50), ("Voicemail", 50), ("Generated On", 12),
]
GEN_FILL = "7030A0"
REGION_PHRASE = {
    "Southeast (Detroit Metro)": "Southeast Michigan", "West (Grand Rapids/Muskegon)": "West Michigan",
    "Southwest (Kalamazoo/Battle Creek)": "Southwest Michigan", "Lansing / Mid-Michigan": "the Lansing area",
    "Saginaw / Bay / Thumb": "the Saginaw, Bay City and Thumb area", "Flint / Genesee": "the Flint area",
    "Upper Peninsula": "the Upper Peninsula", "Jackson / South Central": "the Jackson area",
    "Northwest (Traverse City)": "Northwest Michigan", "Northern Lower": "Northern Michigan"}

SUFFIX = re.compile(r",?\s+(inc|llc|l\.l\.c|corp|corporation|co|company|ltd|lp|llp|pc)\.?$", re.I)


# ---------------------------------------------------------------- helpers
def short_name(name):
    s = str(name).strip().strip('"')
    for _ in range(2):
        s = SUFFIX.sub("", s).strip().rstrip(",")
    return s

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")[:80] or "company"

def first_name(full):
    full = (full or "").strip()
    return full.split()[0] if full else ""

def winter_now(today):
    return today.month in (10, 11, 12, 1, 2)

def words(s):
    return len(re.sub(r"\[.*?\]", "x", s.split(C.SIGNATURE.splitlines()[0])[0]).split())



# ---------------------------------------------------------------- content
def build(row, pb, version, today, peers):
    co, short = row["Company"], short_name(row["Company"])
    city = (row.get("City") or "").strip()
    sites = int(row.get("MI Sites") or 1)
    emp = int(row.get("MI Employees") or 0)
    region = REGION_PHRASE.get(row.get("MI Region"), "Michigan")
    rec = catalog.recommend(row.get("Industry Detail"), row.get("Industry Group"),
                            outdoor=pb["outdoor"], winter=winter_now(today))
    g = rec["gloves"]
    lc = lambda t: (t[:1].lower() + t[1:]).rstrip(".") if t else ""
    p1, w1 = g[0]["name"], lc(g[0]["desc"])
    second = next((x for x in g[1:] if lc(x["desc"]) != w1), g[1])   # avoid two near-identical picks
    p2, w2 = second["name"], lc(second["desc"])
    work = pb["work"]

    # who gets which email
    contacts = []
    for n in ("1", "2"):
        nm, role = row.get(f"Contact {n} Name"), row.get(f"Contact {n} Role") or ""
        if nm: contacts.append((nm, role))
    def who(roles):
        for nm, role in contacts:
            if role in roles: return first_name(nm)
        return ""
    safety_first = who({"Safety / EHS"}) or "[First name]"
    purch_first = who({"Purchasing"}) or "[First name]"

    sig = C.SIGNATURE
    site_phrase = f"{sites} Michigan sites" if sites > 1 else (f"your {city} location" if city else "your location")

    # ---- safety email
    if version == "A":
        s_subj = f"Glove idea for {short}"
        s_body = (f"Hi {safety_first},\n\n{pb['problem']}\n\n"
                  f"I'm the Michigan rep for Tegera gloves by Ejendals. For {work}, I'd start with the {p1} ({w1}) "
                  f"and the {p2} ({w2}). Sizes go up to 12 in some styles, and they ship through {C.DISTRIBUTORS}, "
                  f"so there's no new vendor.\n\n"
                  f"Would you be open to a 15-minute call to see if a glove trial at {short} makes sense?\n\n{sig}")
    else:
        if pb["outdoor"] and winter_now(today):
            hook = "With Michigan winter on the way, cold, wet hands are about to become the main reason gloves come off."
        elif sites > 1:
            hook = f"With {site_phrase}, I'm guessing glove choices vary by site, area and shift."
        else:
            hook = f"I'm guessing glove choices at {site_phrase} vary by area and shift, and some people skip them."
        s_subj = f"Local glove support for {short}"
        s_body = (f"Hi {safety_first},\n\n{hook}\n\n"
                  f"I'm the Michigan rep for Tegera gloves by Ejendals, and I cover {region} in person: plant walks, "
                  f"fit checks and glove trials. For {work}, the {p1} and {p2} are where I'd start, and you can order "
                  f"them through {C.DISTRIBUTORS}.\n\n"
                  f"Would you be open to a 15-minute call, or a quick visit with samples?\n\n{sig}")

    # ---- purchasing email
    if version == "A":
        p_subj = f"Glove spend at {short}"
        p_body = (f"Hi {purch_first},\n\nGloves are a consumable that adds up fast in {work}, especially when they "
                  f"wear out quickly or get tossed because they don't fit.\n\n"
                  f"I'm the Michigan rep for Tegera gloves by Ejendals. They're made to last longer at each protection "
                  f"level, which lowers what you spend per worker, and sizing goes up to 12 in some styles. You can order "
                  f"through {C.DISTRIBUTORS}, so there's no new vendor setup.\n\n"
                  f"Would a 15-minute call make sense to compare what {short} buys today?\n\n{sig}")
    else:
        hook = (f"Buying gloves for {sites} Michigan sites usually means different gloves, prices and reorder points at each one."
                if sites > 1 else
                "Most companies I visit buy several glove types from several sources, and nobody's sure which one actually lasts.")
        p_subj = f"Simplifying gloves at {short}"
        p_body = (f"Hi {purch_first},\n\n{hook}\n\n"
                  f"I'm the Michigan rep for Tegera gloves by Ejendals. One line covers cut, heat, cold and wet work, and "
                  f"vibration, and it ships through {C.DISTRIBUTORS} you may already use.\n\n"
                  f"Would a 15-minute call make sense to compare what you buy today?\n\n{sig}")

    # ---- general inbox / contact form
    g_subj = f"Who handles safety gloves at {short}?"
    g_body = (f"Hi,\n\nI'm {C.REP_NAME}, the Michigan rep for Tegera safety gloves by Ejendals. Could you point me to the "
              f"person who handles safety gloves or PPE purchasing for {short}? Usually that's the safety manager or "
              f"purchasing.\n\nI'd like to send them a short note about gloves for {work}. Thank you!\n\n{sig}")

    fu1 = (f"Hi [First name],\n\nFollowing up on my note about gloves for {work}. If it's easier, I can drop off a few "
           f"pairs of the {p1} in different sizes so your team can try them on shift. Is there a good day this week or next?\n\n{sig}")
    fu2 = (f"Hi [First name],\n\nI don't want to crowd your inbox, so this is my last note for now. If gloves come up "
           f"later, I'm local and happy to help. We also carry JALAS safety footwear from the same manufacturer.\n\n{sig}")
    vm = (f"Hi [First name], this is {C.REP_NAME} with {C.COMPANY}, the Michigan rep for Tegera safety gloves. "
          f"I'm calling about gloves for {work} at {short}. I'd like to drop off a few pairs of the {p1} for your team to try. "
          f"I'll send a short email too. "
          f"You can reach me at {C.PHONE}. Again, {C.REP_NAME}, {C.PHONE}. Thanks.")
    opener = pb["opener"]
    styles = "; ".join(f"{x['name'].replace('TEGERA ', '')} ({lc(x['desc'])})" for x in [g[0], second] + [x for x in g[1:] if x is not second][:1])

    # ---- brief
    rate = row.get("OSHA Injury Rate")
    peer = peers.get(row.get("Industry Group"))
    cases = int(row.get("OSHA Recordable Cases") or 0)
    if rate in (None, ""):
        injury = "not available"
    elif cases == 0:
        injury = "no recordable cases reported for 2025"
    elif peer:
        pct = round(100 * sum(1 for x in peer if x < float(rate)) / len(peer))
        injury = (f"{cases} recordable cases in 2025, injury rate {float(rate):.1f}; higher than {pct}% of "
                  f"{row.get('Industry Group')} companies on your list")
    else:
        injury = f"{cases} recordable cases in 2025, injury rate {float(rate):.1f}"
    contacts_md = "\n".join(f"- {nm} ({role or 'role not set'})" for nm, role in contacts) or "- None yet. Research needed."
    fw = f"https://www.google.com/search?q={re.sub(' +', '+', short + ' ' + city + ' Michigan')}"
    li = f"https://www.linkedin.com/search/results/people/?keywords={re.sub(' +', '%20', short + ' safety OR purchasing')}"

    brief = f"""# {co}: call prep
**Tier {row.get('Tier')}** | Glove fit: {row.get('Glove Fit')} | {row.get('Industry Group')} | {row.get('MI Region')} | Generated {today:%Y-%m-%d}

_Generated from OSHA 2025 data and the {row.get('Industry Group')} playbook. No web research yet: hazards and pain points are typical for this industry, not confirmed for this company._

## Snapshot (OSHA 2025)
- **Industry:** {row.get('Industry Detail') or row.get('Industry Group')}
- **Michigan size:** {emp:,} employees across {sites} site{'s' if sites > 1 else ''}
- **Largest site:** {row.get('Street Address') or ''}, {city} {row.get('ZIP') or ''}
- **Website:** {row.get('Website') or 'not found yet'} | [Find website]({fw}) | [Find people on LinkedIn]({li})
- **Main phone:** {row.get('Main Phone') or 'not found yet'} | **General email:** {row.get('General Email') or 'not found yet'}
- **Injury record (INTERNAL ONLY, never quote):** {injury}

## Contacts
{contacts_md}

**Titles to find:** Safety / EHS Manager, Purchasing Manager or Buyer, Plant or Operations Manager.

## Likely hand hazards (industry-typical)
""" + "\n".join(f"- {h}" for h in pb["hazards"]) + ("\n\n**Ejendals notes for this industry:**\n" + "\n".join(f"- {h}" for h in rec["hazards"]) if rec["hazards"] else "") + """

## Recommended Tegera gloves
""" + "\n".join(f"{i}. **{x['name']}**: {x['desc'].rstrip('.')}." + (f" {x['features'].rstrip('.')}." if x.get('features') else "") + f" _({x['why_source']})_ [See on ejendals.com]({x['url']})" for i, x in enumerate(g, 1)) + """

Lead with #1 and #2. Ratings shown are Ejendals' EU ratings; confirm US (ANSI) ratings before quoting them.

## JALAS footwear (secondary: mention once, in follow-up 2 or on a call)
""" + ("\n".join(f"- **{x['name']}**: {x['desc'].rstrip('.')}. [See on ejendals.com]({x['url']})" for x in rec["shoes"]) or "- No industry-specific picks; see ejendals.com/jalas") + """

**Sources:** """ + " · ".join(f"[{n}]({u})" for n, u in rec["sources"]) + """

## Likely pain points (industry-typical, inferred)
""" + "\n".join(f"- {x}" for x in pb["pains"]) + f"""

## Call scripts
**Gatekeeper (main line)**
> Hi, this is {C.REP_NAME} with {C.COMPANY}. I'm the Michigan rep for Tegera safety gloves. Who handles safety gloves and PPE for {short}: your safety manager or purchasing?
> Great, could you connect me? Or what's the best email to reach them?

**Safety / EHS manager**
> Hi [First name], {C.REP_NAME} with {C.COMPANY}, the Michigan rep for Tegera gloves. Did I catch you at an OK time for 30 seconds?
> {opener} {pb['problem']}
> Ask 1–2 discovery questions (below), then: "What I'd suggest is a quick trial. I drop off the {p1} and {p2} in a few sizes, your team wears them for a week or two, and they tell you what they think. Would [day] work for me to stop by?"

**Purchasing**
> Hi [First name], {C.REP_NAME} with {C.COMPANY}. I'm the Michigan rep for Tegera gloves, which ship through {C.DISTRIBUTORS}. Quick question: which gloves does {short} buy the most of? I'd like to show you a Tegera option on cost per worker, not just price per pair. Is a 15-minute call this week possible?

**Voicemail (under 30 seconds)**
> {vm}

**Objections**
- *"We already have a supplier."* Most companies do. Tegera ships through {C.DISTRIBUTORS}, so you may not need a new vendor, just a better glove on the same order. Worth comparing your one or two highest-volume gloves?
- *"Just send me some info."* Happy to. So I send the right thing, which jobs are hardest on gloves right now?
- *"It's about price."* If a glove lasts longer, it can cost less per worker even at a higher price per pair. A short trial shows whether that's true for you.
- *"Not interested."* Fair enough. Is it OK if I check back in a few months? (Set Prospect Status to **Not now** and add a Next Step Date.)

## Discovery questions
""" + "\n".join(f"{i}. {q}" for i, q in enumerate(pb["questions"] + [
        "Who picks the glove spec, and who places the order?",
        "How do you handle safety footwear today? (opens the JALAS conversation)"], 1)) + f"""

## Emails (Version {version})
**Safety: {s_subj}**
```
{s_body}
```
**Purchasing: {p_subj}**
```
{p_body}
```
**General inbox or contact form: {g_subj}**
```
{g_body}
```
**Follow-up 1 (day 3): Re: [original subject]**
```
{fu1}
```
**Follow-up 2 (day 7): Closing the loop**
```
{fu2}
```

## Notes from CRM
{row.get('Notes') or '-'}
"""
    return dict(styles=styles, opener=opener, s_subj=s_subj, s_body=s_body, p_subj=p_subj, p_body=p_body,
                g_subj=g_subj, g_body=g_body, fu1=fu1, fu2=fu2, vm=vm, brief=brief)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crm", default=os.path.join(ROOT, "CRM.xlsx"))
    ap.add_argument("--briefs-dir", default=os.path.join(ROOT, "briefs"),
                    help="folder for briefs; hand-researched briefs live here, generated ones in <dir>/generated")
    ap.add_argument("--out", help="output workbook (default: overwrite --crm after making a backup)")
    ap.add_argument("--tier", help="e.g. A or A,B")
    ap.add_argument("--region", help="text match on MI Region, e.g. Southeast")
    ap.add_argument("--industry", help="text match on Industry Group")
    ap.add_argument("--status", help="comma list of Prospect Status values")
    ap.add_argument("--company", help="text match on company name")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--brief-tiers", default="A,B", help="tiers that get a brief file (default A,B)")
    a = ap.parse_args()

    today = dt.date.today()
    wb = load_workbook(a.crm)
    ws = wb["Companies"]
    hdr = {c.value: c.column for c in ws[1] if c.value}
    # add generated columns if missing
    for h, w in GEN_COLS:
        if h not in hdr:
            col = ws.max_column + 1
            c = ws.cell(1, col, h)
            c.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
            c.fill = PatternFill("solid", fgColor=GEN_FILL)
            c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            ws.column_dimensions[c.column_letter].width = w
            hdr[h] = col
    last = max(hdr.values())

    rows = []
    for r in range(2, ws.max_row + 1):
        if not ws.cell(r, hdr["Company"]).value: continue
        rows.append((r, {h: ws.cell(r, c).value for h, c in hdr.items()}))

    peers = defaultdict(list)
    for _, d in rows:
        if d.get("OSHA Injury Rate") not in (None, "") and (d.get("MI Employees") or 0) >= 20:
            peers[d.get("Industry Group")].append(float(d["OSHA Injury Rate"]))

    def keep(d):
        if a.tier and str(d.get("Tier")) not in a.tier.split(","): return False
        if a.region and a.region.lower() not in str(d.get("MI Region") or "").lower(): return False
        if a.industry and a.industry.lower() not in str(d.get("Industry Group") or "").lower(): return False
        if a.status and str(d.get("Prospect Status")) not in [s.strip() for s in a.status.split(",")]: return False
        if a.company and a.company.lower() not in str(d.get("Company")).lower(): return False
        return True
    sel = [(r, d) for r, d in rows if keep(d)][: a.limit or None]

    gen_dir = os.path.join(a.briefs_dir, "generated"); os.makedirs(gen_dir, exist_ok=True)
    researched = {f[:-3] for f in os.listdir(a.briefs_dir) if f.endswith(".md")}
    brief_tiers = set(a.brief_tiers.split(","))
    n_brief = n_rows = n_skip = 0
    for r, d in sel:
        pb = PLAYBOOKS.get(d.get("Industry Group"), PLAYBOOKS[DEFAULT_GROUP])
        version = (d.get("Email Version") or "")[:1]
        if version not in ("A", "B"):
            version = "A" if int(d.get("ID") or r) % 2 else "B"
            ws.cell(r, hdr["Email Version"], "A - Pain point" if version == "A" else "B - News/trigger")
        s = slug(d["Company"])
        if s in researched:      # hand-researched brief exists: point to it, don't overwrite
            ws.cell(r, hdr["Brief File"], f"{os.path.basename(a.briefs_dir)}/{s}.md (researched)")
            n_skip += 1
            continue
        out = build(d, pb, version, today, peers)
        path = ""
        if str(d.get("Tier")) in brief_tiers:
            fname = f"{int(d.get('ID') or r):04d}-{s}.md"
            path = os.path.relpath(os.path.join(gen_dir, fname), os.path.dirname(os.path.abspath(a.crm)))
            with open(os.path.join(gen_dir, fname), "w") as f: f.write(out["brief"])
            n_brief += 1
        vals = {"Brief File": path, "Recommended Styles": out["styles"], "Call Opener": out["opener"],
                "Safety Email Subject": out["s_subj"], "Safety Email Body": out["s_body"],
                "Purchasing Email Subject": out["p_subj"], "Purchasing Email Body": out["p_body"],
                "General Inbox Email Subject": out["g_subj"], "General Inbox Email Body": out["g_body"],
                "Follow-up 1 Body": out["fu1"], "Follow-up 2 Body": out["fu2"], "Voicemail": out["vm"],
                "Generated On": today}
        for h, v in vals.items():
            c = ws.cell(r, hdr[h], v)
            c.font = Font(name="Arial", size=10)
            if h == "Generated On": c.number_format = "mm/dd/yyyy"
        n_rows += 1

    ws.auto_filter.ref = f"A1:{ws.cell(1, last).column_letter}{ws.max_row}"
    out_path = a.out or a.crm
    if not a.out:
        shutil.copy(a.crm, a.crm.replace(".xlsx", f"_backup_{today:%Y%m%d}.xlsx"))
    wb.save(out_path)
    print(f"Selected {len(sel)} companies: {n_rows} updated, {n_brief} briefs written, {n_skip} kept researched briefs.")
    print(f"Saved {out_path}")

if __name__ == "__main__":
    main()
