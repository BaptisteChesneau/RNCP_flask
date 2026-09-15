def validate_id(id_value, id_name="ID"):
    if not isinstance(id_value, int) or id_value <= 0:
        return f"{id_name} doit être un entier positif."
    return None

def test_validate_id_valid():
    assert validate_id(5) is None

def test_validate_id_invalid():
    assert "entier positif" in validate_id("invalid_id")
    assert "entier positif" in validate_id(-3)