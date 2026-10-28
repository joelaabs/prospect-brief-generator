#!/usr/bin/env python3
"""Build a ranked B2B target list from OSHA Form 300A injury data.

Steps: filter to one state -> map NAICS codes to industry groups + glove-fit score ->
group establishments into companies (name / EIN) -> size tier A/B/C -> priority score.

Usage:
  python3 pipeline/build_target_list.py --osha ITA_300A_Summary_Data.csv --state MI --out output/
Download the data (free): https://www.osha.gov/Establishment-Specific-Injury-and-Illness-Data
"""
import argparse, os, re, pandas as pd, numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--osha", required=True, help="OSHA ITA 300A summary CSV")
ap.add_argument("--state", default="MI")
ap.add_argument("--out", default="output")
args = ap.parse_args()
raw = pd.read_csv(args.osha, dtype=str, low_memory=False)
df = raw[raw["state"].str.strip().str.upper() == args.state.upper()].copy()
for c in ['annual_average_employees','total_hours_worked','total_deaths','total_dafw_cases',
          'total_djtr_cases','total_other_cases','total_injuries','total_dafw_days']:
    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
df['naics_code'] = df['naics_code'].fillna('').str.strip()

# ---------- industry mapping: (prefix, group, fit) longest prefix wins ----------
MAP = [
 # Construction
 ('23','Construction - General','High'),('2361','Construction - Residential Building','High'),
 ('2362','Construction - Commercial/Industrial Building','High'),('237','Construction - Heavy/Civil & Utilities','High'),
 ('2381','Construction - Concrete/Masonry/Steel/Roofing','High'),('23811','Construction - Concrete & Foundation','High'),
 ('23812','Construction - Structural Steel/Erection','High'),('23814','Construction - Masonry','High'),
 ('23816','Construction - Roofing','High'),('23817','Construction - Siding','High'),
 ('23821','Construction - Electrical','High'),('23822','Construction - Plumbing/HVAC','High'),
 ('2383','Construction - Finishing (Drywall/Painting/Tile/Carpentry)','High'),('2389','Construction - Site Prep/Demolition','High'),
 # Manufacturing
 ('31','Manufacturing - Other','Medium'),('311','Food Processing','High'),('3116','Food Processing - Meat & Poultry','High'),
 ('312','Food Processing - Beverage','Medium'),('313','Manufacturing - Textiles','Medium'),('314','Manufacturing - Textiles','Medium'),
 ('315','Manufacturing - Apparel','Low'),('316','Manufacturing - Leather','Medium'),
 ('32','Manufacturing - Other','Medium'),('321','Manufacturing - Wood Products','High'),('322','Manufacturing - Paper & Packaging','High'),
 ('323','Manufacturing - Printing','Medium'),('324','Manufacturing - Petroleum/Asphalt','High'),('325','Manufacturing - Chemicals','High'),
 ('326','Manufacturing - Plastics & Rubber','High'),('327','Manufacturing - Glass/Concrete/Stone','High'),
 ('33','Manufacturing - Other','Medium'),('331','Manufacturing - Primary Metals/Foundry','High'),
 ('332','Manufacturing - Fabricated Metal','High'),('3321','Manufacturing - Forging & Stamping','High'),
 ('3327','Manufacturing - Machine Shops/Screw Machine','High'),('3328','Manufacturing - Coating/Heat Treating/Plating','High'),
 ('333','Manufacturing - Machinery','High'),('333514','Manufacturing - Tool & Die','High'),('334','Manufacturing - Electronics','Medium'),
 ('335','Manufacturing - Electrical Equipment','High'),('336','Manufacturing - Transportation Equipment','High'),
 ('3361','Automotive - OEM Assembly','High'),('3362','Automotive - Body & Trailer','High'),('3363','Automotive - Parts Supplier','High'),
 ('3364','Aerospace','High'),('337','Manufacturing - Furniture','High'),('339','Manufacturing - Misc','Medium'),
 # Primary / energy
 ('11','Agriculture/Forestry/Fishing','Medium'),('113','Forestry & Logging','High'),('1133','Forestry & Logging','High'),
 ('21','Mining & Aggregates','High'),('211','Oil & Gas','High'),('213','Oil & Gas Support','High'),
 ('22','Utilities','High'),('2211','Utilities - Electric','High'),('2212','Utilities - Gas','High'),('2213','Utilities - Water/Sewer','High'),
 # Wholesale / transport
 ('42','Wholesale Distribution','Medium'),('4231','Wholesale - Auto Parts/Lumber/Metal','Medium'),('42351','Wholesale - Steel Service Center','High'),
 ('42393','Scrap Metal Recycling','High'),('4244','Wholesale - Food','Medium'),
 ('48','Transportation','Medium'),('482','Railway','High'),('4881','Airport Work','High'),('484','Trucking','Medium'),
 ('49','Logistics/Warehousing','Medium'),('493','Logistics/Warehousing','High'),('492','Couriers & Delivery','Medium'),
 # Services
 ('56','Admin & Support Services','Low'),('5613','Staffing Agencies (industrial)','Medium'),('5617','Cleaning & Building Services','Medium'),
 ('56173','Landscaping','High'),('562','Waste Management & Remediation','High'),
 ('81','Repair & Maintenance','Medium'),('8111','Auto Repair','Medium'),('8113','Industrial Machinery Repair','High'),('8123','Laundry/Linen','Medium'),
 ('92','Public Administration (Municipal)','Medium'),
 ('62','Healthcare','Low'),('6221','Healthcare - Hospitals','Medium'),('623','Healthcare - Nursing/Residential','Low'),
 ('72','Hotel, Restaurant & Catering','Low'),('721','Hotels','Low'),
 ('44','Retail','Low'),('45','Retail','Low'),('444','Retail - Building Materials','Medium'),('4441','Retail - Building Materials','Medium'),
 ('455','Retail','Low'),('61','Education','Low'),('71','Arts & Recreation','Low'),
 ('51','Information/Media','Low'),('52','Finance','Low'),('53','Real Estate & Rental','Low'),('532','Equipment Rental','Medium'),
 ('54','Professional Services','Low'),('5413','Engineering Services','Low'),('55','Corporate Offices','Low'),('99','Unclassified','Low'),
]
MAP.sort(key=lambda x: -len(x[0]))
def classify(n):
    for p, g, f in MAP:
        if n.startswith(p): return g, f
    return 'Other', 'Low'
