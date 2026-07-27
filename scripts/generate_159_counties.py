"""Generate 100% audit-proof 159 Georgia County datasets for GAScout.

Safety rule: if a county JSON already exists and has is_live=true,
that file is PRESERVED and its real data is used for the manifest.
Only planned/non-existent counties get placeholder metadata generated.
"""

import json
from pathlib import Path

REGISTRY_PATH = Path("C:/dev/georgia/gascrape-project/gascrape-project/gascrape/data/counties.json")
raw_counties = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

# Load real DeKalb dashboard data
DEKALB_PATH = Path("C:/dev/georgia/gascrape-site/src/data/dashboard.json")
dekalb_real = json.loads(DEKALB_PATH.read_text(encoding="utf-8"))

out_dir = Path("C:/dev/georgia/gascrape-site/src/data/counties")
out_dir.mkdir(parents=True, exist_ok=True)

manifest = []
skipped_live = []

for county_info in raw_counties:
    name = county_info["name"]
    slug = name.lower().replace(" ", "_")
    fips = county_info["fips"]
    seat = county_info["seat"]
    adapter = county_info.get("adapter", "gpn")
    status = county_info.get("status", "planned")
    legal_organ = county_info.get("legal_organ") or f"{name.title()} Legal Organ"

    county_file = out_dir / f"{slug}.json"

    # ── Safety gate: never overwrite a live county's real data ──────────
    if county_file.exists():
        existing = json.loads(county_file.read_text(encoding="utf-8"))
        if existing.get("is_live"):
            # Preserve the file untouched; pull manifest entry from its real data
            manifest.append({
                "slug": slug,
                "name": existing.get("name", name.title()),
                "fips": existing.get("fips", fips),
                "seat": existing.get("seat", seat),
                "is_live": True,
                "status": existing.get("status", "LIVE PRODUCTION"),
                "legal_organ": existing.get("legal_organ", legal_organ),
                "records": existing.get("records", 0),
                "total_due": existing.get("total_due", 0.0),
            })
            skipped_live.append(slug)
            continue

    # ── DeKalb special-case: always rebuild from dashboard.json ─────────
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
    else:
        # Planned county: audit-proof metadata only (NO stubbed numbers)
        data = {
            "county": slug,
            "name": name.title(),
            "fips": fips,
            "seat": seat,
            "is_live": False,
            "status": "ADAPTER PLANNED",
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
            "status": "ADAPTER PLANNED",
            "legal_organ": legal_organ,
            "records": 0,
            "total_due": 0.0
        })

    county_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

# Sort manifest: Live counties first, then alphabetical
manifest.sort(key=lambda x: (not x["is_live"], x["name"]))

(out_dir.parent / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

live_count = len([c for c in manifest if c["is_live"]])
planned_count = len([c for c in manifest if not c["is_live"]])
print(f"Registry updated: {live_count} live counties, {planned_count} planned.")
if skipped_live:
    print(f"Preserved live county files (not overwritten): {', '.join(skipped_live)}")
