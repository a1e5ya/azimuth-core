"""
Quick script to check transaction amounts in database
"""
from app.models.database import Transaction, SessionLocal

db = SessionLocal()
try:
    trans = db.query(Transaction).limit(10).all()
    print("=" * 50)
    print("Sample Transaction Amounts:")
    print("=" * 50)
    for t in trans:
        print(f"Amount: {t.amount}")
        print(f"  Type: {type(t.amount)}")
        print(f"  Merchant: {t.merchant}")
        print(f"  Main Category: {t.main_category}")
        print("-" * 50)
finally:
    db.close()