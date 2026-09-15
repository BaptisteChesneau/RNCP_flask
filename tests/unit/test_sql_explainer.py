from controllers.admin_controller import generate_sql_explanation

def test_sql_explanation_queries():
    assert "SELECT query" in generate_sql_explanation("SELECT * FROM client")
    assert "INSERT query" in generate_sql_explanation("INSERT INTO client VALUES (...)")
    assert "UPDATE query" in generate_sql_explanation("UPDATE client SET nom='A'")
    assert "DELETE query" in generate_sql_explanation("DELETE FROM client WHERE id=1")