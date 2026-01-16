from app.services.google_sheets import google_sheets
sh = google_sheets._get_spreadsheet()
for s in sh.worksheets():
    print(f"Sheet: {s.title}")
    print(f"Headers: {s.row_values(1)}")
    print("-" * 20)
