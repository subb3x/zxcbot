from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, DateTime, String, BigInteger

engine = create_engine('postgresql://postgres:1@localhost/zxcbot')

Session = sessionmaker(bind=engine)

Base = declarative_base()


class Mutes(Base):
    __tablename__ = 'mutes'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    end_date = Column(DateTime)
    guild = Column(BigInteger)


class Warns(Base):
    __tablename__ = 'warns'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    end_date = Column(DateTime)
    guild = Column(BigInteger)


def create_tables():
    try:
        Base.metadata.create_all(engine)
    except exc.OperationalError:
        pass
