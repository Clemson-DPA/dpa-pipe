"""A framework for restful APIs.

Classes
-------
RestfulClient 
    Base class for client-side restful data objects.
 
"""
# -----------------------------------------------------------------------------
# Module: dpa.restful
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
 
from collections import defaultdict

import json
import requests
import yaml

# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

URL_CONFIG_PATH = "config/restful/urls.cfg"

# -----------------------------------------------------------------------------
# Public Classes:
# -----------------------------------------------------------------------------
class RestfulClient(object):

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    # data format expected for restful communication
    data_format = 'json'

    # define how boolean values are represented as strings in request params 
    param_bool_false_str = "False"
    param_bool_true_str = "True"

    # -------------------------------------------------------------------------
    # Private class attributes:
    # -------------------------------------------------------------------------

    _url_cache = {}

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def execute_request(cls, action, data_type, primary_key=None, data=None,
        params=None, headers=None):

        # Never written this type of code before. If you are an experienced
        # web developer, please suggest improvements. Be gentle.

        # get method and url based on the action and data_type
        (http_method, url) = cls._get_url(action, data_type,
            primary_key=primary_key)

        return cls.execute_request_url(http_method, url, data, params, headers)

    @classmethod
    def execute_request_url(cls, http_method, url, data=None, params=None, headers=None):

        data_format = cls.data_format

        if params:
            params = cls._sanitize_params(params)

        if data:
            data = json.dumps(data)

        if data and not headers:
            if data_format == 'json':
                headers = {'content-type': 'application/json'}
            else:
                raise RestfulClientError("Unknown data format: " + data_format)

        # requests method based on the supplied http method name.
        # it *should* be a 1 to 1 lc mapping. (GET==get, PUT==put, etc.)
        requests_method_name = http_method.lower()

        # see if the requests api has a method that matches
        try:
            requests_method = getattr(requests, requests_method_name)
        except AttributeError:
            raise RestfulClientError(
                "Unknown method for requests: " + str(requests_method_name))

        print url
        # execute the request
        response = requests_method(url, params=params, data=data,
            headers=headers)

        # raise a custom exception if 400/500 error
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise RestfulClientError(e.response.text)

        # deserialize the returned data. may want to flesh this out at some
        # point to allow for additional data formats
        if data_format == 'json':
            # json.loads(response.content) results in unicode instead of
            # str. using yaml results in string values. so using that for now.
            return yaml.load(response.content)
        else:
            raise RestfulClientError("Unknown data format: " + data_format)

    # -------------------------------------------------------------------------
    # Private class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def _get_url(cls, action, data_type, primary_key=None):

        data_format = cls.data_format

        # some hacky caching based on data type, method name, and primary key.
        cache_str = data_type + action + str(primary_key)
        if cache_str in cls._url_cache.keys():
            return cls._url_cache[cache_str]

        from dpa.env.vars import DpaVars
        data_server = DpaVars.data_server().get()

        if not data_server:
            raise RestfulClientError(
                "Unable to determine pipeline data server."
            )

        url_config = _get_url_config()
        url_pattern = None
        
        try:
            (http_method, url_pattern) = url_config.get(data_type).get(action)
        except AttributeError:
            try:
                (http_method, url_pattern) = \
                    url_config.get('default').get(action)
            except AttributeError:
                raise RestfulClientError(
                    "Could not find url for '{dt}' {m}".\
                    format(dt=data_type, m=action)
                )

        # replace all of the place holder strings with the actual data
        url = url_pattern.format(
            data_format=data_format,
            data_type=data_type,
            server=data_server,
            primary_key=primary_key,
        )

        cls._url_cache[cache_str] = (http_method, url)

        return (http_method, url)

    # -------------------------------------------------------------------------
    @classmethod
    def _sanitize_params(cls, params=None):
        """Make sure all params are formatted properly."""

        if params is None:
            return {} 

        sanitized = defaultdict(str)

        for key, value in params.items():

            # translate boolean value to proper str
            if isinstance(value, bool):
                sanitized[key] = cls.param_bool_true_str \
                    if value else cls.param_bool_false_str

            # otherwise, make sure the value is a str
            else:
                sanitized[key] = str(value)

        return sanitized

# -----------------------------------------------------------------------------
# Public exception classes:
# -----------------------------------------------------------------------------
class RestfulClientError(Exception):
    pass

# -----------------------------------------------------------------------------
# Private Functions:
# -----------------------------------------------------------------------------
def _get_url_config():
    from dpa.ptask.area import PTaskArea
    return PTaskArea.current().config(
        URL_CONFIG_PATH,
        composite_ancestors=True,
    )