df[['industry_group','glove_fit']] = df['naics_code'].apply(lambda n: pd.Series(classify(n)))

# ---------- region by ZIP3 ----------
def region(z):
    z = str(z or '')[:3]
    try: z = int(z)
    except: return 'Unknown'
    if 480 <= z <= 483: return 'Southeast (Detroit Metro)'
    if 484 <= z <= 485: return 'Flint / Genesee'
    if 486 <= z <= 487: return 'Saginaw / Bay / Thumb'
    if 488 <= z <= 489: return 'Lansing / Mid-Michigan'
    if z == 492: return 'Jackson / South Central'
    if 490 <= z <= 491: return 'Southwest (Kalamazoo/Battle Creek)'
    if 493 <= z <= 495: return 'West (Grand Rapids/Muskegon)'
    if z == 496: return 'Northwest (Traverse City)'
    if z == 497: return 'Northern Lower'
    if 498 <= z <= 499: return 'Upper Peninsula'
    return 'Unknown'
df['mi_region'] = df['zip_code'].apply(region)

# ---------- data quality on employees ----------
# hours-implied headcount; flag implausible employee counts
implied = df['total_hours_worked'] / 2000
bad = (df['annual_average_employees'] > 20000) | ((implied > 0) & (df['annual_average_employees'] > 20 * implied.clip(lower=1) + 50))
df['emp_flag'] = np.where(bad, 'employee count looks wrong in OSHA data - used hours/2000', '')
df['emp_clean'] = np.where(bad, implied.round(), df['annual_average_employees'])
df['recordables'] = df['total_dafw_cases'] + df['total_djtr_cases'] + df['total_other_cases']

