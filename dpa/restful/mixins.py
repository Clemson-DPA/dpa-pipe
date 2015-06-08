"""A framework for restful APIs."""
# -----------------------------------------------------------------------------
# Module: dpa.restful
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import copy

from dpa.restful.client import RestfulClient, RestfulClientError

# -----------------------------------------------------------------------------
# Public Classes
# -----------------------------------------------------------------------------
class CreateMixin(object):

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, data):

        try:
            data = RestfulClient().execute_request(
                'create', cls.data_type, data=data)
        except RestfulClientError as e:
            raise cls.exception_class(e)

        # XXX 
        # get or create cache based on cls.__name__
        # get object 

        return cls(data)

# -----------------------------------------------------------------------------
class DeleteMixin(object):

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def delete(cls, primary_key):

        # XXX
        # get cache based on cls.__name__
        # remove by primary_key and id

        try:
            return RestfulClient().execute_request('delete', cls.data_type,
                primary_key=primary_key)
        except RestfulClientError as e:
            raise cls.exception_class(e)

# -----------------------------------------------------------------------------
class GetMixin(object):

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, primary_key, **filters):

        # XXX
        # get or create cache based on cls.__name__
        # get object for primary_key
        # if exists, and not expired, return it
        # if doesn't exist, query
        # cache by primary_key and id

        try:
            data = RestfulClient().execute_request('get', cls.data_type, 
                primary_key=primary_key, params=filters)
        except RestfulClientError as e:
            raise cls.exception_class(e)

        return cls(data)

# -----------------------------------------------------------------------------
class ListMixin(object):

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    # XXX cache method based on supplied filters with reasonable expiration
    @classmethod
    def list(cls, **filters):

        try:
            data_list = RestfulClient().execute_request('list', cls.data_type,
                params=filters)
        except RestfulClientError as e:
            raise cls.exception_class(e)

        # XXX
        # get or create cache based on cls.__name__
        # for each piece of data returned:
        #    if object exist in cache for "id", update with new data
        #    otherwise, add new object to cache

        return [cls(data) for data in data_list]

# -----------------------------------------------------------------------------
class UpdateMixin(object):

    # -------------------------------------------------------------------------
    # Public Methods:
    # -------------------------------------------------------------------------
    def update(self, primary_key, data):

        update_data = copy.deepcopy(self._data.data_dict)

        # update the dictionary with the new data
        for key, val in data.items(): 
            if key not in update_data.keys():
                raise cls.exception_class(
                    "Invalid key '{k}' supplied for update.".format(k=key)
                )
            if val is not None:
                update_data[key] = val

        cls = self.__class__

        try:
            db_data = RestfulClient().execute_request('update', cls.data_type,
                primary_key=primary_key, data=update_data)
        except RestfulClientError as e:
            raise cls.exception_class(e)

        # XXX handle cache update

        tmp_obj = cls(db_data)

        self._data = tmp_obj._data

