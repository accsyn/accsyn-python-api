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

import urllib.parse
import base64
import io
import gzip

import re
import requests

from typing import Any, Dict, List, Optional, Union, cast

from ._version import __version__

try:
    requests.packages.urllib3.disable_warnings()
except BaseException:
    logging.error(traceback.format_exc())

logging.basicConfig(
    format="(%(thread)d@%(asctime)-15s) %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

ACCSYN_BACKEND_DOMAIN = "accsyn.com"
ACCSYN_BACKEND_MASTER_HOSTNAME = f"master.{ACCSYN_BACKEND_DOMAIN}"
ACCSYN_PORT = 443
DEFAULT_EVENT_PAYLOAD_COMPRESS_SIZE_TRESHOLD = 100 * 1024  # Compress event data payloads above 100k

CLEARANCE_SUPPORT = "support"
CLEARANCE_ADMIN = "admin"
CLEARANCE_EMPLOYEE = "employee"
CLEARANCE_STANDARD = "standard"
CLEARANCE_CLIENT = CLEARANCE_STANDARD  # BWCOMP
CLEARANCE_NONE = "none"

CLIENT_TYPE_APP = 0
CLIENT_TYPE_SERVER = 1
CLIENT_TYPE_USERSERVER = 2
CLIENT_TYPE_BROWSER = 3
CLIENT_TYPE_COMPUTE_LANE = 4
CLIENT_TYPE_ACCSYN_VPX = 5

CLIENT_STATE_INIT = "init"
CLIENT_STATE_ONLINE = "online"
CLIENT_STATE_OFFLINE = "offline"
CLIENT_STATE_DISABLED = "disabled"
CLIENT_STATE_DISABLED_OFFLINE = "disabled-offline"

JOB_TYPE_TRANSFER = 1   # p2p transfer job, either standalone or beneath a delivery/request
JOB_TYPE_QUEUE = 2  # A job contai
JOB_TYPE_COMPUTE = 3    # A compute/render job
JOB_TYPE_DELIVERY = 7 # An outgoing delivery job, hold one or more upload jobs for managers and one download job per recipient
JOB_TYPE_REQUEST = 8 # An inbound upload request, holds one upload job per recipient and then one or more download job for managers
JOB_TYPE_STREAM = 10 # An accsyn streaming delivery, same as delivery but containing one or more streamable media

class JSONEncoder(json.JSONEncoder):
    """JSON serialiser."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
            # Convert to UTC if datetime, otherwise use as-is for date
            if isinstance(obj, datetime.datetime):
                # If naive (no timezone), assume local timezone
                if obj.tzinfo is None:
                    # Get local timezone and apply it
                    local_tz = datetime.datetime.now().astimezone().tzinfo
                    obj = obj.replace(tzinfo=local_tz)
                # Convert to UTC before sending to backend
                obj = obj.astimezone(datetime.timezone.utc)
            return obj.strftime("%Y-%m-%dT%H:%M:%S")
        return super().default(obj)


class JSONDecoder(json.JSONDecoder):
    """JSON deserialize."""

    def decode(self, json_string: str) -> Any:
        json_data = json.loads(json_string)

        def recursive_decode(d: Any) -> Any:
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
                                dt = datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%S")
                            else:
                                dt = datetime.datetime.strptime(d[key], "%y-%m-%dT%H:%M:%S")
                            # Backend sends UTC, convert to local timezone
                            dt = dt.replace(tzinfo=datetime.timezone.utc)
                            d[key] = dt.astimezone()
                        # With millis
                        elif re.match(
                            "^[0-9]{2,4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:" "[0-9]{2}:[0-9]{2}.[0-9]{3}$",
                            str(Session._safely_printable(d[key])),
                        ):
                            if len(d[key].split("-")[0]) == 4:
                                dt = datetime.datetime.strptime(d[key], "%Y-%m-%dT%H:%M:%S.%f")
                            else:
                                dt = datetime.datetime.strptime(d[key], "%y-%m-%dT%H:%M:%S.%f")
                            # Backend sends UTC, convert to local timezone
                            dt = dt.replace(tzinfo=datetime.timezone.utc)
                            d[key] = dt.astimezone()
            return d

        return recursive_decode(json_data)


def _load_env_file(path: str, override: bool = False) -> None:
    """
    Load environment variables from a .env file.
    
    :param path: Path to the .env file
    :param override: If True, override existing environment variables. If False, only set if not already set.
    """
    if not os.path.exists(path):
        return
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                # Strip whitespace and skip empty lines
                line = line.strip()
                if not line:
                    continue
                
                # Skip comments (lines starting with #)
                if line.startswith("#"):
                    continue
                
                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if len(value) >= 2:
                        if (value.startswith('"') and value.endswith('"')) or (
                            value.startswith("'") and value.endswith("'")
                        ):
                            value = value[1:-1]
                    
                    # Only set if not already set (unless override=True)
                    if override or key not in os.environ:
                        os.environ[key] = value
    except (IOError, OSError) as e:
        logging.error(traceback.format_exc())


class Session(object):
    """accsyn API session object."""

    DEFAULT_CONNECT_TIMEOUT: int = 10  # Wait 10 seconds for connection
    DEFAULT_TIMEOUT: int = 2 * 60  # Wait 2 minutes for response

    _p_logfile: Optional[str] = None

    @property
    def username(self) -> str:
        return self._username

    @property
    def timeout(self) -> int:
        return self._timeout

    @property
    def connect_timeout(self) -> int:
        return self._connect_timeout

    def __init__(
        self,
        workspace: Optional[str] = None,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        hostname: Optional[str] = None,
        port: Optional[int] = None,
        proxy: Optional[str] = None,
        verbose: bool = False,
        pretty_json: bool = False,
        path_logfile: Optional[str] = None,
        timeout: Optional[int] = None,
        connect_timeout: Optional[int] = None,
        domain: Optional[str] = None,
        path_envfile: Optional[str] = None,
    ) -> None:
        """
        Initiate a new API session object. Throws exception upon authentication failure.

        :param workspace: The accsyn workspace code (or read from ACCSYN_WORKSPACE environment variable)
        :param username: The accsyn username (or read from ACCSYN_API_USER environment variable)
        :param api_key: The secret API key for authentication (or read from ACCSYN_API_KEY environment variable)
        :param hostname: Override the hostname/IP of the workspace to connect to.
        :param port: Override default port (443/TCP)
        :param proxy: The proxy settings (or read from ACCSYN_PROXY environment variable).
        :param verbose: Printing verbose debugging output to stdout.
        :param pretty_json: (verbose) Print pretty formatted JSON.
        :param path_logfile: Output all log messages to this logfile instead of stdout.
        :param timeout: Timeout in seconds for API calls - waiting for response.
        :param connect_timeout: Timeout in seconds for API calls - waiting for connection.
        :param domain: (Backward compatibility) The accsyn domain (or read from ACCSYN_DOMAIN environment variable)
        :param path_envfile: Path to .env file to load credentials from (or read from ACCSYN_CREDENTIALS_PATH environment variable)

        .. deprecated:: 3.1.0
            Use the :param workspace: parameter instead
        """
        self._be_verbose = verbose
        # Load .env file if specified or if ACCSYN_CREDENTIALS_PATH is set
        env_file_path = path_envfile or os.environ.get("ACCSYN_CREDENTIALS_PATH")
        if env_file_path:
            self._verbose(f"Loading credentials from {env_file_path}")
            _load_env_file(env_file_path, override=True)
        elif os.path.exists(".env"):
            self._verbose(f"Loading credentials from .env")
            # Also try loading .env from current directory if no path specified
            _load_env_file(".env", override=True)

        # Generate a session ID
        self.__version__ = __version__
        self._session_id = None
        self._uid = None
        self._api_key = None
        self._pretty_json = pretty_json
        self._proxy = proxy
        self._dev = os.environ.get('AS_DEV', 'false') in ['true', '1']
        Session._p_logfile = path_logfile
        self._role = CLEARANCE_NONE
        self._verbose(f"Creating accsyn Python API session (v{__version__})")
        if not workspace:
            workspace = domain
        if not workspace:
            for key in ["ACCSYN_WORKSPACE", "ACCSYN_DOMAIN", "ACCSYN_ORG"]:
                if key in os.environ:
                    workspace = os.environ[key]
                    break
        if not workspace:
            raise AccsynException("Please supply your accsyn workspace domain or set ACCSYN_WORKSPACE environment!")
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
                # Resolve workspace hostname
                response = self._rest(
                    "GET",
                    ACCSYN_BACKEND_MASTER_HOSTNAME,
                    "J3PKTtDvolDMBtTy6AFGA",
                    dict(ident=workspace),
                )
                # Store hostname
                if "message" in response:
                    raise AccsynException(response["message"])
                result = response.get('result', dict())
                assert "hostname" in result, f"No API endpoint hostname were provided for workspace {workspace}!"
                self._hostname = result["hostname"]
                if self._port is None:
                    self._port = result["port"]
        if self._port is None:
            self._port = ACCSYN_PORT if not self._dev else 8181
        self._workspace = workspace
        self._username = username
        self._api_key = api_key
        self._last_message = None
        self._login()

    @staticmethod
    def get_hostname() -> str:
        """
        :return: The hostname of this computer.
        """
        return socket.gethostname()

    @staticmethod
    def _info(s: str, standout: bool = False) -> str:
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
    def str(d: Optional[Dict[str, Any]], indent: int = 4) -> str:
        """Return a string representation of a dict"""
        return json.dumps(d, default=Session._json_serial, indent=indent) if d is not None else "None"

    def get_last_message(self) -> Optional[str]:
        """Retreive error message from last API call."""
        return self._last_message

    def _login(self) -> bool:
        """Attempt to authenticate with accsyn using the provided credentials, returns a session ID."""
        assert self._uid is None, "Already logged in!"
        headers = {
            "Authorization": f"basic {Session._base64_encode(self._username)}:{Session._base64_encode(self._api_key)}",
            "X-Accsyn-Workspace": self._workspace,
        }
        response = self._rest(
            "PUT",
            self._hostname,
            "/api/login",
            dict(),
            headers=headers,
            port=self._port,
        )
        # Store session key
        assert "result" in response, "No result were provided!"
        result = response["result"]
        self._role = result["role"]
        self._uid = result["id"]
        self._session_id = result["session_id"]
        return True

    # Create

    def create(
        self,
        entitytype: str,
        data: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        entitytype_id: Optional[str] = None,
        allow_duplicates: bool = True,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a new accsyn entity.

        :param entitytype: The type of entity to create (job, share, acl)
        :param data: The entity data as a dictionary.
        :param entitytype_id: For creating sub entities (tasks), this is the parent (job) id.
        :param allow_duplicates: (jobs and tasks) Allow duplicates to be created.
        :return: The created entity data, as dictionary.
        """
        entitytype = (entitytype or "").lower().strip()
        assert entitytype, "You must provide the entity type to create!"
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
                data = dict(tasks=data)
            assert data is not None and 0 < len(data), "Empty create data submitted!"
        uri="create"
        if entitytype == "task" and "tasks" not in data:
            data = dict(tasks=data)
        if entitytype == "file":
            uri="add"
        if entitytype in ["transfer", "compute", "delivery", "request", "stream", "job", "task"]:
            data["allow_duplicates"] = allow_duplicates
        d = self._event(
            "POST",
            f"{entitytype}/{uri}",
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
        query: str,
        entityid: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        finished: Optional[bool] = None,
        inactive: Optional[bool] = None,
        offline: Optional[bool] = None, # Deprecated, use inactive instead
        archived: Optional[bool] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        create: bool = False,
        update: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Return (GET) a list of entities/entitytypes/attributes based on *query*.

        :param query: The query, a string on accsyn query format.
        :param entityid: The parent entity ID, required for sub entities "task" and "file".
        :param attributes: The attributes to return, default is to return all attributes with access.
        :param finished: (job) Search among inactive jobs.
        :param inactive: (user,share) Search among inactive entities.
        :param offline: (user,share) Search among offline entities. (Deprecated)
        :param archived: Search among archived (deleted/purged) entities.
        :param limit: The maximum amount of entities to return.
        :param skip: The amount of entities to skip.
        :param create: (attributes) Return create (POST) attributes.
        :param update: (attributes) Return update (PUT) attributes.
        :return: List of dictionaries.
        """
        assert 0 < len(query or "") and Session._is_str(query), "Invalid query type supplied, must be of string type!"

        retval = None
        d = self._decode_query(query)
        data = dict()
        if d["entitytype"] == "entitytypes":
            # Ask cloud server, the Python API is rarely updated and should not
            # need to know
            d = self._event("GET", "entitytypes", dict())
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
                dict(entitytype=entitytype, create=create, update=update),
            )
            if d:
                retval = d["result"]
        else:
            # Send query to server, first determine uri
            if entityid is not None:
                data["parent"] = entityid
            if finished is not None:
                data["finished"] = finished
            if inactive is not None:
                data["inactive"] = inactive
            elif offline is not None:
                logging.warning(f"[WARNING] The 'offline' parameter is deprecated, use 'inactive' instead.")
                data["inactive"] = offline
            if archived is not None:
                data["archived"] = archived
            if limit:
                data["limit"] = limit
            if skip:
                data["skip"] = skip
            if attributes:
                data["attributes"] = attributes
            d = self._event("GET", f"{d['entitytype']}/find", data, query=d.get("expression"))
            if d:
                retval = d["result"]
        return retval

    def find_one(
        self,
        query: str,
        attributes: Optional[List[str]] = None,
        finished: Optional[bool] = None,
        offline: Optional[bool] = None,
        archived: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
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
            if 1<len(result):
                logging.warning(f"[WARNING] Multiple entities retreived({len(result)}), returning first one.")
            return retval
        return None

    def report(self, query: str) -> str:
        """
        (Support) Return an internal backend report of an entity.

        :param query: The query, a string on accsyn query format.
        :return: A text string containing the human readable report.
        """
        d = self._decode_query(query)
        data = dict()
        d = self._event("GET", f"{d['entitytype']}/report", data, query=d.get("expression"))
        return d["report"]

    def metrics(
        self, query: str, attributes: Optional[List[str]] = None, time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return metrics for an entity (job)

        .. versionadded:: 2.0

        :param query:
        :param attributes:
        :param time:
        :return:
        """
        d = self._decode_query(query)
        data = dict(
            attributes=attributes,
        )
        if not time is None:
            data["time"] = time
        d = self._event("GET", f"{d['entitytype']}/metrics", data, query=d.get("expression"))
        return d["result"]

    # Update an entity

    def update(
        self, 
        entitytype: str, 
        entityid: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update/modify an entity.

        :param entitytype: The type of entity to update (job, share, acl, ..)
        :param entityid: The entity ID of the parent entity to update (job).
        :param data: The dictionary containing attributes to update.
        :return: The updated entity data, as dictionary.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        if entitytype == "acl":
            raise AccsynException("ACLs cannot be updated, use the grant function to grant access.")
        assert 0 < len(entityid or "") and Session._is_str(
            entityid
        ), "Invalid entity ID supplied, must be of string type!"
        assert 0 < len(data or dict()) and isinstance(data, dict), "Invalid data supplied, must be dict and have content!"
        response = self._event(
            "PUT",
            f"{entitytype}/edit",
            data,
            entityid=entityid,
        )
        if response:
            return response["result"][0]

    def update_one(
        self, 
        entitytype: str, 
        entityid: str, 
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        '''
        Update/modify an entity.

        :param entitytype: The type of entity to update (job, share, acl, ..)
        :param entityid: The id of the entity.
        :param data: The dictionary containing attributes to update.
        :return: The updated entity data, as dictionary

        .. deprecated:: 2.0.2
            Since version 2.0.2 you should use the :func:`update` function instead

        '''
        return self.update(entitytype, entityid, data)

    def update_many(
        self, 
        entitytype: str, 
        entityid: str,
        data: List[Dict[str, Any]], 
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Update/modify multiple entities - tasks beneath a job.

        :param entitytype: The type of parent entity to update (job)
        :param entityid: The id of the parent entity job to update
        :param data: The list dictionaries containing sub entity (task) id and attributes to update.
        :return: The updated sub entities (tasks), as dictionaries.

        .. changed:: 3.2.0
            The entityid and data parameters have switched places.

        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert entitytype == "task", "Only multiple 'task' entities can be updated!"
        if entitytype == "acl":
            raise AccsynException("ACLs cannot be updated, use the grant function to grant access.")
        assert 0 < len(entityid or "") and (
            Session._is_str(entityid)
        ), "Entity ID must be provided and be of string type!"
        if not re.match("^[a-z0-9]{24}$", (entityid or "")):
            raise Exception("Invalid parent entity ID supplied!")
        assert 0 < len(data or []) and isinstance(data, list), "Invalid data supplied, must be a list!"
        response = self._event(
            "PUT",
            f"{entitytype['entitytype']}/edit",
            data,
            entityid=entityid,
        )
        if response:
            return response["result"]

    # Entity assignment / connections

    def assign(
        self,
        entitytype_parent: str,
        entitytype: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Assign one entity to another.

        .. versionadded:: 2.0

        :param entitytype_parent: The parent entity type to assign entity to.
        :param entitytype_other: The entity type to assign to parent entity.
        :param data: Assignment data, should contain parent entity id and entity ids.
        :return: True if assignment was a success, exception otherwise.
        """
        assert 0 < len(entitytype_parent or "") and Session._is_str(
            entitytype_parent
        ), "Invalid parent entity type supplied, must be of string type!"
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype_parent = entitytype_parent.lower().strip()
        entitytype = entitytype.lower().strip()
        assert (
            not data is None and isinstance(data, dict) and (0 < len(data or dict()))
        ), "Invalid assignment data supplied, must be a dict with values!"
        response = None
        if entitytype_parent in ["volume", "share"] and entitytype in ["server", "client"]:
            # Assign a server to a share, expect share and client supplied
            share_id = data.get("volume", data.get("share"))
            assert re.match("^[a-z0-9]{24}$", (share_id or "")), "Please supply parent entity ID as 'volume' with assignment data!"
            client_id = data.get("server", data.get("client"))
            assert re.match("^[a-z0-9]{24}$", (client_id or "")), "Please supply entity ID as 'server' with assignment data!"
            response = self._event(
                "PUT",
                f"share/server",
                dict(
                    client=client_id,
                ),
                entityid=share_id,
            )
        elif entitytype_parent in ["delivery"] and entitytype in ["user"]:
            # Assign a user to a delivery, expect delivery and user supplied
            delivery_id = data.get("delivery")
            assert re.match("^[a-z0-9]{24}$", (delivery_id or "")), "Please supply parent entity ID as 'delivery' with assignment data!"
            user_id = data.get("user")
            assert re.match("^[a-z0-9]{24}$", (user_id or "")), "Please supply entity ID as 'user' with assignment data!"
            response = self._event(
                "PUT",
                f"job/recipient/add",
                dict(recipient=user_id),
                entityid=delivery_id,
            )
        elif entitytype_parent in ["volume","folder","home","collection"] and entitytype in ["user"]:
            # Assign an employee user to a volume
            volume_id = data.get("volume")
            assert re.match("^[a-z0-9]{24}$", (volume_id or "")), "Please supply parent entity ID as 'volume' with assignment data!"
            user_id = data.get("user")
            assert re.match("^[a-z0-9]{24}$", (user_id or "")), "Please supply entity ID as 'user' with assignment data!"
            payload = dict(
                entity=f"user:{user_id}",
                target=f"share:{volume_id}",
                read=data.get("read", True),
                write=data.get("write", True),
                notify=data.get("notify", True),
                message=data.get("message", "")
            )
            response = self._event(
                "POST",
                f"acl/create",
                payload
            )
        if response is not None:
            return response["result"]
        else:
            raise Exception("Unsupported assignment operation!")

    def assignments(self, entitytype: str, entityid: str) -> List[Dict[str, Any]]:
        """
        Return list of assigned entities.

        This can be used to list servers assigned to a volume.

        .. versionadded:: 2.0

        :param query:
        :return: List of dictionaries.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid parent entity type supplied, must be of string type!"
        if entitytype.lower() in ["volume", "share"]: # share is deprecated since 3.2
            # List servers assigned to a volume
            response = self._event(
                "GET",
                f"{entitytype}/servers",
                dict(),
                entityid=entityid,
            )
            return response["result"]
        else:
            raise Exception("Unsupported assignment operation!")

    def deassign(
        self,
        entitytype_parent: str,
        entitytype: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        De-assign one entity from another.

        .. versionadded:: 2.0

        :param entitytype_parent: The parent entity type to deassign entity from
        :param entitytype: The entity type to deassign from parent entity
        :param data: De-assignment data, should contain parent entity id and entity ids + additional information as required
        :return: True if deassignment was a success, exception otherwise.
        """
        assert 0 < len(entitytype_parent or "") and Session._is_str(
            entitytype_parent
        ), "Invalid parent entity type supplied, must be of string type!"
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid centity type supplied, must be of string type!"
        entitytype_parent = entitytype_parent.lower().strip()
        entitytype = entitytype.lower().strip()
        assert (
            not data is None and isinstance(data, dict) and (0 < len(data or dict()))
        ), "Invalid de-assignment data supplied, must be a dict with values!"
        response = None
        if entitytype_parent in ["volume", "share"] and entitytype == "server":
            # Assign a server to a share, expect share and client supplied
            share_id = data.get("volume", data.get("share"))
            assert re.match("^[a-z0-9]{24}$", (share_id or "")), "Please supply parent entity ID as 'volume' with de-assignment data!"
            client_id = data.get("server", data.get("client"))
            assert re.match("^[a-z0-9]{24}$", (client_id or "")), "Please supply entity ID as 'server' with de-assignment data!"
            response = self._event(
                "DELETE",
                f"{entitytype_parent}/server",
                dict(client=client_id),
                entityid=share_id,
            )
        if response is not None:
            return response["result"]
        else:
            raise Exception("Unsupported assignment operation!")

     # Entity access grant / revocation

    def grant(
        self,
        entitytype: str,
        entitityid: str,
        targettype: str,
        targetid: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Grant access to an entity.

        .. versionadded:: 3.2

        :param entitytype: The entity type that should be granted access.
        :param entitityid: The id of the entity that should be granted access.
        :param targettype: The entity type to grant access to.
        :param targetid: The id of the entity to grant access to.
        :param data: ACL data, should permissions and other data.
        :return: True if assignment was a success, exception otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entitityid or "") and Session._is_str(
            entitityid
        ), "Invalid entity ID supplied, must be of string type!"
        entitityid = entitityid.lower().strip()
        assert re.match("^[a-z0-9]{24}$", (entitityid or "")), "Please supply a valid entity ID!"
        assert 0 < len(targettype or "") and Session._is_str(
            targettype
        ), "Invalid target entity type supplied, must be of string type!"
        targettype = targettype.lower().strip()
        assert 0 < len(targetid or "") and Session._is_str(
            targetid
        ), "Invalid entity type supplied, must be of string type!"
        targetid = targetid.lower().strip()
        assert re.match("^[a-z0-9]{24}$", (targetid or "")), "Please supply a target valid ID!"
        assert (
            not data is None and isinstance(data, dict) and (0 < len(data or dict()))
        ), "Invalid grant access data supplied, must be a dict with values!"
        result = None
        if entitytype == "user" and targettype in ["delivery"]:
            # Assign a user to a delivery, expect delivery and user supplied
            user_id = entitityid
            delivery_id = targetid
            response = self._event(
                "PUT",
                f"job/recipient/add",
                dict(recipient=user_id),
                entityid=delivery_id,
            )
            result = response["result"]
        elif entitytype == "user" and targettype in ["volume","folder","home","collection"]:
            # Assign an employee user to a volume
            user_id = entitityid
            volume_id = targetid
            payload = dict(
                entity=f"user:{user_id}",
                target=f"share:{volume_id}",
                read=data.get("read", True),
                write=data.get("write", True),
                notify=data.get("notify", True),
                message=data.get("message", ""),
                path=data.get("path", "/"),
            )
            response = self._event(
                "POST",
                f"acl/create",
                payload
            )
            acl = response["result"][0]
            result = dict(
                user=acl["entity"].split(":")[1],
                user_hr=acl.get("entity_hr", ""),
                read=acl["read"],
                write=acl["write"],
                acknowledged=acl.get("acknowledged", False),
            )
        if result is not None:
            return result
        else:
            raise Exception("Unsupported grant access operation!")

    def access(self, targettype: str, targetid: str, recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Return list of ACLs for an entity.

        This can be used to list user with access to a delivery or a share (volume, folder, home, collection).

        .. versionadded:: 3.2

        :param targettype: The entity type to list access for (delivery, volume, folder, home, collection).
        :param targetid: The id of the entity to list access for.
        :param recursive: If True, list ACLs for all shares beneath the target volume, folder or home.
        :return: List of dictionaries.
        """
        assert 0 < len(targettype or "") and Session._is_str(
            targettype
        ), "Invalid parent target type supplied, must be of string type!"
        targettype = targettype.lower().strip()
        assert 0 < len(targetid or "") and Session._is_str(
            targetid
        ), "Invalid target id supplied, must be of string type!"
        targetid = targetid.lower().strip()
        assert re.match("^[a-z0-9]{24}$", (targetid or "")), "Please supply a valid entity ID!"

        if targettype.lower() in ["delivery"]:
            # List recipients assigned to a delivery
            response = self._event(
                "GET",
                f"job/recipients",
                dict(),
                entityid=targetid,
            )
            return response["result"]
        elif targettype.lower() in ["volume", "folder", "home","collection"]:
            # List users with access to a share
            response = self._event(
                "GET",
                f"acl/find",
                dict(recursive=recursive),
                query=f"acl WHERE target=share:{targetid}",
            )
            result = []
            for acl in response["result"]:
                result.append(dict(
                    user=acl["entity"].split(":")[1],
                    user_hr=acl.get("entity_hr", ""),
                    share=acl["target"].split(":")[1],
                    share_hr=acl.get("target_hr", ""),
                    read=acl["read"],
                    write=acl["write"],
                    acknowledged=acl.get("acknowledged", False),
                    path=acl.get("path", "/"),
                ))
            return result
        else:
            raise Exception("Unsupported access operation!")

    def revoke(
        self,
        entitytype: str,
        entityid: str,
        targettype: str,
        targetid: str
    ) -> bool:
        """
        Revoke access to an entity.

        .. versionadded:: 3.2

        :param entity: The entity type to revoke access for.
        :param entityid: The id of the entity to revoke access for.
        :param target: The entity type to revoke access from.
        :param targetid: The id of the entity to revoke access from.
        :param data: ACL data, should contain parent entity id and entity ids.
        :return: True if revocation was a success, exception otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityid or "") and Session._is_str(
            entityid
        ), "Invalid entity id supplied, must be of string type!"
        entityid = entityid.lower().strip()
        assert re.match("^[a-z0-9]{24}$", (entityid or "")), "Please supply a valid entity ID!"
        assert 0 < len(targettype or "") and Session._is_str(
            targettype
        ), "Invalid target entity type supplied, must be of string type!"
        targettype = targettype.lower().strip()
        assert 0 < len(targetid or "") and Session._is_str(
            targetid
        ), "Invalid target entity id supplied, must be of string type!"
        targetid = targetid.lower().strip()
        assert re.match("^[a-z0-9]{24}$", (targetid or "")), "Please supply a valid entity ID!"
        response = None
        if targettype in ["delivery"] and entitytype == "user":
            # Revoke user access from a delivery, expect delivery and user supplied
            delivery_id = targetid
            user_id = entityid
            response = self._event(
                "DELETE",
                f"job/recipient",
                dict(recipient=user_id),
                entityid=delivery_id,
            )
        elif targettype in ["volume","folder","home","collection"] and entitytype == "user":
            # Revoke user access from a share
            share_id = targetid
            user_id = entityid
            # First, located the ACL
            response = self._event("GET", f"acl/find", dict(), query=f"acl WHERE entity=user:{user_id} AND target=share:{share_id}")
            acls = response["result"]
            if len(acls) == 0:
                raise AccsynException(f"No ACL found for user {user_id} and share {share_id}")
            response = self._event(
                "DELETE",
                f"acl/delete",
                dict(),
                entityid=acls[0]["id"],
            )
        if response is not None:
            return response["result"]
        else:
            raise Exception("Unsupported revoke access operation!")


    # Deactivate/Delete an entity

    def offline_one(self, entitytype: str, entityid: str) -> Any:
        """
        Deactivate an entity - remove from accsyn but keep in database for audit/later restoration.

        .. deprecated:: 3.2.0
            Use the :func:`deactivate_one` function instead

        """
        return self.deactivate_one(entitytype, entityid)

    def deactivate_one(self, entitytype: str, entityid: str) -> Any:
        """
        Deactivate an entity - remove from accsyn but keep in database for audit/later restoration.

        .. versionadded:: 3.2

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
            f"{entitytype}/deactivate",
            dict(),
            entityid=entityid,
        )
        if response:
            return response["result"]

    def delete_one(self, entitytype: str, entityid: str) -> Any:
        """
        Delete(archive) an entity.

        :param entitytype: The type of entity to delete (job, share, acl, ..)
        :param entityid: The id of the entity.
        :return: True if deleted, an exception is thrown otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, provided and be of string type!"
        entitytype = entitytype.lower().strip()
        if entitytype == "acl":
            raise AccsynException("ACLs cannot be deleted, use the revoke function to revoke access.")
        assert 0 < len(entityid or "") and (
            Session._is_str(entityid)
        ), "Invalid entity ID supplie, provided and be of string type!"
        response = self._event(
            "DELETE",
            f"{entitytype}/delete",
            dict(),
            entityid=entityid,
        )
        if response:
            return response["result"]

    def delete_many(self, entitytype: str, entityid: str, data: Dict[str, Any]) -> Any:
        """
        Delete multiple sub entities (files) beneath a parent entity.

        :param entitytype: The type of parent entity to delete (job)
        :param entityid: The id of the parent entity job to delete
        :param data: The dictionary containing attributes to delete.
        :return: True if deleted, an exception is thrown otherwise.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityid or "") and (
            Session._is_str(entityid)
        ), "Invalid entity ID supplied, must be of string type!"
        if not re.match("^[a-z0-9]{24}$", (entityid or "")):
            raise AccsynException("Invalid parent entity ID supplied!")
        assert 0 < len(data or dict()) and isinstance(data, dict), "Invalid data supplied, must be dict and have content!"
        if entitytype == "collection":
            uri = "file/remove"
        else:
            raise AccsynException(f"Unsupported entity type for deletion: {entitytype}")
        response = self._event(
            "DELETE",
            f"{entitytype}/{uri}",
            data,
            entityid=entityid,
        )
        if response:
            return response["result"]

    # Activate an entity

    def activate_one(self, entitytype: str, entityident: str) -> Any:
        """
        Activate an entity - bring back from deactivated(offline) state.
        """
        assert 0 < len(entitytype or "") and Session._is_str(
            entitytype
        ), "Invalid entity type supplied, must be of string type!"
        entitytype = entitytype.lower().strip()
        assert 0 < len(entityident or "") and Session._is_str(
            entityident
        ), "Invalid entity identification supplied, must be of string type!"
        entityident = entityident.lower().strip()
        response = self._event(
            "POST",
            f"{entitytype}/activate",
            dict(),
            entityid=entityident if re.match("^[a-z0-9]{24}$", (entityident or "")) else None,
            query=entityident if not re.match("^[a-z0-9]{24}$", (entityident or "")) else None
        )
        if response:
            return response["result"]

    # File operations

    def ls(
        self,
        path: Union[str, Dict[str, Any], List[str]],
        recursive: bool = False,
        maxdepth: Optional[int] = None,
        getsize: bool = False,
        files_only: bool = False,
        directories_only: bool = False,
        include: Optional[Union[str, List[str]]] = None,
        exclude: Optional[Union[str, List[str]]] = None,
    ) -> Optional[Dict[str, Any]]:
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
        data = dict(
            op="ls",
            path=path,
            download=True,
            recursive=recursive,
            getsize=getsize,
        )
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
        response = self._event("GET", "workspace/file", data)
        if response:
            return response["result"]

    def getsize(
        self,
        path: Union[str, Dict[str, Any], List[str]],
        include: Optional[Union[str, List[str]]] = None,
        exclude: Optional[Union[str, List[str]]] = None,
    ) -> Optional[Dict[str, Any]]:
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
        data = dict(
            op="getsize",
            path=path,
        )
        if include:
            data["include"] = include
        if exclude:
            data["exclude"] = exclude
        response = self._event("GET", "workspace/file", data)
        if response:
            return response["result"]

    def exists(
        self, path: Union[str, Dict[str, Any], List[str]]
    ) -> Optional[bool]:
        """
        Check if a file or directory exists.

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = dict(
            op="exists",
            path=path,
        )
        response = self._event("GET", "workspace/file", data)
        if response:
            return response["result"]

    def mkdir(
        self, path: Union[str, Dict[str, Any], List[str]]
    ) -> Optional[Any]:
        """
        Create a directory on a share.

        .. versionadded:: 2.0

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = dict(
            op="mkdir",
            path=path,
        )
        response = self._event("POST", "workspace/file", data)
        if response:
            return response["result"]

    def rename(
        self,
        path: Union[str, Dict[str, Any], List[str]],
        path_to: Union[str, Dict[str, Any], List[str]],
    ) -> Optional[Any]:
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
        data = dict(
            op="rename",
            path=path,
            path_to=path_to,
        )
        response = self._event("PUT", "workspace/file", data)
        if response:
            return response["result"]

    def mv(
        self,
        path_src: Union[str, Dict[str, Any], List[str]],
        path_dst: Union[str, Dict[str, Any], List[str]],
    ) -> Optional[Any]:
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
        data = dict(
            op="move",
            path=path_src,
            path_to=path_dst,
        )
        response = self._event("PUT", "workspace/file", data)
        if response:
            return response["result"]

    def rm(
        self, path: Union[str, Dict[str, Any], List[str]]
    ) -> Optional[Any]:
        """
        Remove a file/directory on a share.

        .. versionadded:: 2.0

        :param path: The accsyn path, on the form 'share=<the share>/<path>/<somewhere>'.
        :return: True if file exists, False otherwise.
        """
        assert 0 < len(path or "") and (
            Session._is_str(path) or isinstance(path, dict) or isinstance(path, list)
        ), "No path supplied, or not a string/list/dict!"
        data = dict(
            op="mkdir",
            path=path,
        )
        response = self._event("POST", "workspace/file", data)
        if response:
            return response["result"]

    # Pre publish
    def prepublish(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pre-process a publish.

        :param data: The pre publish data, see documentation.
        :return: Processed publish data, see documentation.
        """
        if data is None or not isinstance(data, list):
            raise AccsynException("None or empty data supplied!")

        # Check entries, calculate size
        def recursive_get_size(files: List[Dict[str, Any]]) -> int:
            result = 0
            for d in files:
                if "size" not in d:
                    d["size"] = (
                        0 if not d.get("is_dir") is True or d.get("files") is None else recursive_get_size(d["files"])
                    )
                result += d["size"]
            return result

        event_data = dict(files=data, size=recursive_get_size(data))
        response = self._event("PUT", "workspace/publish/preprocess", event_data)
        return response["result"]

    # Settings

    def get_setting(
        self,
        name: Optional[str] = None,
        scope: str = 'workspace',
        entity_id: Optional[str] = None,
        integration: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        '''Retrive *name* setting for the given *scope* (workspace, job, share..), for optional *entity_id* or *integration* (ftrack,..)'''
        evt_data = dict(scope=scope, name=name)
        if entity_id:
            evt_data['ident'] = entity_id
        if integration:
            evt_data['integration'] = integration
        if evt_data:
            evt_data['data'] = data
        response = self._event("GET", "setting", evt_data)
        return response.get("result")

    def set_setting(
        self,
        name: str,
        value: Any,
        scope: str = 'workspace',
        entity_id: Optional[str] = None,
        integration: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        '''Set the setting identified by *name* to *value* for *entity_id* within *scope*.'''
        evt_data = dict(scope=scope, name=name, value=value)
        if entity_id:
            evt_data['ident'] = entity_id
        if integration:
            evt_data['integration'] = integration
        if evt_data:
            evt_data['data'] = data
        response = self._event("PUT", "setting", evt_data)
        return response.get("result")

    # Misc
    def get_api_key(self) -> str:
        """Fetch API key, by default disabled in backend."""
        return self._event("GET", "user/api_key", dict())["api_key"]

    def gui_is_running(self) -> Optional[bool]:
        """Backward compability"""
        return self.app_is_running()

    def app_is_running(self) -> Optional[bool]:
        """
        Check if the accsyn desktop app is running on the same machine (code/hostname match) and with same user ID.

        Equivalent to do client query with user, code and type.

        :return: True if found, False otherwise.
        """
        result = self._event(
            "GET",
            "client/find",
            dict(),
            query=f"user={self._uid} AND code={Session.get_hostname()} AND type={CLIENT_TYPE_APP}",
        )["result"]
        retval = None
        if 0 < len(result):
            for c in result:
                retval = c["status"] in [CLIENT_STATE_ONLINE, CLIENT_STATE_DISABLED]
                if retval is True:
                    break
        return retval

    def server_is_running(self) -> Optional[bool]:
        """Backward compatibility"""
        return self.daemon_is_running()

    def daemon_is_running(self) -> Optional[bool]:
        """
        Check if a daemon is running on the same machine (code/hostname match) with same user ID.

        Equivalent to do client query with user, code and type.

        :return: True if found, False otherwise.
        """
        result = self._event(
            "GET",
            "client/find",
            dict(),
            query=f"user={self._uid} AND code={Session.get_hostname()} AND (type={CLIENT_TYPE_SERVER} OR type={CLIENT_TYPE_USERSERVER})",
        )["result"]
        retval = None
        if 0 < len(result):
            for c in result:
                retval = c["status"] in [CLIENT_STATE_ONLINE, CLIENT_STATE_DISABLED]
                if retval is True:
                    break
        return retval

    def integration(
        self, name: str, operation: str, data: Dict[str, Any]
    ) -> Any:
        '''Make an integration utility call for integration pointed out by *name* and providing the *operation* as string and *data* as a dictionary'''
        assert len(name) > 0, 'No name provided'
        assert len(operation) > 0, 'No operation provided'
        return self._event(
            "PUT",
            f"workspace/integration/{name}/utility",
            {
                'operation': operation,
                'data': data,
            },
        )["result"]

    # Help
    def help(self) -> None:
        print("Please have a look at the Python API reference: " "https://accsyn-python-api.readthedocs.io/en/latest/")

    # Internal utility functions

    @staticmethod
    def _obscure_dict_string(s: Optional[str]) -> Optional[str]:
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
        method: str,
        hostname: Optional[str],
        uri: str,
        data: Optional[Dict[str, Any]],
        timeout: Optional[int] = None,
        ssl: bool = True,
        port: Optional[int] = None,
        quiet: bool = False,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
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
            hostname = f"{self._workspace}.{ACCSYN_BACKEND_DOMAIN}"
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
            self._verbose(f"Using accsyn proxy @ {proxy_hostname}:{proxy_port}")
            hostname = proxy_hostname
            port = proxy_port
        elif proxy_type in ["socks", "socks5"]:
            try:
                self._verbose(f"Using SOCKS5 proxy @ {proxy_hostname}:{proxy_port}")
                try:
                    import socks
                except ImportError as ie:
                    logging.error("socks module is not installed, please install it with 'pip install socks' or add it to your PYTHONPATH")
                    raise ie

                socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, proxy_hostname, proxy_port)
                socket.socket = socks.socksocket
            except ImportError as ie:
                Session._warning('Python lacks SOCKS support, please install "pysocks" and' " try again...")
                raise ie
        elif proxy_type is not None:
            raise AccsynException(f'Unknown proxy type "{proxy_type}"!')
        url = f"http{'s' if ssl else ''}://{hostname}:{port}/api/v3{('/' if not uri.startswith('/') else '') + uri}"
        if timeout is None:
            timeout = self.timeout
        if data is None:
            data = dict()
        # Wait 10s to reach machine, 2min for it to send back data
        CONNECT_TO, READ_TO = (self.connect_timeout, timeout)
        r = None
        retval = None

        headers_effective = dict()
        if headers:
            headers_effective = copy.deepcopy(headers)
        elif self._api_key:
            headers_effective = {
                "Authorization": f"basic {Session._base64_encode(self._username)}:{Session._base64_encode(self._api_key)}",
                "X-Accsyn-Workspace": self._workspace,
            }
        headers_effective[
            "X-Accsyn-Device"
        ] = f"PythonAPI v{__version__} @ {sys.platform} {Session.get_hostname()}({os.name})"
        t_start = int(round(time.time() * 1000))
        try:
            self._verbose(f"REST {method} {url}, data: {data if not self._pretty_json else Session.str(data)}")
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
                f"Could not reach {hostname}:{port}! Make sure backend({hostname}) can be reached from you location and no firewall is blocking outgoing TCP traffic at port {port}. Details: {traceback.format_exc() if not quiet else '(quiet)'}"
            )
        try:
            retval = json.loads(r.text, cls=JSONDecoder)
            if not quiet:
                str_result = Session._obscure_dict_string(
                    Session._safely_printable(str(retval) if not self._pretty_json else Session.str(retval)).replace(
                        "'", '"'
                    )
                )
                self._verbose(f"{hostname}/{uri} REST {method} result: {str_result} (~{t_start - t_end + 1}ms)")
        except BaseException:
            sys.stderr.write(traceback.format_exc())
            str_data = Session._obscure_dict_string(Session._safely_printable(str(data)).replace("'", '"'))
            message = (
                f'The {url} REST {method} {str_data} operation failed! Details: {r.text} {traceback.format_exc()}'
            )
            Session._warning(message)
            raise AccsynException(message)

        if "exception" in retval:
            message = f"{uri} caused an exception! Please contact {self._workspace} admin for more further support."
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
        method: str,
        uri: str,
        data: Optional[Dict[str, Any]],
        query: Optional[str] = None,
        entityid: Optional[str] = None,
        timeout: Optional[int] = None,
        ssl: bool = True,
        quiet: bool = False,
    ) -> Dict[str, Any]:
        """Utility; Construct an event and send using REST to accsyn backend."""
        assert self._uid, "Login before posting event!"
        event = dict(
            audience="api",
            workspace=self._workspace,
            eid=str(uuid.uuid4()),
            session=self._session_id,
            uri=uri,
            ident=self._username,
            created=datetime.datetime.now(),
            hostname=Session.get_hostname(),
        )
        did_compress_payload = False
        if data is not None and 0 < len(data):
            # Check if should compress payload
            def recursive_estimate_dict_size(o: Any) -> int:
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
                    f"Compressed event payload {size}>{len(event['gz_data'])}({100 * len(event['gz_data']) / size}%)"
                )
                did_compress_payload = True
        if not did_compress_payload:
            event["data"] = data

        if query:
            event["query"] = query
        if entityid:
            event["id"] = entityid
        response = self._rest(
            method,
            hostname=self._hostname,
            uri="/event",
            data=event,
            timeout=timeout,
            ssl=ssl,
            port=self._port,
            quiet=quiet,
        )
        return response

    def _decode_query(self, query: str) -> Dict[str, str]:
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
        self._verbose(f'Query: "{query}", parts: "{parts}"')
        assert len(parts) == 1 or 3 <= len(parts), (
            "Query has invalid syntax; statements can either be "
            'single ("<entity>"") or with a WHERE statement '
            '("<(sub)entity> WHERE {<entity>.}id=..{ AND ..}"")'
        )
        if len(parts) == 1:
            return dict(entitytype=parts[0].lower())
        else:
            assert (
                parts[1].strip().lower() == "where"
            ), f'Invalid query "{query}", should be on the form "<entitytype> where <expression>".'
            # Decode expression
            return {
                "entitytype": parts[0].lower(),
                "expression": (" ".join(parts[2:])).lower(),
            }

    @staticmethod
    def _warning(s: str, standout: bool = True) -> str:
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

    def _verbose(self, s: str) -> None:
        if self._be_verbose:
            Session._info(f"[ACCSYN_API] {s}")

    @staticmethod
    def _safe_dumps(d: Any, indent: Optional[int] = None) -> str:
        return json.dumps(d if not isinstance(d, list) else list(d.values()), cls=JSONEncoder, indent=indent)

    @staticmethod
    def _safely_printable(s: Optional[str]) -> str:
        return ((s or "").encode()).decode("ascii", "ignore")

    @staticmethod
    def _is_str(s: Any) -> bool:
        return isinstance(s, str)

    @staticmethod
    def _url_quote(url: Any) -> str:
        return urllib.parse.quote(Session._safe_dumps(url))

    @staticmethod
    def _json_serial(obj: Any) -> str:
        """JSON serializer for *obj not serializable by default json code."""
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def _base64_encode(s: str) -> str:
        """Produce a BASE64 encoded string."""
        return (base64.b64encode(s.encode("utf-8"))).decode("ascii")


class AccsynException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
