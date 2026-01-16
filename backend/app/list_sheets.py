from app.services.google_sheets import google_sheets
sh = google_sheets._get_spreadsheet()
print("Worksheets found:")
for s in sh.worksheets():
    print(f"- {s.title}")
