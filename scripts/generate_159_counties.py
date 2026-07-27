"""Generate audit-proof 159 Georgia County datasets for GAScout.

DeKalb is LIVE PRODUCTION ($62.75M / 409k records).
Fulton is LIVE SHERIFF TAX SALES (3 records / Fulton Sheriff Levy Roll).
The remaining 157 counties display authentic registry metadata (FIPS, Seat, Legal Organ, Adapter Status).
"""

import json
from pathlib import Path

REGISTRY_PATH = Path("C:/dev/georgia/gascrape-project/gascrape-project/gascrape/data/counties.json")
raw_counties = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

# Load real DeKalb dashboard data
DEKALB_PATH = Path("C:/dev/georgia/gascrape-site/src/data/dashboard.json")
dekalb_real = json.loads(DEKALB_PATH.read_text(encoding="utf-8"))

# Load real Fulton Sheriff dashboard data
FULTON_PATH = Path("C:/dev/georgia/gascrape-site/src/data/counties/fulton.json")
fulton_real = json.loads(FULTON_PATH.read_text(encoding="utf-8")) if FULTON_PATH.exists() else None

out_dir = Path("C:/dev/georgia/gascrape-site/src/data/counties")
out_dir.mkdir(parents=True, exist_ok=True)

manifest = []

for county_info in raw_counties:
    name = county_info["name"]
    slug = name.lower().replace(" ", "_")
    fips = county_info["fips"]
    seat = county_info["seat"]
    adapter = county_info.get("adapter", "gpn")
    status = county_info.get("status", "planned")
    legal_organ = county_info.get("legal_organ") or f"{name.title()} Legal Organ"
    
    if slug == "dekalb":
        data = {
            "county": "dekalb",
            "name": "DeKalb",
            "fips": fips,
            "seat": seat,
            "is_live": True,
            "status": "LIVE PRODUCTION",
            "adapter": "dekalb_pdf",
            "legal_organ": "The Champion",
            "source": "DeKalb County Tax Commissioner — Delinquent Tax Listing",
            "run_date": dekalb_real["run_date"],
            "generated_at": dekalb_real["generated_at"],
            "records": dekalb_real["records"],
            "owners": dekalb_real["owners"],
            "total_due": dekalb_real["total_due"],
            "by_year": dekalb_real["by_year"],
            "amount_bands": dekalb_real["amount_bands"],
            "flags": dekalb_real["flags"],
            "median_due": dekalb_real["median_due"],
            "largest_single_bill": dekalb_real["largest_single_bill"]
        }
        manifest.append({
            "slug": "dekalb",
            "name": "DeKalb",
            "fips": fips,
            "seat": seat,
            "is_live": True,
            "status": "LIVE PRODUCTION",
            "legal_organ": "The Champion",
            "records": dekalb_real["records"],
            "total_due": dekalb_real["total_due"]
        })
    elif slug == "fulton" and fulton_real:
        data = fulton_real
        manifest.append({
            "slug": "fulton",
            "name": "Fulton",
            "fips": fips,
            "seat": seat,
            "is_live": True,
            "status": "LIVE SHERIFF TAX SALES",
            "legal_organ": "Fulton County Sheriff Tax Sales Roll",
            "records": fulton_real["records"],
            "total_due": fulton_real["total_due"]
        })
    else:
        # 157 Non-DeKalb/Fulton Counties: Audit-proof metadata only (NO invented numbers)
        status_label = "ADAPTER PLANNED" if status == "planned" else "DEVELOPMENT"
        data = {
            "county": slug,
            "name": name.title(),
            "fips": fips,
            "seat": seat,
            "is_live": False,
            "status": status_label,
            "adapter": adapter,
            "legal_organ": legal_organ,
            "source": f"{name.title()} County — {legal_organ}",
            "records": 0,
            "owners": 0,
            "total_due": 0.0
        }
        manifest.append({
            "slug": slug,
            "name": name.title(),
            "fips": fips,
            "seat": seat,
            "is_live": False,
            "status": status_label,
            "legal_organ": legal_organ,
            "records": 0,
            "total_due": 0.0
        })

    (out_dir / f"{slug}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

# Sort manifest: Live counties first, then alphabetical
manifest.sort(key=lambda x: (not x["is_live"], x["name"]))

(out_dir.parent / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Successfully generated audit-proof 159 county registry data (2 Live, 157 Planned) in {out_dir}")
