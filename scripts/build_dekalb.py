"""Build counties/dekalb.json from the parsed DeKalb delinquent CSV (tax-dekalb.csv,
produced by the gascrape tax pipeline from the 9,915-page DQ205GADEK mainframe PDF).
AGGREGATE ONLY — owner names & addresses are never written out. Emits the same
canonical schema as the other live counties. Re-run when the pipeline refreshes the CSV.
Usage: python build_dekalb.py /path/to/tax-dekalb.csv
"""
import sys, json, csv
from collections import defaultdict

def build(csv_path, out_path, run_date="2026-06-17"):
    total_rows = 0; total_due = 0.0
    owners = set(); bills = set()
    by_year = defaultdict(lambda: [0, 0.0])
    flags = defaultdict(int)
    bands = {"$0–100":0,"$100–500":0,"$500–1K":0,"$1K–5K":0,"$5K+":0}
    amts = []
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            try: b = float(r["total_due"])
            except (TypeError, ValueError): b = 0.0
            total_rows += 1; total_due += b; amts.append(b)
            owners.add(r["owner"]); bills.add(r["bill_no"])
            y = (r["tax_year"] or "").strip()
            if y.isdigit(): by_year[y][0]+=1; by_year[y][1]+=b
            fl = (r["flag"] or "").strip() or "(blank)"
            flags[fl]+=1
            bands["$0–100" if b<100 else "$100–500" if b<500 else "$500–1K" if b<1000
                  else "$1K–5K" if b<5000 else "$5K+"] += 1
    amts.sort()
    data = {
        "county":"dekalb","name":"DeKalb","fips":"13089","seat":"Decatur",
        "is_live":True,"status":"LIVE PRODUCTION","has_amounts":True,
        "adapter":"dekalb_pdf","legal_organ":"DeKalb County Tax Commissioner",
        "source":"DeKalb County Tax Commissioner — DQ205GADEK Delinquent Tax Cross-Reference (mainframe PDF)",
        "run_date":run_date,"generated_at":run_date,
        "records":total_rows,"owners":len(owners),"parcels":len(bills),
        "total_due":round(total_due,2),
        "by_year":{y:{"records":c,"due":round(v,2)} for y,(c,v) in sorted(by_year.items())},
        "amount_bands":bands,
        "flags":dict(sorted(flags.items(), key=lambda kv:-kv[1])),
        "median_due":round(amts[len(amts)//2],2) if amts else 0.0,
        "largest_single_bill":round(max(amts),2) if amts else 0.0,
        "note":("Full delinquent tax roll parsed from the county's 9,915-page DQ205GADEK "
                "mainframe report. Each row is one unpaid charge (a bill can carry several). "
                "Aggregate figures only — no owner names or addresses are published.")
    }
    json.dump(data, open(out_path,"w",encoding="utf-8"), indent=2)
    return data

if __name__ == "__main__":
    d = build(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "src/data/counties/dekalb.json")
    print(f"records={d['records']:,} owners={d['owners']:,} parcels(bills)={d['parcels']:,} total_due=${d['total_due']:,.2f}")
    print(f"median=${d['median_due']:,.2f} largest=${d['largest_single_bill']:,.2f}")
    print("flags:", d['flags'])
    print("bands:", d['amount_bands'])
