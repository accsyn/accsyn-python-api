# :coding: utf-8
# :copyright: Copyright (c) 2016-2022 accsyn / HDR AB

import sys
import os
import logging
import traceback
import time
import datetime
import subprocess
import socket
import json
import uuid
import hashlib
import copy

import urllib
import base64
import io
import gzip

import re
import requests


from ._version import __version__

if sys.version_info.major >= 3:
    import io

else:
    # Python 2 backward compability
    import binascii

try:
    requests.packages.urllib3.disable_warnings()
except BaseException:
    sys.stderr.write(traceback.format_exc())

logging.basicConfig(
    format="(%(thread)d@%(asctime)-15s) %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

ACCSYN_BACKEND_DOMAIN = "accsyn.com"
ACCSYN_BACKEND_MASTER_HOSTNAME = "master.{}".format(ACCSYN_BACKEND_DOMAIN)
ACCSYN_PORT = 443
DEFAULT_EVENT_PAYLOAD_COMPRESS_SIZE_TRESHOLD = 100 * 1024  # Compress event data payloads above 100k

CLEARANCE_SUPPORT = "support"
CLEARANCE_ADMIN = "admin"
CLEARANCE_EMPLOYEE = "employee"
CLEARANCE_STANDARD = "standard"
CLEARANCE_CLIENT = CLEARANCE_STANDARD # BWCOMP
CLEARANCE_NONE = "none"


class JSONEncoder(json.JSONEncoder):
    """JSON serialiser."""

    def default(self, obj):
        if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        return super(JSONEncoder, self).default(obj)


class JSONDecoder(json.JSONDecoder):
    """JSON deserialize."""

    def decode(self, json_string):
        json_data = json.loads(json_string)

        def recursive_decode(d):
            if isinstance(d, dict):
                for key in d.keys():
                    if isinstance(d[key], dict):
                        d[key] = recursive_decode(d[key])
                    elif isinstance(d[key], list):
                        newlist = []
                        for i in d[key]:
                            newlist.append(recursive_decode(i))
                        d[key] = newlist
                    elif Session._is_str(d[key]):
                        if re.match(
                            "^[0-9]{2,4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:" "[0-9]{2}$",
                            str(Session._safely_printable(d[key])),
                        ):
                            if len(d[key].split("-")[0]) == 4:
                                d[key] = datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%S")
                            else:
                                d[key] = datetime.datetime.strptime(d[key], "%y-%m-%dT%H:%M:%S")
                        # With millis
                        elif re.match(
                            "^[0-9]{2,4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:" "[0-9]{2}:[0-9]{2}.[0-9]{3}$",
                            str(Session._safely_printable(d[key])),
                        ):
                            if len(d[key].split("-")[0]) == 4:
                                d[key] = datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%S.%f")
                            else:
                                d[key] = datetime.datetime.strptime(d[key], "%y-%m-%dT%H:%M:%S.%f")
                        # DEPRECATED
                        elif str(Session._safely_printable(d[key])).find("{USD::date}") > -1:
                            s = d[key][d[key].find("}") + 1 :]
                            d[key] = datetime.datetime.strptime(
                                s,
                                "%Y%m%d %H:%M:%S" if s.find("+") == -1 else "%Y%m%d+%H:%M:%S",
                            )
            return d

        return recursive_decode(json_data)


class Session(object):
    """accsyn API session object."""

    DEFAULT_CONNECT_TIMEOUT = 10  # Wait 10 seconds for connection
    DEFAULT_TIMEOUT = 2 * 60  # Wait 2 minutes for response

    _p_logfile = None

    @property
    def username(self):
        return self._username

    @property
    def timeout(self):
        return self._timeout

    @property
    def connect_timeout(self):
        return self._connect_timeout

    def __init__(
        self,
        domain=None,
        username=None,
        api_key=None,
        hostname=None,
        port=None,
        proxy=None,
        verbose=False,
        pretty_json=False,
        dev=False,
        path_logfile=None,
        timeout=None,
        connect_timeout=None,
    ):
        """
        Initiate a new API session object. Throws exception upon authentication failure.

        :param domain: The accsyn domain (or read from ACCSYN_DOMAIN environment variable)
        :param username: The accsyn username (or read from ACCSYN_API_USER environment variable)
        :param api_key: The secret API key for authentication (or read from ACCSYN_API_KEY environment variable)
        :param hostname: Override hostname/IP to connect to.
        :param port: Override default port 443.
        :param proxy: The proxy settings (or read from ACCSYN_PROXY environment variable).
        :param verbose: Create a verbose session, printing debug output to stdout.
        :param pretty_json: (verbose) Print pretty formatted JSON.
        :param dev: Dev mode.
        :param path_logfile: Output all log messages to this logfile instead of stdout.
        :param timeout: Timeout in seconds for API calls - waiting for response.
        :param connect_timeout: Timeout in seconds for API calls - waiting for connection.
        """
        # Generate a session ID
        self.__version__ = __version__
        self._session_id = str(uuid.uuid4())
        self._uid = None
        self._api_key = None
        self._be_verbose = verbose
        self._pretty_json = pretty_json
        self._proxy = proxy
        self._dev = dev is True or os.environ.get('ACCSYN_DEV', 'false') in ['true', '1']
        Session._p_logfile = path_logfile
        self._role = CLEARANCE_NONE
        self._verbose("Creating accsyn Python API session (v{})".format(__version__))
        for key in os.environ:
            if key.startswith("FILMHUB_"):
                Session._warning('Found old FilmHUB product environment variable "{}", ' "please migrate!".format(key))
        if not domain:
            domain = (
                os.environ["ACCSYN_DOMAIN"]
                if "ACCSYN_DOMAIN" in os.environ
                else os.environ.get(
                    "ACCSYN_ORG",
                )
            )
        if not domain:
            raise AccsynException(
                "Please supply your accsyn domain/organization or set " "ACCSYN_DOMAIN environment!"
            )
        if not username:
            username = os.environ.get("ACCSYN_API_USER")
        if not username:
            if not ("ACCSYN_API_USER" in os.environ):
                raise AccsynException(
                    "Please supply your accsyn user name (E-mail) or set ACCSYN_API_USER environment!"
                )
        if not api_key:
            api_key = os.environ.get("ACCSYN_API_KEY")
        if not api_key:
            raise AccsynException("Please supply your accsyn API KEY or set ACCSYN_API_KEY environment!")
        self._hostname = hostname
        self._port = port
        self._timeout = timeout or Session.DEFAULT_TIMEOUT
        self._connect_timeout = connect_timeout or Session.DEFAULT_CONNECT_TIMEOUT
        if self._hostname is None:
            if self._dev:
                self._hostname = "127.0.0.1"
            else:
                # Get domain
                response = self._rest(
                    "GET",
                    ACCSYN_BACKEND_MASTER_HOSTNAME,
                    "J3PKTtDvolDMBtTy6AFGA",
                    {"ident": domain},
                )
                # Store hostname
                if "message" in response:
                    raise AccsynException(response["message"])
                result = response.get('result', {})
                assert "hostname" in result, "No API endpoint hostname were provided for us!"
                self._hostname = result["hostname"]
                if self._port is None:
                    self._port = result["port"]
        if self._port is None:
            self._port = ACCSYN_PORT if not self._dev else 8181
        self._domain = domain
        self._username = username
        self._api_key = api_key
        self._last_message = None
        self.login()

    @staticmethod
    def get_hostname():
        """
        :return: The hostname of this computer.
        """
        return socket.gethostname()

    @staticmethod
    def _info(s, standout=False):
        """
        Utility; Print informational message to logfile or stdout.

        :param s: The message to print.
        :param standout: If True, statement will be made more visible.
         :return: The message.
        """
        if Session._p_logfile:
            with open(Session._p_logfile, "a") as f:
                try:
                    if standout:
                        f.write("-" * 80 + "\n")
                    f.write(s + "\n")
                    if standout:
                        f.write("-" * 80 + "\n")
                finally:
                    f.flush()
        else:
            if standout:
                logging.info("-" * 80)
            logging.info(s)
            if standout:
                logging.info("-" * 80)
        return s

    @staticmethod
    def str(d, indent=4):
        """Return a string representation of a dict"""
        return json.dumps(d, default=Session._json_serial, indent=indent) if d is not None else ""

    def get_last_message(self):
        """Retreive error message from last API call."""
        return self._last_message

    def login(self):
        """Attempt to login to accsyn and get a session."""
        # TODO: Load session key from safe disk storage/key chain?
        assert self._uid is None, "Already logged in!"
        payload = dict(
            session_id=self._session_id,
        )
        headers = {
            "Authorization": "basic {}:{}".format(
                Session._base64_encode(self._username),
                Session._base64_encode(self._api_key),
            ),
            "X-Accsyn-Workspace": self._domain,
        }
        response = self._rest(
            "PUT",
            self._hostname,
            "/api/login",
            payload,
            headers=headers,
            port=self._port,
        )
        # Store session key
        assert "result" in response, "No result were provided!"
        result = response["result"]
        self._role = result["role"]
        self._uid = result["id"]
        return True

    # Create

    def create(self, entitytype, data, entitytype_id=None, allow_duplicates=True):
        """
        Create a new accsyn entity.

        :param entitytype: The type of entity to create (job, share, acl)
        :param data: The entity data as a dictionary.
        :param entitytype_id: For creating sub entities (tasks), this is the parent (job) id.
        :param allow_duplicates: (jobs and tasks) Allow duplicates to be created.
        :return: The created entity data, as dictionary.
        """
        assert 0 < len((entitytype or "").strip()), "You must provide the entity type!"
        entitytype = entitytype.lower().strip()
        if Session._is_str(data):
            assert 0 < len((data or "").strip()), "You must provide the data to create!"
            # Is it JSON as a string or JSON in a file pointed to?
            try:
                data = json.loads(data)
            except BaseException:
                # Not JSON string, maybe a path?
                if os.path.exists(data):
                    data = json.load(open(data, "r"))
                else:
                    raise AccsynException(
                        "Cannot build JSON payload data, not a valid JSON " "string or path to a JSON file!"
                    )
        else:
            if isinstance(data, list):
                data = {"tasks": data}
            assert data is not None and 0 < len(data), "Empty create data submitted!"
        if entitytype == "queue":
            data["type"] = 2
        elif entitytype == "task" and "tasks" not in data:
            data = {"tasks": data}
        if entitytype in ["job", "task"]:
            data["allow_duplicates"] = allow_duplicates
        d = self._event(
            "POST",
            "%s/create" % Session._get_base_uri(entitytype),
            data,
            query=entitytype_id,
        )
        if d:
            if "result" in d:
                if len(d["result"]) == 1:
                    return d["result"][0]
                else:
                    return d["result"]
            else:
                return d

    # Query

    def find(
        self,
        query,
        attributes=None,
        finished=None,
        offline=None,
        archived=None,
        limit=None,
        skip=None,
        create=False,
        update=False,
    ):
        """
        Return (GET) a list of entities/entitytypes/attributes based on *query*.

        :param query: The query, a string on accsyn query format.
        :param attributes: The attributes to return, default is to return all attributes with access.
        :param finished: (job) Search among inactive jobs.
        :param offline: (user,share) Search among offline entities.
        :param archived: Search among archived (deleted/purged) entities.
        :param limit: The maximum amount of entities to return.
        :param skip: The amount of entities to skip.
        :param create: (attributes) Return create (POST) attributes.
        :param update: (attributes) Return update (PUT) attributes.
        :return: List of dictionaries.
        """
        assert 0 < len(query or "") and Session._is_str(query), "Invalid query type supplied, must be of string type!"

        retval = None
        d = self.decode_query(query)
        data = {}
        if d["entitytype"] == "entitytypes":
            # Ask cloud server, the Python API is rarely updated and should not
            # need to know
            d = self._event("GET", "entitytypes", {})
            if d:
                retval = d["result"]
        elif d["entitytype"] == "attributes":
            assert d.get("expression"), (
                "Please query which entity to obtain attributes for (i.e. " '"attributes WHERE entitytype=job")'
            )
            # Look at expression
            parts = d["expression"].split("=")
            assert len(parts) == 2 and parts[0].strip() == "entitytype", (
                "Please query attributes by expressions on the form " '"attributes WHERE entitytype=job"'
            )
            entitytype = parts[1].strip().replace("'", "").replace('"', "")
            d = self._event(
                "GET",
                "attributes",
                {"entitytype": entitytype, "create": create, "update": update},
            )
            if d:
                retval = d["result"]
        else:
            # Send query to server, first determine uri
            uri_base = Session._get_base_uri(d["entitytype"])
            if d["entitytype"] == "queue":
                data = {"type": 2}
            elif d["entitytype"] == "job":
                data = {"type": 1}
            if finished is not None:
                data["finished"] = finished
            if offline is not None:
                data["offline"] = offline
            if archived is not None:
                data["archived"] = archived
            if limit:
                data["limit"] = limit
            if skip:
                data["skip"] = skip
            if attributes:
                data["attributes"] = attributes
            d = self._event("GET", "%s/find" % uri_base, data, query=d.get("expression"))
            if d:
                retval = d["result"]
        return retval

    def find_one(
        self,
        query,
        attributes=None,
        finished=None,
        offline=None,
        archived=None,
    ):
        """
        Return a single entity.

        :param query: The query, a string on accsyn query format.
        :param attributes: The attributes to return, default is to return all attributes with access.
        :param finished: (job) Search among inactive jobs.
        :param offline: (user,share) Search among offline entities.
        :param archived: Search among archived (purged/deleted) entities.
        :return: If found, a single dictionary. None otherwise.
        """
        assert 0 < len(query or "") and (
            Session._is_str(query)
        ), "Invalid query type supplied, must be of string type!"
        #
        result = self.find(
            query,
            attributes=attributes,
            finished=finished,
            offline=offline,
            archived=archived,
        )
        if result and 0 < len(result):
            retval = result[0]
            return retval
        return None

    def report(self, query):
        """
        (Support) Return an internal backend report of an entity.

        :param query: The query, a string on accsyn query format.
        :return: A text string containing the human readable report.
        """
        d = self.decode_query(query)
        # Send query to server, first determine uri
        uri_base = Session._get_base_uri(d["entitytype"])
        data = {}
        d = self._event("GET", "%s/report" % uri_base, data, query=d.get("expression"))
        return d["report"]

    def metrics(self, query, attributes=["speed"], time=None):
        """
        Return metrics for an entity (job)

        .. versionadded:: 2.0

        :param query:
        :param attributes:
        :param time:
        :return:
        """
        d = self.decode_query(query)
        # Send query to server, first determine uri
        uri_base = Session._get_base_uri(d["entitytype"])
        data = {
            "attributes": attributes,
        }
        if not time is None:
            data["time"] = time
        d = self._event("GET", "%s/metrics" % uri_base, data, query=d.get("expression"))
        return d["result"]

    # Update an entity

    def update(self, entitytype, entityid, data):
        """
        Update/modify an entity.

        :param entitytype: The type of entity to update (job, share, acl, ..)
        :param entityid: The id of the entity.
        :param data: The dictionary containing attributes to update.
        :return: The updated entity data, as dictionary.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityid or "") and Session._is_str(
            entityid
        ), "Invalid entity ID supplied, must be of string type!"
        assert 0 < len(data or {}) and isinstance(data, dict), "Invalid data supplied, must be dict and have content!"
        response = self._event(
            "PUT",
            "%s/edit" % Session._get_base_uri(entitytype),
            data,
            entityid=entityid,
        )
        if response:
            return response["result"][0]

    def update_one(self, entitytype, entityid, data):
        '''
        Update/modify an entity.

        :param entitytype: The type of entity to update (job, share, acl, ..)
        :param entityid: The id of the entity.
        :param data: The dictionary containing attributes to update.
        :return: The updated entity data, as dictionary

        .. deprecated:: 2.0.2
            Since Python 2.0.2 you should use the :func:`update` function instead

        '''
        return self.update(entitytype, entityid, data)

    def update_many(self, entitytype, data, entityid):
        """
        Update/modify multiple entities - tasks beneath a job.

        :param entitytype: The type of parent entity to update (job)
        :param data: The list dictionaries containing sub entity (task) id and attributes to update.
        :param entityid: The id of the parent entity to update (job)
        :return: The updated sub entities (tasks), as dictionaries.

        .. deprecated:: 2.0.2
            Since Python 2.0.2 you should use the :func:`update` function instead
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert entitytype == "task", 'Only multiple "task" entities can be updated!'
        if entitytype.lower() == "task":
            assert 0 < len(entityid or "") and (
                Session._is_str(entityid)
            ), "Invalid entity ID supplied, must be of string type!"
        assert 0 < len(data or []) and isinstance(data, list), "Invalid data supplied, must be a list!"
        response = self._event(
            "PUT",
            "%s/edit" % Session._get_base_uri(entitytype),
            data,
            entityid=entityid,
        )
        if response:
            return response["result"]

    # Entity assignment / connections

    def assign(self, entitytype_parent, entitytype_child, data):
        """
        Assign one entity to another.

        .. versionadded:: 2.0

        :param entitytype_parent: The parent entity type to assign child entity to.
        :param entitytype_child: The child entity type to assign to parent entity.
        :param data: Assignment data, should contain parent and child entity ids.
        :return: True if assignment was a success, exception otherwise.
        """
        assert 0 < len(entitytype_parent or "") and Session._is_str(
            entitytype_parent
        ), "Invalid parent entity type supplied, must be of string type!"
        assert 0 < len(entitytype_child or "") and Session._is_str(
            entitytype_child
        ), "Invalid child entity type supplied, must be of string type!"
        entitytype_parent = entitytype_parent.lower().strip()
        entitytype_child = entitytype_child.lower().strip()
        assert (
            not data is None and isinstance(data, dict) and (0 < len(data or {}))
        ), "Invalid assignment data supplied, must be a dict with values!"
        response = None
        if entitytype_parent == "share" and entitytype_child == "server":
            # Assign a server to a share, expect share and client supplied
            share_id = data.get("share")
            assert re.match("^[a-z0-9]{24}$", (share_id or "")), "Please supply share ID with assignment data!"
            client_id = data.get("client")
            assert re.match("^[a-z0-9]{24}$", (client_id or "")), "Please supply client ID with assignment data!"
            what = None
            if data.get("main") is True:
                what = "server"
            elif data.get("site") is True:
                what = "siteserver"
            else:
                raise Exception("Please supply type of server assignment (main " "or site) in assignment data!")
            response = self._event(
                "PUT",
                "%s/edit" % Session._get_base_uri(entitytype_parent),
                {what: client_id},
                entityid=share_id,
            )
        if response:
            return True
        else:
            raise Exception("Unsupported assignment operation!")

    def assignments(self, entitytype, entityid):
        """
        Return list of assigned child entities.

        .. versionadded:: 2.0

        :param query:
        :return: List of dictionaries.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid parent entity type supplied, must be of string type!"
        if entitytype.lower() == "share":
            response = self._event(
                "GET",
                "%s/servers" % Session._get_base_uri(entitytype),
                {},
                entityid=entityid,
            )
            return response["result"]
        else:
            raise Exception("Unsupported assignment operation!")

    def deassign(self, entitytype_parent, entitytype_child, data):
        """
        De-assign one entity from another.

        .. versionadded:: 2.0

        :param entitytype_parent: The parent entity type to deassign child entity from
        :param entitytype_child: The child entity type to deassign from parent entity
        :param data: De-assignment data, should contain parent and child entity ids + additional information as required
        :return: True if deassignment was a success, exception otherwise.
        """
        assert 0 < len(entitytype_parent or "") and Session._is_str(
            entitytype_parent
        ), "Invalid parent entity type supplied, must be of string type!"
        assert 0 < len(entitytype_child or "") and Session._is_str(
            entitytype_child
        ), "Invalid child entity type supplied, must be of string type!"
        entitytype_parent = entitytype_parent.lower().strip()
        entitytype_child = entitytype_child.lower().strip()
        assert (
            not data is None and isinstance(data, dict) and (0 < len(data or {}))
        ), "Invalid de-assignment data supplied, must be a dict with values!"
        response = None
        if entitytype_parent == "share" and entitytype_child == "server":
            # Assign a server to a share, expect share and client supplied
            share_id = data.get("share")
            assert re.match("^[a-z0-9]{24}$", (share_id or "")), "Please supply share ID with de-assignment data!"
            client_id = data.get("client")
            assert re.match("^[a-z0-9]{24}$", (client_id or "")), "Please supply client ID with de-assignment data!"
            what = None
            if data.get("main") is True:
                what = "server"
            elif data.get("site") is True:
                what = "siteserver"
            else:
                raise Exception("Please supply type of server assignment (main " "or site) in assignment data!")
            response = self._event(
                "PUT",
                "%s/edit" % Session._get_base_uri(entitytype_parent),
                {"{}_clear".format(what): client_id},
                entityid=share_id,
            )
        if response:
            return True
        else:
            raise Exception("Unsupported assignment operation!")

    # Offline/Delete an entity

    def offline_one(self, entitytype, entityid):
        """
        Offline an entity.

        .. versionadded:: 2.0

        :param entitytype: The type of entity to delete (job, share, acl, ..)
        :param entityid: The id of the entity.
        :return: True if offline, an exception is thrown otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityid or "") and (
            Session._is_str(entityid)
        ), "Invalid entity ID supplied, must be of string type!"
        response = self._event(
            "DELETE",
            "%s/offline" % Session._get_base_uri(entitytype),
            {},
            entityid=entityid,
        )
        if response:
            return response["result"]

    def delete_one(self, entitytype, entityid):
        """
        Delete(archive) an entity.

        :param entitytype: The type of entity to delete (job, share, acl, ..)
        :param entityid: The id of the entity.
        :return: True if deleted, an exception is thrown otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityid or "") and (
            Session._is_str(entityid)
        ), "Invalid entity ID supplied, must be of string type!"
        response = self._event(
            "DELETE",
            "%s/delete" % Session._get_base_uri(entitytype),
            {},
            entityid=entityid,
        )
        if response:
            return response["result"]

    # File operations

    def ls(
        self,
        path,
        recursive=False,
        maxdepth=None,
        getsize=False,
        files_only=False,
        directories_only=False,
        include=None,
        exclude=None,
    ):
        """
        List files on a share.

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'
        :param recursive: If True - a recursive listing will be performed.
        :param maxdepth: (Recursive) The maximum depth to descend.
        :param getsize: If True - file sizes will be returned.
        :param files_only: If True - only return files, no directories.
        :param directories_only: If True - only return directories, no files.
        :param include: Filter expression (string or list) dictating what to include in result: "word" - exact match, "*word" - ends with word, "word*" - starts with word, "*word*" - contains word, "start*end" - starts & ends with word and "re('...')" - regular expression. Has precedence over *exclude*.
        :param exclude: Filter expression (string or list) dictating what to exclude from result: "word" - exact match, "*word" - ends with word, "word*" - starts with word, "*word*" - contains word, "start*end" - starts & ends with word and "re('...')" - regular expression.
        :return: A dictionary containing result of file listing.

        Include and exclude filters are case-insensitive, to make regular expression case-sensitive, use the following
        syntax: "re('...', 'I')".

        .. versionadded:: 2.2.0 (app/daemon: 2.6-20)

        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = {
            "op": "ls",
            "path": path,
            "download": True,
            "recursive": recursive,
            "getsize": getsize,
        }
        if maxdepth:
            data["maxdepth"] = maxdepth
        if directories_only:
            data["directories_only"] = directories_only
        if files_only:
            data["files_only"] = files_only
        if include:
            data["include"] = include
        if exclude:
            data["exclude"] = exclude
        response = self._event("GET", "organization/file", data)
        if response:
            return response["result"]

    def getsize(self, path, include=None, exclude=None):
        """
        Get size of a file or directory.

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :param include: Filter expression (string or list) dictating what to include in result: "word" - exact match, "*word" - ends with word, "word*" - starts with word, "*word*" - contains word, "start*end" - starts & ends with word and "re('...')" - regular expression. Has precedence over *exclude*.
        :param exclude: Filter expression (string or list) dictating what to exclude from result: "word" - exact match, "*word" - ends with word, "word*" - starts with word, "*word*" - contains word, "start*end" - starts & ends with word and "re('...')" - regular expression.
        :return: A dictionary containing result of file listing.

        Include and exclude filters are case-insensitive, to make regular expression case-sensitive, use the following
        syntax: "re('...', 'I')".

        .. versionadded:: 2.2.0 (app/daemon: 2.6-20)
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = {
            "op": "getsize",
            "path": path,
        }
        if include:
            data["include"] = include
        if exclude:
            data["exclude"] = exclude
        response = self._event("GET", "organization/file", data)
        if response:
            return response["result"]

    def exists(self, path):
        """
        Check if a file or directory exists.

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = {
            "op": "exists",
            "path": path,
        }
        response = self._event("GET", "organization/file", data)
        if response:
            return response["result"]

    def mkdir(self, path):
        """
        Create a directory on a share.

        .. versionadded:: 2.0

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = {
            "op": "mkdir",
            "path": path,
        }
        response = self._event("POST", "organization/file", data)
        if response:
            return response["result"]

    def rename(self, path, path_to):
        """
        Rename a file/directory on a share.

        .. versionadded:: 2.0

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :param path_to: The new accsyn path, has to be within the same directory as source *path*, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        assert 0 < len(path_to or "") and (
            Session._is_str(path_to) or isinstance(path_to, dict) or isinstance(path_to, list)
        ), "No destination path supplied, or not a string/list/dict!"
        data = {
            "op": "rename",
            "path": path,
            "path_to": path_to,
        }
        response = self._event("PUT", "organization/file", data)
        if response:
            return response["result"]

    def mv(self, path_src, path_dst):
        """
        Move a file/directory on a share.

        .. versionadded:: 2.0

        :param path_src: The accsyn source path, on the form 'share=<the share>/<path>/<somewhere>'.
        :param path_dst: The accsyn destination path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path_src or "") and (
            Session._is_str(path_src) or isinstance(path_src, dict) or isinstance(path_src, list)
        ), "No source path supplied, or not a string/list/dict!"
        assert 0 < len(path_dst or "") and (
            Session._is_str(path_dst) or isinstance(path_dst, dict) or isinstance(path_dst, list)
        ), "No destination path supplied, or not a string/list/dict!"
        data = {
            "op": "move",
            "path": path_src,
            "path_to": path_dst,
        }
        response = self._event("PUT", "organization/file", data)
        if response:
            return response["result"]

    def rm(self, path):
        """
        Remove a file/directory on a share.

        .. versionadded:: 2.0

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = {
            "op": "mkdir",
            "path": path,
        }
        response = self._event("POST", "organization/file", data)
        if response:
            return response["result"]

    # Pre publish
    def prepublish(self, data):
        """
        Pre-process a publish.

        :param data: The pre publish data, see documentation.
        :return: Processed publish data, see documentation.
        """
        if data is None or not isinstance(data, list):
            raise AccsynException("None or empty data supplied!")

        # Check entries, calculate size
        def recursive_get_size(files):
            result = 0
            for d in files:
                if "size" not in d:
                    d["size"] = (
                        0 if not d.get("is_dir") is True or d.get("files") is None else recursive_get_size(d["files"])
                    )
                result += d["size"]
            return result

        event_data = {"files": data, "size": recursive_get_size(data)}
        response = self._event("PUT", "organization/publish/preprocess", event_data)
        return response["result"]

    # Settings

    def get_setting(self, name=None, scope='workspace', entity_id=None, integration=None, data=None):
        '''Retrive *name* setting for the given *scope* (workspace, job, share..), for optional *entity_id* or *integration* (ftrack,..)'''
        evt_data = {'scope': scope, 'name': name}
        if entity_id:
            evt_data['ident'] = entity_id
        if integration:
            evt_data['integration'] = integration
        if evt_data:
            evt_data['data'] = data
        response = self._event("GET", "setting", evt_data)
        return response.get("result")

    def set_setting(self, name, value, scope='workspace', entity_id=None, integration=None, data=None):
        '''Set the setting identified by *name* to *value* for *entity_id* within *scope*.'''
        evt_data = {'scope': scope, 'name': name, 'value': value}
        if entity_id:
            evt_data['ident'] = entity_id
        if integration:
            evt_data['integration'] = integration
        if evt_data:
            evt_data['data'] = data
        response = self._event("PUT", "setting", evt_data)
        return response.get("result")

    # Misc
    def get_api_key(self):
        """Fetch API key, by default disabled in backend."""
        return self._event("GET", "user/api_key", {})["api_key"]

    def gui_is_running(self):
        """
        Check if a GUI is running on the same machine (hostname match) and with same username.

        :return: True if found, False otherwise.
        """
        result = self._event(
            "GET",
            "client/find",
            {},
            query="user={0} AND code={1} AND type={2}".format(self._uid, Session.get_hostname(), 0),
        )["result"]
        retval = None
        if 0 < len(result):
            for c in result:
                retval = c["status"] in ["online", "disabled"]
                if retval is True:
                    break
        return retval

    def server_is_running(self):
        """
        Check if a server is running on the same machine with same username.

        :return: True if found, False otherwise.
        """
        result = self._event(
            "GET",
            "client/find",
            {},
            query="user={0} AND code={1} AND type!={2}".format(self._uid, Session.get_hostname(), 0),
        )["result"]
        retval = None
        if 0 < len(result):
            for c in result:
                retval = c["status"] in ["online", "disabled"]
                if retval is True:
                    break
        return retval

    def integration(self, name, operation, data):
        '''Make an integration utility call for integration pointed out by *name* and providing the *operation* as string and *data* as a dictionary'''
        assert len(name) > 0, 'No name provided'
        assert len(operation) > 0, 'No operation provided'
        return self._event(
            "PUT",
            "organization/integration/{}/utility".format(name),
            {
                'operation': operation,
                'data': data,
            },
        )["result"]

    # Help
    def help(self):
        print("Please have a look at the Python API reference: " "https://accsyn-python-api.readthedocs.io/en/latest/")

    # Internal utility functions

    @staticmethod
    def _obscure_dict_string(s):
        """Hide sensitive information within a string originating from a dict."""
        if s is None:
            return s
        for key in ["pwd", "_key", "token"]:
            last_pos = 0
            while True:
                new_pos = s.find(key, last_pos)
                if new_pos == -1:
                    break
                else:
                    idx_start = s.find('"', new_pos + len(key) + 1)
                    idx_end = s.find('"', idx_start + 1)
                    s = s[: idx_start + 1] + "*" + s[idx_end:]
                    last_pos = idx_start
        return s

    # Network

    def _rest(
        self,
        method,
        hostname,
        uri,
        data,
        timeout=None,
        ssl=True,
        port=None,
        quiet=False,
        headers=None,
    ):
        """
        (Utility) Make a REST call to accsyn backend.

        :param method: The REST method to use: GET,POST,PUT or DELETE
        :param hostname: The name of remote endpoint to call.
        :param uri: The remote endpoint URI to call.
        :param data: Payload data.
        :param timeout: Timeout for request, in seconds.
        :param ssl: If True (default), attempt to communicate using SSL.
        :param port: The remote port to connect to.
        :param quiet: If True, do not print any log messages.
        :param headers: The headers to supply, by default the session will be supplied.

        :return: The result of request, as a JSON dict.
        """
        if port is None:
            port = self._port or ACCSYN_PORT
        if hostname is None:
            hostname = "{}.{}".format(self._domain, ACCSYN_BACKEND_DOMAIN)
        # Proxy set?
        proxy_type = None
        proxy_hostname = None
        proxy_port = -1
        proxy_setting = self._proxy or os.environ.get("ACCSYN_PROXY")
        if 0 < len(proxy_setting or ""):
            if 0 < proxy_setting.find(":"):
                parts = proxy_setting.split(":")
                if len(parts) == 3:
                    proxy_type = parts[0]
                    proxy_hostname = parts[1]
                    proxy_port = int(parts[2])
                elif len(parts) == 2:
                    proxy_type = "accsyn"
                    proxy_hostname = parts[0]
                    proxy_port = int(parts[1])
            else:
                proxy_type = "accsyn"
                proxy_hostname = proxy_setting
                proxy_port = 80
            ssl = False
        if self._dev and (uri or "").find("registry") != 0:
            ssl = False
            port = 8181
        if proxy_type == "accsyn":
            if proxy_port == -1:
                proxy_port = 80
            self._verbose("Using accsyn proxy @ {}:{}".format(proxy_hostname, proxy_port))
            hostname = proxy_hostname
            port = proxy_port
        elif proxy_type in ["socks", "socks5"]:
            try:
                self._verbose("Using SOCKS5 proxy @ {}:{}".format(proxy_hostname, proxy_port))
                import socks

                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_hostname, proxy_port)
                socket.socket = socks.socksocket
            except ImportError as ie:
                Session._warning('Python lacks SOCKS support, please install "pysocks" and' " try again...")
                raise ie
        elif proxy_type is not None:
            raise AccsynException('Unknown proxy type "{}"!'.format(proxy_type))
        url = "http{}://{}:{}/api/v3{}".format(
            "s" if ssl else "",
            hostname,
            port,
            ("/" if not uri.startswith("/") else "") + uri,
        )
        if timeout is None:
            timeout = self.timeout
        if data is None:
            data = {}
        # Wait 10s to reach machine, 2min for it to send back data
        CONNECT_TO, READ_TO = (self.connect_timeout, timeout)
        r = None
        retval = None

        headers_effective = dict()
        if headers:
            headers_effective = copy.deepcopy(headers)
        elif self._api_key:
            headers_effective = {
                "Authorization": "basic {}:{}".format(
                Session._base64_encode(self._username),
                    Session._base64_encode(self._api_key)
                ),
                "X-Accsyn-Workspace": self._domain,
            }
        headers_effective["X-Accsyn-Device"] = "PythonAPI v%s @ %s %s(%s)" % (
            __version__,
            sys.platform,
            Session.get_hostname(),
            os.name,
        )
        if 3 <= sys.version_info.major:
            t_start = int(round(time.time() * 1000))
        else:
            t_start = long(round(time.time() * 1000))
        try:
            self._verbose(
                "REST %s %s, data: %s"
                % (
                    method,
                    url,
                    data if not self._pretty_json else Session.str(data),
                )
            )
            if method.lower() == "get":
                r = requests.get(
                    url,
                    params=Session._url_quote(data),
                    timeout=(CONNECT_TO, READ_TO),
                    verify=False,
                    headers=headers_effective,
                )
            elif method.lower() == "put":
                r = requests.put(
                    url,
                    Session._safe_dumps(data),
                    timeout=(CONNECT_TO, READ_TO),
                    verify=False,
                    headers=headers_effective,
                )
            elif method.lower() == "post":
                r = requests.post(
                    url,
                    Session._safe_dumps(data),
                    timeout=(CONNECT_TO, READ_TO),
                    verify=False,
                    headers=headers_effective,
                )
            elif method.lower() == "delete":
                r = requests.delete(
                    url,
                    params=Session._url_quote(data),
                    timeout=(CONNECT_TO, READ_TO),
                    verify=False,
                    headers=headers_effective,
                )
            t_end = int(round(time.time() * 1000))
            # break
        except BaseException:
            # if timeout <= 0:
            raise AccsynException(
                "Could not reach {}:{}! Make sure backend({}) can"
                " be reached from you location and no firewall is "
                "blocking outgoing TCP traffic at port {}. "
                "Details: {}".format(
                    hostname,
                    port,
                    hostname,
                    port,
                    traceback.format_exc() if not quiet else "(quiet)",
                )
            )
        try:
            retval = json.loads(r.text, cls=JSONDecoder)
            if not quiet:
                self._verbose(
                    "{}/{} REST {} result: {} (~{}ms)".format(
                        hostname,
                        uri,
                        method,
                        Session._obscure_dict_string(
                            Session._safely_printable(
                                str(retval) if not self._pretty_json else Session.str(retval)
                            ).replace("'", '"')
                        ),
                        t_start - t_end + 1,
                    )
                )
        except BaseException:
            sys.stderr.write(traceback.format_exc())
            message = 'The {} REST {} {} operation failed! Details: {} {}'.format(
                url,
                method,
                Session._obscure_dict_string(Session._safely_printable(str(data)).replace("'", '"')),
                r.text,
                traceback.format_exc(),
            )
            Session._warning(message)
            raise AccsynException(message)

        if "exception" in retval:
            message = "{} caused an exception! Please contact {} admin for more"
            " further support.".format(uri, self._domain)
            Session._warning(message)
            if self._role in [CLEARANCE_ADMIN, CLEARANCE_SUPPORT]:
                Session._warning(retval["exception"])
            raise AccsynException(message)
        elif "message" in retval:
            message_effective = retval.get("message_hr") or retval["message"]
            Session._warning(message_effective)
            raise AccsynException(message_effective)
        return retval

    # REST get

    def _event(
        self,
        method,
        uri,
        data,
        query=None,
        entityid=None,
        timeout=None,
        ssl=True,
        quiet=False,
    ):
        """Utility; Construct an event and send using REST to accsyn backend."""
        assert self._uid, "Login before posting event!"
        event = {
            "audience": "api",
            "domain": self._domain,
            "eid": str(uuid.uuid4()),
            "session": self._session_id,
            "uri": uri,
            "ident": self._username,
            "created": datetime.datetime.now(),
            "hostname": Session.get_hostname(),
        }
        did_compress_payload = False
        if data is not None and 0 < len(data):
            # Check if should compress payload
            def recursive_estimate_dict_size(o):
                result = 0
                if o is not None:
                    if isinstance(o, dict):
                        d = o
                        for key, value in list(d.items()):
                            result += len(key) + recursive_estimate_dict_size(value)
                    elif isinstance(o, list):
                        l = o
                        for _o in l:
                            result += recursive_estimate_dict_size(_o)
                    elif Session._is_str(o):
                        result += len(o)
                    else:
                        result += 10
                return result

            size = recursive_estimate_dict_size(data)
            if DEFAULT_EVENT_PAYLOAD_COMPRESS_SIZE_TRESHOLD < size:
                out = io.BytesIO()
                with gzip.GzipFile(fileobj=out, mode="w") as f:
                    f.write(Session._safe_dumps(data).encode('ascii'))
                b = out.getvalue()
                event["gz_data"] = base64.b64encode(b).decode('utf-8')
                self._verbose(
                    "Compressed event payload %d>%d(%s%%)"
                    % (
                        size,
                        len(event["gz_data"]),
                        (100 * len(event["gz_data"]) / size),
                    )
                )
                did_compress_payload = True
        if not did_compress_payload:
            event["data"] = data

        if query:
            event["query"] = query
        if entityid:
            event["id"] = entityid
        retval = self._rest(
            method,
            hostname=self._hostname,
            uri="/event",
            data=event,
            timeout=timeout,
            ssl=ssl,
            port=self._port,
            quiet=quiet,
        )
        return retval

    def decode_query(self, query):
        # Scenarios:
        #   entities
        #   attributes WHERE entitytype='job'
        #   Job WHERE code='my_transfer'
        #   Job WHERE (dest='lars@edit.com' OR ..)

        # First replace tabs with spaces, remove double spaces
        s = ""
        is_escaped = False
        is_at_whitespace = False
        query = (query or "").replace("\t", " ").replace("\n", "").strip()
        parts = []
        idx_part_start = 0
        paranthesis_depth = 0
        for idx in range(0, len(query)):
            do_append = True
            if query[idx] == " ":
                if not is_escaped and paranthesis_depth == 0:
                    if is_at_whitespace:
                        # Ignore this
                        do_append = False
                    else:
                        is_at_whitespace = True
                        if idx_part_start < idx:
                            # Add this part
                            parts.append(query[idx_part_start:idx])
                            idx_part_start = idx + 1
            else:
                is_at_whitespace = False
                if query[idx] == '"':
                    is_escaped = not is_escaped
                elif query[idx] == "(":
                    if not is_escaped:
                        paranthesis_depth += 1
                elif query[idx] == ")":
                    if not is_escaped:
                        paranthesis_depth -= 1
            if do_append:
                s += query[idx]
        if idx_part_start < len(query):
            parts.append(query[idx_part_start:])
        self._verbose('Query: "{}", parts: "{}"'.format(query, parts))
        assert len(parts) == 1 or 3 <= len(parts), (
            "Query has invalid syntax; statements can either be "
            'single ("<entity>"") or with a WHERE statement '
            '("<(sub)entity> WHERE {<entity>.}id=..{ AND ..}"")'
        )
        if len(parts) == 1:
            return {"entitytype": parts[0].lower()}
        else:
            assert (
                parts[1].strip().lower() == "where"
            ), 'Invalid query "{}", should be on the form ' '"<entitytype> where <expression>".'.format(query)
            # Decode expression
            return {
                "entitytype": parts[0].lower(),
                "expression": (" ".join(parts[2:])).lower(),
            }

    @staticmethod
    def _get_base_uri(entitytype):
        uri_base = entitytype
        # Send query to server, first determine uri
        # if entitytype == 'share':
        #   uri_base = 'organization/share'
        if entitytype == "site":
            uri_base = "organization/site"
        elif entitytype == "queue":
            uri_base = "job"
        elif entitytype == "task":
            uri_base = "job/task"
        return uri_base

    @staticmethod
    def _warning(s, standout=True):
        """
        Utility; Print warning message to logfile or stdout.

        :param s: The message to print.
        :param standout: If True, statement will be made more visible.
        :return: The message.

        """
        if Session._p_logfile:
            with open(Session._p_logfile, "a") as f:
                if standout:
                    f.write("[WARNING]" + "-" * 80 + "\n")
                f.write("[WARNING]" + s + "\n")
                if standout:
                    f.write("[WARNING]" + "-" * 80 + "\n")
        else:
            if standout:
                logging.warning("-" * 80)
            logging.warning(s)
            if standout:
                logging.warning("-" * 80)
        return s

    def _verbose(self, s):
        if self._be_verbose:
            Session._info("[ACCSYN_API] %s" % (s))

    @staticmethod
    def _safe_dumps(d, indent=None):
        if 3 <= sys.version_info.major:
            return json.dumps(d if not isinstance(d, list) else list(d.values()), cls=JSONEncoder, indent=indent)
        else:
            return json.dumps(d, cls=JSONEncoder, indent=indent)

    @staticmethod
    def _safely_printable(s):
        return ((s or "").encode()).decode("ascii", "ignore")

    @staticmethod
    def _is_str(s):
        if 3 <= sys.version_info.major:
            return isinstance(s, str)
        else:
            return isinstance(s, str) or isinstance(s, unicode)

    @staticmethod
    def _url_quote(url):
        if 3 <= sys.version_info.major:
            return urllib.parse.quote(Session._safe_dumps(url))
        else:
            return urllib.quote(Session._safe_dumps(url))

    @staticmethod
    def _json_serial(obj):
        """JSON serializer for *obj not serializable by default json code."""
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    @staticmethod
    def _base64_encode(s):
        """Produce a BASE64 encoded string."""
        if 3 <= sys.version_info.major:
            return (base64.b64encode(s.encode("utf-8"))).decode("ascii")
        else:
            if isinstance(s, str) or isinstance(s, unicode):
                return base64.b64encode(s)
            else:
                return binascii.b2a_base64(s)


class AccsynException(Exception):
    def __init__(self, message):
        super(AccsynException, self).__init__(message)
