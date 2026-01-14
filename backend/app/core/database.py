
from app.core.sheets_db import get_sheets_db

# Dummy Base for compatibility with existing imports in models_db.py
class Base:
    pass

def get_db():
    """
    Yields a SheetsDB instance instead of a SQLAlchemy Session.
    This maintains compatibility with Depends(get_db).
    """
    db = get_sheets_db()
    try:
        yield db
    finally:
        # Commit any pending changes automatically if needed, 
        # or leave it to the routers.
        db.commit()
