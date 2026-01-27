
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.getcwd())

from app.services.google_sheets import google_sheets

def delete_unassigned_project():
    try:
        sh = google_sheets.get_worksheet("projects")
        rows = sh.get_all_records()
        header = sh.row_values(1)
        
        # Find row with empty name or 'Unassigned'
        for i, row in enumerate(rows):
            name = str(row.get('project_name', '')).strip()
            if name.lower() == 'unassigned' or name == '':
                row_idx = i + 2
                print(f"Deleting project at row {row_idx}: {name}")
                # Set is_deleted = True
                is_del_idx = -1
                for j, h in enumerate(header):
                    if h.lower() == 'is_deleted':
                        is_del_idx = j + 1
                        break
                
                if is_del_idx != -1:
                    sh.update_cell(row_idx, is_del_idx, "TRUE")
                    print("Updated is_deleted to TRUE")
                else:
                    print("is_deleted column not found")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_unassigned_project()
