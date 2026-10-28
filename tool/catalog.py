"""Ejendals (TEGERA gloves / JALAS shoes) catalog and industry recommendations.

Data comes from ejendals.com, collected 2026-10-28 into catalog/industries/*.txt (each industry
page's recommended gloves, shoes and hazards) and catalog/categories/*.txt (glove category pages).
Line format:  GLOVE|model|name|description[|features]   SHOE|...   HAZARD|text

recommend() maps a CRM Industry Detail to Ejendals industries and returns gloves, shoes and hazards.
Where Ejendals has no industry page (e.g. stamping, plastics), picks come from Ejendals category
ranges matched to the hazard, and are labeled that way.
"""
import os, re

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "catalog")
SITE = "https://www.ejendals.com"

INDUSTRY_PAGES = {  # key: (name, url)
    "bricklaying-masonry": ("Bricklaying and masonry", "/industries/building-and-construction/bricklaying-and-masonry/"),
    "carpentry": ("Carpentry", "/industries/building-and-construction/carpentry/"),
    "concrete": ("Concrete & foundation services", "/industries/building-and-construction/concrete-services/"),
    "electrical": ("Electrical installation", "/industries/building-and-construction/electrical-installation/"),
    "roofing": ("Roofing", "/industries/building-and-construction/roofing/"),
    "scaffolding": ("Scaffolding", "/industries/building-and-construction/scaffolding/"),
    "tiling": ("Tiling", "/industries/building-and-construction/tiling/"),
    "ventilation": ("Ventilation", "/industries/building-and-construction/ventilation/"),
    "painting": ("Painting", "/industries/building-and-construction/painting/"),
    "plumbing": ("Plumbing", "/industries/building-and-construction/plumbing/"),
    "wind-power": ("Wind power", "/industries/energy/wind-power/"),
    "oil-gas": ("Oil & gas", "/industries/energy/oil-and-gas/"),
    "cleaning": ("Cleaning & housekeeping", "/industries/food-hospitality--cleaning/cleaning-and-housekeeping/"),
    "hotel-restaurant": ("Hotel, restaurant & catering", "/industries/food-hospitality--cleaning/hotel-restaurant--catering/"),
    "food-handling": ("Food handling", "/industries/food-hospitality--cleaning/food-handling/"),
    "life-sciences": ("Life sciences", "/industries/healthcare--life-sciences/life-sciences/"),
    "health-care": ("Health care", "/industries/healthcare--life-sciences/health-care/"),
    "automotive": ("Automotive", "/industries/manufacturing-heavy-industry/automotive/"),
    "metalwork": ("Metalwork", "/industries/manufacturing-heavy-industry/metalwork/"),
    "welding": ("Welding", "/industries/manufacturing-heavy-industry/welding/"),
    "mining": ("Mining", "/industries/primary-sector/mining/"),
    "agriculture": ("Agriculture", "/industries/primary-sector/agriculture/"),
    "forestry": ("Forestry", "/industries/primary-sector/forestry/"),
    "fishing": ("Fishing", "/industries/primary-sector/fishing/"),
    "logistics": ("Logistics", "/industries/transportation/logistics/"),
    "winter-cold": ("Winter and cold conditions", "/industries/seasonal-safety-gloves-work-shoes-for-any-weather/winter-and-cold-conditions/"),
}

# Picks built from Ejendals category pages where no industry page exists: (label, category, [models])
RANGES = {
    "cut-oily": ("Ejendals cut-protection range, matched to sharp, oily parts", "cut-protection-gloves",
                 ["43001", "8862", "8846", "8815", "7776"]),
    "plastics": ("Ejendals cut and chemical ranges, matched to trimming, hot molds and chemicals", "cut-protection-gloves",
                 ["43001", "8846", "494", "84520"]),
    "glass-stone": ("Ejendals cut-protection and heavy-duty ranges, matched to heavy sharp materials", "cut-protection-gloves",
                    ["8846", "7773", "2011", "43001"]),
    "scrap": ("Ejendals heavy-duty and cut ranges, matched to sharp scrap and wet, dirty work", "heavy-duty-gloves",
              ["2011", "7773", "9205", "748", "43001"]),
    "vibration": ("Ejendals anti-vibration range", "anti-vibration-gloves", ["9180A", "9183"]),
}

