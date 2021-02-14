from resources.DatabaseModels import Database

from resources.DatabaseModels import Country
from sqlalchemy import func
from bot_errors import CountryInDBError, CountryLookUpError, CountryNotFound, DatabaseValueError, EntryNameNotUniqueError
from sqlalchemy.exc import DataError, IntegrityError

class DatabaseInterface:

    def __init__(self):
        self.database = Database()

    # Search stuff
    def get_all(self, obj_type, limit=16):
        session = self.database.Session()

        try:
            country_list = self.database.query_all(session, obj_type, limit)
        finally:
            session.close()
        
        return country_list
    
    def find_country_by_channel(self, channel_id:int):
        expr = Country.channel_id == channel_id
        session = self.database.Session()

        try:
            player = self.database.query_by_filter(session, Country, expr)[0]
        except IndexError as e:
            print(e)
            raise CountryNotFound
        finally:
            session.close()

        return player
    
    def find_country_by_player(self, player_id):
        session = self.database.Session()
        expr = Country.president_id == player_id

        try:
            player = self.database.query_by_filter(session, Country, expr)[0]
        except IndexError:
            raise CountryNotFound
        finally:
            session.close()

        return player

    def get_last_turn(self, country=Country):
        session = self.database.Session()
        expr = Country.is_turn == True

        try:
            country = self.database.query_by_filter(session, Country, expr)[0]
        finally:
            session.close()

        return country
    
    def get_all_the_channels(self, obj_type=Country, limit=16):
        session = self.database.Session()

        try:
            channel_list = obj_type.select()
        finally:
            session.close()

        return channel_list


    # Add stuff
    def add_country(self, channel_id, discord_id, name):
        session = self.database.Session()
        try:
            country = self.find_country_by_player(discord_id)
            if (discord_id is not None) and (discord_id == country.president_id):
                raise CountryInDBError
            else:
                raise CountryNotFound

        except CountryNotFound:
            try:
                self.find_country_by_channel(channel_id)
                raise CountryInDBError
            except CountryNotFound:
                country = Country(discord_id=discord_id, channel_id=channel_id, name=name)
                self.database.add_object(session,country)
        
        finally:
            session.close()

        return country

    # Change/remove stuff
    def change_the_turn(self, country):
        m_session = self.database.Session()
        # last_turn = self.get_last_turn()
        # c = self.find_country_by_channel(country.channel_id)
        last_turn = m_session.query(Country).filter(Country.is_turn == True).first()
        c = m_session.query(Country).filter(country.channel_id == Country.channel_id).first()
        try:
            last_turn.is_turn = False
            c.is_turn = True
            
            m_session.commit()
        except IntegrityError:
            m_session.rollback()
            raise EntryNameNotUniqueError
        except DataError:
            m_session.rollback()
            raise DatabaseValueError
        except IndexError:
            raise CountryLookUpError
        finally:
            m_session.close()
        return country
