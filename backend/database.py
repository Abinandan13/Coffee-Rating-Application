"""
Database configuration and SQLAlchemy ORM models for Coffee Rating Application.
Module 3: Database Integration
"""

import os
from typing import Generator
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ==============================================================================
# Database Configuration & Engine
# ==============================================================================
# Default database location in the backend folder: backend/coffee_rating.db
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coffee_rating.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# SQLite connection args (check_same_thread=False allows FastAPI multi-threaded requests)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==============================================================================
# SQLAlchemy ORM Model
# ==============================================================================
class Coffee(Base):
    """
    Coffee database model.
    Table: coffees
    Fields:
      - id: String primary key (e.g., 'cappuccino', 'iced-latte', 'espresso', 'cold-brew')
      - name: String display name
      - description: String flavor description
      - image_url: String URL to coffee photo
      - votes: Integer total votes, default 0
    """
    __tablename__ = "coffees"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    votes = Column(Integer, default=0, nullable=False)

    def to_dict(self) -> dict:
        """Converts model instance to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "votes": self.votes,
        }


# ==============================================================================
# Initial Seed Data
# ==============================================================================
INITIAL_COFFEES = [
    {
        "id": "cappuccino",
        "name": "Cappuccino",
        "description": "A harmonious balance of rich espresso, velvety steamed milk, and a luxurious cloud of foam.",
        "image_url": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?auto=format&fit=crop&w=600&q=80",
        "votes": 0,
    },
    {
        "id": "iced-latte",
        "name": "Iced Latte",
        "description": "Chilled espresso poured gently over crisp iced milk for a refreshing, silky-smooth coffee experience.",
        "image_url": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=600&q=80",
        "votes": 0,
    },
    {
        "id": "espresso",
        "name": "Espresso",
        "description": "An intense, concentrated shot crowned with a dense, hazelnut-toned golden crema.",
        "image_url": "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?auto=format&fit=crop&w=600&q=80",
        "votes": 0,
    },
    {
        "id": "cold-brew",
        "name": "Cold Brew",
        "description": "Slow-steeped in cold water for 18 hours to unlock ultra-smooth, naturally sweet, low-acid notes.",
        "image_url": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=600&q=80",
        "votes": 0,
    },
]


# ==============================================================================
# Database Dependency & Initialization
# ==============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session
    and ensures it is safely closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None, session_factory=None):
    """
    Creates tables if they do not exist and populates the 4 initial coffees
    only if they are not already present in the database.
    Preserves existing vote counts upon server restart.
    """
    eng = target_engine or engine
    sf = session_factory or SessionLocal

    # Create tables
    Base.metadata.create_all(bind=eng)

    # Seed initial data without overwriting existing votes
    db: Session = sf()
    try:
        for item in INITIAL_COFFEES:
            existing = db.query(Coffee).filter(Coffee.id == item["id"]).first()
            if existing is None:
                new_coffee = Coffee(
                    id=item["id"],
                    name=item["name"],
                    description=item["description"],
                    image_url=item["image_url"],
                    votes=0,
                )
                db.add(new_coffee)
        db.commit()
    finally:
        db.close()
