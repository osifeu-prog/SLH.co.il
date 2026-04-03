from backend.app.db.database import engine, Base
from backend.app.models.user import User

def main():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    main()
