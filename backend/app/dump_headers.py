from app.services.google_sheets import google_sheets
import json
sh = google_sheets._get_spreadsheet()
results = {}
for s in sh.worksheets():
    results[s.title] = s.row_values(1)

with open("headers_dump.json", "w") as f:
    json.dump(results, f, indent=4)
print("Headers dumped to headers_dump.json")
