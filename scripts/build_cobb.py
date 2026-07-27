"""Build counties/cobb.json from the Cobb County Delinquent Tax List (text PDF).
AGGREGATE ONLY — parcel/amount/year used; owner names & addresses never written
(PII untouched). Re-run monthly on the new PDF.
Usage: python build_cobb.py "/path/to/Cobb ... Delinquent Tax List MM.DD.YYYY.pdf"
"""
import sys, json, re
from collections import defaultdict
import pypdf

ROW = re.compile(r'^(\d{9,12})\s+.*?\s+\$([\d,]+\.\d{2})\s+(\d{4})\s*$')

def build(pdf_path, out_path, run_date="2026-07-01"):
    total_rows = 0; total_amt = 0.0; parcels = set()
    by_year = defaultdict(lambda: [0, 0.0]); amts = []
    bands = {"$0–100":0,"$100–500":0,"$500–1K":0,"$1K–5K":0,"$5K+":0}
    for pg in pypdf.PdfReader(pdf_path).pages:
        for ln in (pg.extract_text() or "").splitlines():
            m = ROW.match(ln.strip())
            if not m: continue
            amt = float(m.group(2).replace(",", ""))
            total_rows += 1; total_amt += amt; amts.append(amt); parcels.add(m.group(1))
            by_year[m.group(3)][0] += 1; by_year[m.group(3)][1] += amt
            b = amt
            bands["$0–100" if b<100 else "$100–500" if b<500 else "$500–1K" if b<1000
                  else "$1K–5K" if b<5000 else "$5K+"] += 1
    amts.sort()
    data = {"county":"cobb","name":"Cobb","fips":"13067","seat":"Marietta","is_live":True,
        "status":"LIVE PRODUCTION","has_amounts":True,"adapter":"cobb_pdf",
        "legal_organ":"Cobb County Tax Commissioner",
        "source":"Cobb County Tax Commissioner — Monthly Delinquent Tax List (text PDF)",
        "run_date":run_date,"generated_at":run_date,"records":total_rows,"owners":None,
        "parcels":len(parcels),"total_due":round(total_amt,2),
        "by_year":{y:{"records":c,"due":round(v,2)} for y,(c,v) in sorted(by_year.items()) if y.isdigit()},
        "amount_bands":bands,"flags":None,
        "median_due":round(amts[len(amts)//2],2) if amts else 0.0,
        "largest_single_bill":round(max(amts),2) if amts else 0.0,
        "note":("Delinquent tax roll from the county's monthly published PDF. Each row is one "
                "unpaid bill (a parcel can carry multiple years). Aggregate figures only — no "
                "owner names or addresses are published.")}
    json.dump(data, open(out_path,"w",encoding="utf-8"), indent=2)
    return data

if __name__ == "__main__":
    d = build(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else "src/data/counties/cobb.json")
    print(f"records={d['records']:,} parcels={d['parcels']:,} total_due=${d['total_due']:,.2f}")
