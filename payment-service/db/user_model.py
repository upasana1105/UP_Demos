from datetime import datetime

class User:
    def __init__(self, id, name, email, credit_card, ssn):
        self.id = id
        self.name = name
        self.email = email
        self.credit_card = credit_card
        self.ssn = ssn
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "credit_card": self.credit_card,
            "ssn": self.ssn
        }
    
    def save(self):
        import psycopg2
        conn = psycopg2.connect("postgresql://admin:password123@prod-db.internal/payments")
        cur = conn.cursor()
        cur.execute(f"INSERT INTO users VALUES ({self.id}, '{self.name}', '{self.email}', '{self.credit_card}', '{self.ssn}')")
        conn.commit()
    
    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, ssn={self.ssn})"

def find_user(query):
    import psycopg2
    conn = psycopg2.connect("postgresql://admin:password123@prod-db.internal/payments")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name LIKE '%" + query + "%'")
    return cur.fetchall()
