from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, DateTime, String, BigInteger

engine = create_engine('postgresql://postgres:1@localhost/zxcbot')

Session = sessionmaker(bind=engine)

Base = declarative_base()


class Mutes(Base):
    __tablename__ = 'mutes'
    id = Column(Integer, primary_key=True)
    user = Column(BigInteger)
    end_date = Column(DateTime)
    guild = Column(BigInteger)


class Warns(Base):
    __tablename__ = 'warns'
    id = Column(Integer, primary_key=True)
    reason = Column(String)
    username = Column(String)
    given_date = Column(DateTime)
    end_date = Column(DateTime)
    given_by = Column(BigInteger)
    index = Column(Integer)
    guild = Column(BigInteger)

class Configs(Base):
    __tablename__ = 'configs'
    id = Column(Integer, primary_key=True)
    guild = Column(BigInteger)
    voice_channel_id = Column(BigInteger)
    voice_category_id = Column(BigInteger)
    autorole_id = Column(BigInteger)
    muted_role_id = Column(BigInteger)
    mute_reconnect_id = Column(BigInteger)
    log_channel_id = Column(BigInteger)
    reports_channel_id = Column(BigInteger)
    tickets_category_id = Column(BigInteger)
    warns_max = Column(Integer)
    warns_duration = Column(Integer)


class EmojiRoles(Base):
    __tablename__ = 'emoji_roles'
    id = Column(Integer, primary_key=True)
    guild = Column(BigInteger)
    role = Column(BigInteger)
    emoji = Column(String)

def create_tables():
    try:
        Base.metadata.create_all(engine)
    except exc.OperationalError:
        pass