# CRM Industry Detail -> Ejendals industries / ranges, most relevant first
DETAIL_MAP = {
    "Construction - Concrete & Foundation": ["concrete", "bricklaying-masonry", "scaffolding", "vibration"],
    "Construction - Masonry": ["bricklaying-masonry"],
    "Construction - Roofing": ["roofing"],
    "Construction - Siding": ["carpentry", "roofing"],
    "Construction - Electrical": ["electrical"],
    "Construction - Plumbing/HVAC": ["plumbing", "ventilation"],
    "Construction - Finishing (Drywall/Painting/Tile/Carpentry)": ["carpentry", "painting", "tiling"],
    "Construction - Structural Steel/Erection": ["scaffolding", "welding"],
    "Construction - Site Prep/Demolition": ["scaffolding", "vibration", "bricklaying-masonry"],
    "Construction - Residential Building": ["carpentry", "roofing"],
    "Construction - Commercial/Industrial Building": ["scaffolding", "carpentry"],
    "Construction - Heavy/Civil & Utilities": ["scaffolding", "bricklaying-masonry", "vibration"],
    "Construction - Concrete/Masonry/Steel/Roofing": ["bricklaying-masonry", "scaffolding", "roofing"],
    "Construction - General": ["carpentry", "scaffolding"],
    "Manufacturing - Primary Metals/Foundry": ["metalwork", "welding", "vibration"],
    "Manufacturing - Fabricated Metal": ["cut-oily", "metalwork"],
    "Manufacturing - Forging & Stamping": ["cut-oily", "metalwork"],
    "Manufacturing - Machine Shops/Screw Machine": ["cut-oily"],
    "Manufacturing - Tool & Die": ["cut-oily", "metalwork"],
    "Manufacturing - Coating/Heat Treating/Plating": ["metalwork", "life-sciences"],
    "Manufacturing - Machinery": ["cut-oily", "metalwork"],
    "Automotive - OEM Assembly": ["automotive", "cut-oily", "welding"],
    "Automotive - Parts Supplier": ["automotive", "cut-oily", "welding"],
    "Automotive - Body & Trailer": ["automotive", "cut-oily", "welding"],
    "Aerospace": ["cut-oily", "electrical"],
    "Manufacturing - Transportation Equipment": ["automotive", "cut-oily", "welding"],
    "Manufacturing - Plastics & Rubber": ["plastics"],
    "Manufacturing - Chemicals": ["life-sciences"],
    "Manufacturing - Petroleum/Asphalt": ["oil-gas", "life-sciences"],
    "Manufacturing - Glass/Concrete/Stone": ["glass-stone"],
    "Manufacturing - Wood Products": ["carpentry", "forestry"],
    "Manufacturing - Furniture": ["carpentry", "cut-oily"],
    "Manufacturing - Electronics": ["electrical"],
    "Manufacturing - Electrical Equipment": ["electrical", "cut-oily"],
    "Manufacturing - Paper & Packaging": ["logistics", "cut-oily"],
    "Food Processing": ["food-handling"],
    "Food Processing - Meat & Poultry": ["food-handling"],
    "Food Processing - Beverage": ["food-handling", "logistics"],
    "Utilities": ["wind-power", "winter-cold"],
    "Utilities - Electric": ["wind-power", "winter-cold"],
    "Utilities - Gas": ["oil-gas", "winter-cold"],
    "Utilities - Water/Sewer": ["plumbing", "winter-cold"],
    "Oil & Gas": ["oil-gas"], "Oil & Gas Support": ["oil-gas"],
    "Mining & Aggregates": ["mining", "vibration"],
    "Forestry & Logging": ["forestry"],
    "Agriculture/Forestry/Fishing": ["agriculture"],
    "Landscaping": ["agriculture", "forestry", "vibration"],
    "Logistics/Warehousing": ["logistics"], "Couriers & Delivery": ["logistics"],
    "Trucking": ["logistics", "winter-cold"], "Transportation": ["logistics", "winter-cold"],
    "Railway": ["logistics", "winter-cold"], "Airport Work": ["logistics", "winter-cold"],
    "Wholesale Distribution": ["logistics"], "Wholesale - Food": ["logistics", "food-handling"],
    "Wholesale - Auto Parts/Lumber/Metal": ["logistics", "cut-oily"], "Wholesale - Steel Service Center": ["cut-oily", "logistics"],
    "Retail - Building Materials": ["logistics"],
    "Scrap Metal Recycling": ["scrap", "mining"], "Waste Management & Remediation": ["scrap", "cleaning"],
    "Auto Repair": ["logistics", "cut-oily"], "Repair & Maintenance": ["logistics", "cut-oily"],
    "Industrial Machinery Repair": ["metalwork", "cut-oily"],
    "Cleaning & Building Services": ["cleaning"], "Laundry/Linen": ["cleaning"],
    "Staffing Agencies (industrial)": ["logistics", "carpentry"], "Admin & Support Services": ["logistics"],
    "Equipment Rental": ["logistics"],
    "Healthcare - Hospitals": ["health-care", "cleaning"], "Healthcare": ["health-care", "cleaning"],
    "Healthcare - Nursing/Residential": ["health-care", "cleaning"],
    "Hotel, Restaurant & Catering": ["hotel-restaurant"], "Hotels": ["hotel-restaurant", "cleaning"],
    "Public Administration (Municipal)": ["plumbing", "winter-cold", "vibration"],
}
GROUP_MAP = {
    "Metalworking & Machinery": ["cut-oily", "metalwork"], "Construction": ["carpentry", "scaffolding"],
    "Other Manufacturing": ["cut-oily", "logistics"], "Wholesale & Distribution": ["logistics"],
    "Logistics & Transportation": ["logistics", "winter-cold"], "Plastics, Rubber & Chemicals": ["plastics"],
    "Automotive & Aerospace": ["automotive", "cut-oily", "welding"],
    "Agriculture, Forestry & Landscaping": ["agriculture", "forestry"],
    "Services, Repair & Staffing": ["logistics", "cut-oily"], "Healthcare": ["health-care", "cleaning"],
    "Food Processing": ["food-handling"], "Public Sector & Municipal": ["plumbing", "winter-cold"],
    "Waste & Recycling": ["scrap"], "Energy, Utilities & Mining": ["wind-power", "mining", "winter-cold"],
    "Retail, Hospitality & Other": ["cleaning", "hotel-restaurant"],
}