# ---------- company grouping key ----------
def norm(s):
    s = str(s or '').lower()
    s = re.sub(r'&', ' and ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\b(inc|llc|l l c|corp|corporation|co|company|ltd|lp|llp|plc|the|of michigan|usa|us|na|north america)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
df['company_name'] = df['company_name'].fillna('').str.strip()
df['company_disp'] = np.where(df['company_name'] != '', df['company_name'], df['establishment_name'].fillna('').str.strip())
df['name_key'] = df['company_disp'].apply(norm)
ein = df['ein'].fillna('').str.replace(r'\D', '', regex=True)
valid_ein = (ein.str.len() == 9) & ~ein.str.fullmatch(r'(\d)\1{8}') & ~ein.isin(['123456789'])
df['key'] = np.where(df['name_key'] != '', 'N:' + df['name_key'], 'E:' + ein)
# merge names that share a valid EIN: map each EIN to its most common name_key
e2n = df[valid_ein].groupby(ein[valid_ein])['name_key'].agg(lambda s: s.value_counts().index[0])
df.loc[valid_ein, 'key'] = 'N:' + ein[valid_ein].map(e2n)


FIT_RANK = {'High': 3, 'Medium': 2, 'Low': 1}
def agg(g):
    g = g.sort_values('emp_clean', ascending=False)
    top = g.iloc[0]
    emp = g['emp_clean'].sum(); hrs = g['total_hours_worked'].sum(); rec = g['recordables'].sum()
    ge = g.groupby(['industry_group','glove_fit'])['emp_clean'].sum().sort_values(ascending=False)
    grp, fit = ge.index[0]
    fit_emp = g.loc[g['glove_fit'] != 'Low', 'emp_clean'].sum()
    hi_sites = int((g['glove_fit'] == 'High').sum())
    names = g['company_disp'].value_counts()
    return pd.Series({
        'company': names.index[0].strip().strip('"').strip(),
        'industry_group': grp, 'glove_fit': fit, 'high_fit_sites': hi_sites, 'employees_at_fit_sites': int(fit_emp),
        'naics_code': top['naics_code'], 'naics_description': top['industry_description'],
        'mi_sites': len(g), 'mi_employees_osha': int(emp),
        'recordable_cases': int(rec), 'days_away_cases': int(g['total_dafw_cases'].sum()),
        'injury_rate_trir': round(rec * 200000 / hrs, 1) if hrs > 0 else np.nan,
        'deaths': int(g['total_deaths'].sum()),
        'hq_or_largest_site': top['establishment_name'], 'street_address': top['street_address'],
        'city': str(top['city']).title(), 'zip': str(top['zip_code'])[:5], 'mi_region': top['mi_region'],
        'all_site_cities': '; '.join(sorted(set(g['city'].dropna().str.title()))),
        'data_flags': '; '.join(sorted(set(f for f in g['emp_flag'] if f))),
    })
co = df.groupby('key').apply(agg).reset_index(drop=True)

def tier(r):
    e, f = r['employees_at_fit_sites'], r['glove_fit']
    if f == 'Low' and r['high_fit_sites'] == 0: return 'D - Low fit'
    if f == 'Low': f = 'Medium'
    if e >= 300: return 'A'
    if e >= 100: return 'B'
    return 'C'
co['tier'] = co.apply(tier, axis=1)
co['priority_score'] = (co['glove_fit'].map(FIT_RANK) * 1000 + co['employees_at_fit_sites'].clip(upper=5000) / 5
                        + co['injury_rate_trir'].fillna(0).clip(upper=20) * 10).round(0).astype(int)
co = co.sort_values(['tier', 'priority_score'], ascending=[True, False]).reset_index(drop=True)

# ---------- outputs ----------
OUT = args.out; os.makedirs(OUT, exist_ok=True)

def broad(g):
    g = str(g)
    if g.startswith('Automotive') or g == 'Aerospace': return 'Automotive & Aerospace'
    if any(k in g for k in ['Fabricated Metal','Primary Metals','Forging','Machine Shops','Tool & Die','Coating','Machinery']): return 'Metalworking & Machinery'
    if any(k in g for k in ['Plastics','Chemicals','Petroleum']): return 'Plastics, Rubber & Chemicals'
    if g.startswith('Food Processing'): return 'Food Processing'
    if g.startswith('Manufacturing'): return 'Other Manufacturing'
    if g.startswith('Construction'): return 'Construction'
    if g.startswith('Utilities') or g in ('Oil & Gas','Oil & Gas Support','Mining & Aggregates'): return 'Energy, Utilities & Mining'
    if g in ('Agriculture/Forestry/Fishing','Forestry & Logging','Landscaping'): return 'Agriculture, Forestry & Landscaping'
    if g in ('Logistics/Warehousing','Trucking','Railway','Airport Work','Couriers & Delivery','Transportation'): return 'Logistics & Transportation'
    if g in ('Scrap Metal Recycling','Waste Management & Remediation'): return 'Waste & Recycling'
    if g.startswith('Wholesale') or g.startswith('Retail - Building'): return 'Wholesale & Distribution'
    if g in ('Repair & Maintenance','Auto Repair','Industrial Machinery Repair','Cleaning & Building Services','Staffing Agencies (industrial)','Admin & Support Services','Laundry/Linen','Equipment Rental'): return 'Services, Repair & Staffing'
    if g.startswith('Public Administration'): return 'Public Sector & Municipal'
    if g.startswith('Healthcare'): return 'Healthcare'
    return 'Retail, Hospitality & Other'
co.insert(co.columns.get_loc('industry_group'), 'industry_group_broad', co['industry_group'].map(broad))
co['account_type'] = np.where(co['mi_employees_osha'] >= 5000,
    'Enterprise - corporate sourcing likely; target individual plants', 'Standard')
co['prospect_status'] = 'Not started'
co['state'] = args.state.upper()
co['source'] = 'OSHA ITA Form 300A summary data'
master_cols = ['tier','priority_score','company','industry_group_broad','industry_group','glove_fit','account_type','mi_sites',
    'mi_employees_osha','employees_at_fit_sites','recordable_cases','days_away_cases','injury_rate_trir','deaths',
    'naics_code','naics_description','hq_or_largest_site','street_address','city','state','zip','mi_region',
    'all_site_cities','prospect_status','data_flags','source']
co[master_cols].to_csv(f'{OUT}/michigan_master_target_list.csv', index=False)

hs = co[co['tier'] != 'D - Low fit'].copy()
hs_out = pd.DataFrame({
    'Company name': hs['company'],
    'Street Address': hs['street_address'], 'City': hs['city'], 'State/Region': 'Michigan',
    'Postal Code': hs['zip'], 'Number of Employees': hs['mi_employees_osha'],
    'Glove Tier': hs['tier'], 'Glove Industry Group': hs['industry_group_broad'], 'Glove Fit': hs['glove_fit'],
    'MI Region': hs['mi_region'], 'OSHA MI Sites': hs['mi_sites'],
    'OSHA Recordable Cases': hs['recordable_cases'], 'OSHA Injury Rate': hs['injury_rate_trir'],
    'Prospect Status': 'Not started',
    'Company Description': 'Industry detail: ' + hs['industry_group'] + ' | ' + hs['naics_description'].fillna('') + ' | Largest MI site: ' + hs['hq_or_largest_site'].fillna('').astype(str)
        + ' | MI site cities: ' + hs['all_site_cities'].fillna('') + np.where(hs['account_type']!='Standard', ' | ' + hs['account_type'], ''),
})
hs_out.to_csv(f'{OUT}/hubspot_companies_import.csv', index=False)

sites = df[['company_disp','establishment_name','industry_group','glove_fit','naics_code','industry_description',
    'street_address','city','zip_code','mi_region','emp_clean','recordables','total_dafw_cases','total_hours_worked','emp_flag']].copy()
sites.columns = ['company','site_name','industry_group','glove_fit','naics_code','naics_description','street_address',
    'city','zip','mi_region','employees','recordable_cases','days_away_cases','hours_worked','data_flag']
sites['city'] = sites['city'].str.title()
sites['injury_rate_trir'] = (sites['recordable_cases']*200000/sites['hours_worked'].replace(0,np.nan)).round(1)
sites.sort_values('employees', ascending=False).to_csv(f'{OUT}/michigan_sites_plant_level.csv', index=False)

summ = co.pivot_table(index='industry_group', columns='tier', values='company', aggfunc='count', fill_value=0)
summ['Total'] = summ.sum(axis=1); summ = summ.sort_values('Total', ascending=False)
summ.to_csv(f'{OUT}/summary_by_industry_and_tier.csv')
print(f"{len(df):,} sites -> {len(co):,} companies -> {len(hs_out):,} qualified (Tiers A-C)")
print(co['tier'].value_counts().sort_index().to_string())
