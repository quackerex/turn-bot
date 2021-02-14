class Error(Exception):
    '''Base class for exceptions in this module.'''
    pass

class NoPermissionError(Error):
    '''You have no permission to run this command'''

class EntryNameNotUniqueError(Error):
    '''A country by that name is already in the database.'''

class DatabaseValueError(Error):
    ''''String too long or number too large'''

class DeleteEntryError(Error):
    '''Error in deleting entry'''

class CountryNotFound(Error):
    '''Country not found in database.'''

class CountryInDBError(Error):
    '''Country already registered in database'''

class NotOnServerError(Error):
    '''You need to run this command on 24CC'''

class CountryLookUpError(Error):
    '''Error in finding country in database'''