def _clean(name):
    return re.sub(r"\s+", " ", name.replace("®", "").replace("™", "")).strip()

def _load(folder):
    out = {}
    for f in sorted(os.listdir(os.path.join(BASE, folder))):
        if not f.endswith(".txt"): continue
        rows = {"GLOVE": [], "SHOE": [], "HAZARD": []}
        for line in open(os.path.join(BASE, folder, f), encoding="utf-8"):
            parts = [p.strip() for p in line.strip().split("|")]
            if parts and parts[0] in rows:
                rows[parts[0]].append(parts[1:])
        out[f[:-4]] = rows
    return out

IND = _load("industries")
CAT = _load("categories")

# product index: model -> dict(name, desc, features, url)
PRODUCTS = {}
for cat, rows in CAT.items():
    for p in rows["GLOVE"]:
        model = p[0].upper()
        PRODUCTS.setdefault(model, dict(model=model, name=_clean(p[1]), desc=p[2] if len(p) > 2 else "",
                                        features=p[3] if len(p) > 3 else "",
                                        url=f"{SITE}/products/gloves/{cat}/", kind="glove"))
for key, rows in IND.items():
    for kind in ("GLOVE", "SHOE"):
        for p in rows[kind]:
            model = p[0].upper()
            if model not in PRODUCTS:
                PRODUCTS[model] = dict(model=model, name=_clean(p[1]), desc=p[2] if len(p) > 2 else "", features="",
                                       url=SITE + INDUSTRY_PAGES[key][1], kind=kind.lower())
