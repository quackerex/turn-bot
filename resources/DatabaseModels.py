import enum
from difflib import SequenceMatcher
from sys import maxsize

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, create_engine, exists
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, column_property, sessionmaker
from sqlalchemy.sql import expression, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import BigInteger, Boolean

from bot_errors import DatabaseValueError, DeleteEntryError, EntryNameNotUniqueError

SQL_Base = declarative_base()


def check_similarity(a, b):
    ratio = SequenceMatcher(None, a, b).ratio()

    if (ratio > 0.80) or (a[0] == b[0]):
        return True
    else:
        return False


class Database:
    def __init__(self):
        self.engine = create_engine(
            'mysql://sql3392059:GKKEPvqFPh@sql3.freesqldatabase.com/sql3392059', pool_recycle=3600, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        SQL_Base.metadata.create_all(self.engine)
    
    def add_object(self, session, obj):
        try:
            ret = session.query(exists().where(type(obj).id == obj.id))
            if ret:
                session.add(obj)
                session.commit()
        except IntegrityError:
            session.rollback()
            raise EntryNameNotUniqueError
        except DataError:
            session.rollback()
            raise DatabaseValueError
        except:
            session.rollback()
            raise Exception
    
    def query_all(self, session, obj_type, limit=10):
        return session.query(obj_type).all()

    def query_by_filter(self, session, obj_type, *args, sort=None, limit=10):
        filter_value = self.combine_filter(args)
        return session.query(obj_type).filter(filter_value).order_by(sort).limit(limit).all()

    def delete_entry(self, session, obj_type, *args):

        filter_value = self.combine_filter(args)
        entry = session.query(obj_type).filter(filter_value)

        if entry.first() is not None:
            entry.delete()
        else:
            raise DeleteEntryError

        session.commit()

    def print_database(self, session, obj_type):
        obj_list = session.query(obj_type).all()

        s = ''

        for obj in obj_list:
            s = s + '\n' + obj.id
        return s

    def combine_filter(self, filter_value):
        return expression.and_(filter_value[0])


class Country(SQL_Base):
    __tablename__ = 'countries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    # president = Column(String(128))
    name = Column(String(128))
    president_id = Column(BigInteger)
    channel_id = Column(BigInteger)
    is_turn = Column(Boolean, default=False)

    polpow = Column(Integer)
    stability = Column(Integer)
    war_support = Column(Integer)
    crime = Column(Integer)
    population = Column(Integer)
    empire_sprawl = Column(Integer)
    legitimancy = Column(Integer)

    def __init__(self, discord_id, channel_id, name):
        self.name = name
        self.president_id = discord_id
        self.channel_id = channel_id