"""
Simple FastAPI application exposing CRUD endpoints for the Berita model.

Example curl commands:

# List all berita
curl -X GET http://localhost:8000/berita

# Retrieve a berita by ID
curl -X GET http://localhost:8000/berita/1

# Create a new berita (requires API key)
curl -X POST http://localhost:8000/berita \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: supersecret' \
     -d '{
           "judul": "Judul Baru",
           "isi_berita": "Isi berita...",
           "tanggal": "2024-05-28",
           "kategori": "Teknologi"
         }'

# Update an existing berita (requires API key)
curl -X PUT http://localhost:8000/berita/1 \
     -H 'Content-Type: application/json' \
     -H 'X-API-Key: supersecret' \
     -d '{
           "judul": "Judul Diperbarui",
           "isi_berita": "Isi terbaru...",
           "tanggal": "2024-05-30",
           "kategori": "Teknologi"
         }'

# Delete a berita (requires API key)
curl -X DELETE http://localhost:8000/berita/1 \
     -H 'X-API-Key: supersecret'
"""

from datetime import date
from typing import Generator, List

from fastapi import Depends, FastAPI, HTTPException, Header, status
from pydantic import BaseModel, Field
from sqlalchemy import Column, Date, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./berita.db"
API_KEY = "supersecret"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Berita(Base):
    __tablename__ = "berita"

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(255), nullable=False)
    isi_berita = Column(Text, nullable=False)
    tanggal = Column(Date, nullable=False)
    kategori = Column(String(100), nullable=False)


class BeritaBase(BaseModel):
    judul: str = Field(..., min_length=1, max_length=255)
    isi_berita: str = Field(..., min_length=1)
    tanggal: date
    kategori: str = Field(..., min_length=1, max_length=100)


class BeritaCreate(BeritaBase):
    pass


class BeritaUpdate(BeritaBase):
    pass


class BeritaRead(BeritaBase):
    id: int

    class Config:
        orm_mode = True


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )


app = FastAPI(title="Berita API", description="CRUD API for managing Berita")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/berita", response_model=List[BeritaRead])
def list_berita(db: Session = Depends(get_db)) -> List[BeritaRead]:
    berita_list = db.query(Berita).all()
    return berita_list


@app.get("/berita/{berita_id}", response_model=BeritaRead)
def get_berita(berita_id: int, db: Session = Depends(get_db)) -> BeritaRead:
    berita = db.query(Berita).filter(Berita.id == berita_id).first()
    if berita is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Berita not found")
    return berita


@app.post("/berita", response_model=BeritaRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_api_key)])
def create_berita(berita_in: BeritaCreate, db: Session = Depends(get_db)) -> BeritaRead:
    berita = Berita(**berita_in.dict())
    db.add(berita)
    db.commit()
    db.refresh(berita)
    return berita


@app.put("/berita/{berita_id}", response_model=BeritaRead, dependencies=[Depends(require_api_key)])
def update_berita(berita_id: int, berita_in: BeritaUpdate, db: Session = Depends(get_db)) -> BeritaRead:
    berita = db.query(Berita).filter(Berita.id == berita_id).first()
    if berita is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Berita not found")

    for field, value in berita_in.dict().items():
        setattr(berita, field, value)

    db.commit()
    db.refresh(berita)
    return berita


@app.delete("/berita/{berita_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)])
def delete_berita(berita_id: int, db: Session = Depends(get_db)) -> None:
    berita = db.query(Berita).filter(Berita.id == berita_id).first()
    if berita is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Berita not found")

    db.delete(berita)
    db.commit()
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
