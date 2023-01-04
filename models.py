"""
Models
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import DateTime
import pathlib as pl
from datetime import datetime

Base = declarative_base()

class GoogleFiles(Base):
  

    __tablename__ = "googlefiles"
    id = Column(Integer, primary_key=True)
    file_name = Column(String(50))
    file_extension = Column(String(50))
    file_id = Column(String(100))
    img_class = Column(Integer)
    pred = Column(Boolean, default=False)
    created = Column(DateTime, default=datetime.now())


def create_db():
    path = pl.Path("\\\DS.db")
    if not path.is_file():
        engine = create_engine('sqlite:///DS.db', connect_args={'check_same_thread': False})
        Base.metadata.create_all(engine)