# verified product pages (from the rep's list)
for model, url in {"295": "/products/gloves/all-round-work-gloves/295/", "43001": "/products/gloves/cut-protection-gloves/43001/",
                   "9180A": "/products/gloves/anti-vibration-gloves/9180a/", "8846": "/products/gloves/cut-protection-gloves/8846/",
                   "118A": "/products/gloves/welding-gloves/118a/"}.items():
    if model in PRODUCTS: PRODUCTS[model]["url"] = SITE + url

POPULAR = ["43001", "295", "9180A", "8846", "118A"]   # the rep's best sellers
COLD = ["295", "9122", "8854R", "9190"]


def recommend(detail, group, outdoor=False, winter=False, n_gloves=6, n_shoes=3):
    keys = DETAIL_MAP.get(detail) or GROUP_MAP.get(group) or ["logistics"]
    gloves, shoes, hazards, sources = [], [], [], []
    seen = set()
    for k in keys:
        if k in RANGES:
            label, cat, models = RANGES[k]
            src = (label, f"{SITE}/products/gloves/{cat}/")
            for m in models:
                if m in PRODUCTS and m not in seen:
                    gloves.append(dict(PRODUCTS[m], why_source=label)); seen.add(m)
        else:
            name, path = INDUSTRY_PAGES[k]
            src = (f"Ejendals: {name}", SITE + path)
            for p in IND[k]["GLOVE"]:
                m = p[0].upper()
                if m in PRODUCTS and m not in seen and PRODUCTS[m]["kind"] == "glove":
                    gloves.append(dict(PRODUCTS[m], why_source=f"Ejendals recommends for {name.lower()}")); seen.add(m)
            for p in IND[k]["SHOE"]:
                m = p[0].upper()
                if m in PRODUCTS and m not in seen:
                    shoes.append(PRODUCTS[m]); seen.add(m)
            hazards += [h[0] for h in IND[k]["HAZARD"]]
        if src not in sources: sources.append(src)
    # collections without model numbers (e.g. concrete page) are skipped as gloves; fill from popular if thin
    gloves = [g for g in gloves if re.search(r"\d", g["model"])]
    if outdoor and winter and not any(g["model"] in COLD for g in gloves[:3]):
        gloves.insert(1 if gloves else 0, dict(PRODUCTS["295"], why_source="for cold, wet winter work"))
    for m in POPULAR:
        if len(gloves) >= 3: break
        if m not in {g["model"] for g in gloves}:
            gloves.append(dict(PRODUCTS[m], why_source="a best-selling Tegera style"))
    return dict(gloves=gloves[:n_gloves], shoes=shoes[:n_shoes], hazards=list(dict.fromkeys(hazards))[:6], sources=sources)


if __name__ == "__main__":
    print(len(PRODUCTS), "products;", len(IND), "industry pages")
    for d in ["Construction - Roofing", "Manufacturing - Forging & Stamping", "Food Processing - Meat & Poultry",
              "Trucking", "Manufacturing - Plastics & Rubber", "Scrap Metal Recycling"]:
        r = recommend(d, "", outdoor="Trucking" in d, winter=True)
        print(d, "->", [g["name"] for g in r["gloves"][:3]], "| shoes:", [s["name"] for s in r["shoes"]])
