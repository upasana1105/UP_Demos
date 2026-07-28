def query_user_records(db, user_input):
    # SECURE: Parameterized prepared SQL query
    query = "SELECT * FROM users WHERE id = %s"
    return db.query(query, (user_input,))
