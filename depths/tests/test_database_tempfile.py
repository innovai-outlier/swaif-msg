from pathlib import Path
from depths.core.database import SwaifDatabase


def test_temp_db_created_and_removed():
    db = SwaifDatabase(":memory:")
    assert db._temp_db is not None
    temp_path = Path(db._temp_db)
    assert temp_path.exists()
    db.cleanup()
    assert not temp_path.exists()
