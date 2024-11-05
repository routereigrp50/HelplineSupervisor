from handlers.logging import Logging as h_log
from shared.tools.decorators import retry
import pymongo
import pymongo.errors
from bson import ObjectId



class Database:
    _client = None
    _uri = None

    @classmethod
    def set_uri(cls, uri: str) -> None:
        cls._uri = uri
        h_log.create_log(5,"handlers.database.set_uri", f"Setting uri to {uri}")

    @classmethod
    def initialize(cls) -> tuple:
        '''Create db client and test connection'''
        try:
            h_log.create_log(5, "handlers.database.initialize", f'Attempting to connect to {cls._uri}')
            cls._client= pymongo.MongoClient(cls._uri)
            cls._client.admin.command("ping")
            h_log.create_log(5, "handlers.database.initialize", f"Successfully connected to {cls._uri}")
            return (True, None)
        except pymongo.errors.ConfigurationError as e:
            h_log.create_log(1,"handlers.database.initialize", f"Database connection failed. Reason: 'Most propably invalid URI or network problem - {cls._uri}'. {str(e)}")
            return (False, f"Database connection failed. Reason: 'Most propably invalid URI or network problem - {cls._uri}'. {str(e)}")
        except pymongo.errors.OperationFailure as e:
            h_log.create_log(1,"handlers.database.initialize", f"Database connection failed. Reason: 'Operation failure, most propably authentication error'. {str(e)}")
            return (False, f"Database connection failed. Reason: 'Operation failure, most propably authentication error'. {str(e)}")
        except pymongo.errors.AutoReconnect as e:
            h_log.create_log(1,"handlers.database.initialize", f"Database connection failed. Reason: 'Connection failure after autoreconnect'. {str(e)}")
            return (False, f"Database connection failed. Reason: 'Connection failure after autoreconnect'. {str(e)}")
        except Exception as e:
            h_log.create_log(1,"handlers.database.initialize", f"Database connection failed. Reason: Unknown - {str(e)}")
            return (False, f"Database connection failed. Reason: Unknown - {str(e)}")
            

    @classmethod 
    @retry(2)   
    def insert_one(cls, collection_name: str, data_to_insert: dict) -> tuple:
        '''Insert one entry into database collection'''
        h_log.create_log(5, "handlers.database.insert_one", f"Attempting to insert data into collection '{collection_name}'")
        try:
            collection = cls._client['HelplineSupervisor'][collection_name]
            result = collection.insert_one(data_to_insert)
            h_log.create_log(5, "handlers.database.insert_one", f"Successfully inserted data into collection '{collection_name}' with ID {str(result.inserted_id)}")
            return (True, {"id":str(result.inserted_id)})
        except Exception as e:
            h_log.create_log(2, "handlers.database.insert_one", f"Failed to insert data into collection '{collection_name}'. Reason: {str(e)}")
            return (False, f"Failed to insert data into collection '{collection_name}'. Reason: {str(e)}")
        
    @classmethod 
    @retry(2)   
    def insert_many(cls, collection_name: str, data_to_insert: list) -> tuple:
        '''Insert many entry into database collection'''
        h_log.create_log(5, "handlers.database.inser_many", f"Attempting to insert data into collection '{collection_name}'")
        try:
            collection = cls._client['HelplineSupervisor'][collection_name]
            result = collection.insert_many(data_to_insert, ordered=False)
            h_log.create_log(5, "handlers.database.inser_many", f"Successfully inserted data into collection '{collection_name}'")
            return (True, None)
        except Exception as e:
            h_log.create_log(2, "handlers.database.inser_many", f"Failed to insert data into collection '{collection_name}'. Reason: {str(e)}")
            return (False, f"Failed to insert data into collection '{collection_name}'. Reason: {str(e)}")
    
    @classmethod 
    @retry(2)   
    def update_one(cls, collection_name: str, data_to_update: dict, upsert: bool = True) -> tuple:
        '''Update one entry in database collection'''
        h_log.create_log(5, "handlers.database.update_one", f"Attempting to update data into collection '{collection_name}'")
        try:
            collection = cls._client['HelplineSupervisor'][collection_name]
            result = collection.update_one(data_to_update, upsert=upsert)
            h_log.create_log(5, "handlers.database.update_one", f"Successfully updated data into collection '{collection_name}' with ID {str(result.inserted_id)}")
            return (True, result)
        except Exception as e:
            h_log.create_log(2, "handlers.database.update_one", f"Failed to update data into collection '{collection_name}'. Reason: {str(e)}")
            return (False, f"Failed to update data into collection '{collection_name}'. Reason: {str(e)}")
    
    @classmethod
    @retry(2)
    def get_collection(cls, collection_name: str, filter: dict = None) -> tuple:
        '''Get whole collection by default. Use filter for more specific search'''
        try:
            collection = cls._client['HelplineSupervisor'][collection_name]
            if filter != None:
                h_log.create_log(5, "handlers.database.get_collection", f"Attempting to get collection '{collection_name}' with filter '{filter}'")
                result = list(collection.find(filter))
            else:
                h_log.create_log(5, "handlers.database.get_collection", f"Attempting to get collection '{collection_name}'")
                result = list(collection.find())

            if len(result) > 0:
                for item in result:
                    item['id'] = str(item["_id"])
                    del item["_id"]
            h_log.create_log(5, "handlers.database.get_collection", f"Successfully received collection '{collection_name}'")
            return (True, result)
        except Exception as e:
            h_log.create_log(2, "handlers.database.get_collection", f"Failed to get collection '{collection_name}'. Reason: Database error - {str(e)}")
            return (False, f"Database error - {str(e)}")
    
    @classmethod 
    @retry(2)   
    def delete_collection(cls, collection_name: str, filter: dict = None) -> tuple:
        '''Delete whole collection by default. Use filter for more specific query'''
        try:
            collection = cls._client['HelplineSupervisor'][collection_name]
            if filter != None:
                h_log.create_log(5, "handlers.database.delete_collection", f"Attempting to delete collection '{collection_name}' with filter '{filter}'")
                result = collection.delete_many(filter)
            else:
                h_log.create_log(5, "handlers.database.delete_collection", f"Attempting to delete collection '{collection_name}'")
                result = collection.delete_many({})
            h_log.create_log(5, "handlers.database.delete_collection", f"Successfully deleted {result.deleted_count} entries from '{collection_name}'")
            return (True, {"deleted_count":result.deleted_count})
        except Exception as e:
            h_log.create_log(5, "handlers.database.delete_collection", f"Failed to delete '{collection_name}'. Reason: {str(e)}")
            return (False, f"Failed to delete '{collection_name}'. Reason: {str(e)}")