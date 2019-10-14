import sys, os, logging, traceback, time, datetime, subprocess, socket, json, uuid, hashlib, copy, unicodedata, _thread, urllib.request, urllib.parse, urllib.error, base64, io, gzip, binascii
import requests

try:
	requests.packages.urllib3.disable_warnings()
except:
	print(traceback.format_exc(), file=sys.stderr)

logging.basicConfig(format="(%(thread)d@%(asctime)-15s) %(message)s", level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

ACCSYN_CLOUD_DOMAIN="accsyn.com"
ACCSYN_CLOUD_REGISTRY_HOSTNAME="registry.%s"%ACCSYN_CLOUD_DOMAIN
ACCSYN_PORT=443
DEFAULT_EVENT_PAYLOAD_COMPRESS_SIZE_TRESHOLD=100*1024;  # Compress event data payloads above 100k

CLEARANCE_CLOUDADMIN="cloudadmin"
CLEARANCE_ADMIN="admin"
CLEARANCE_EMPLOYEE="employee"
CLEARANCE_CLIENT="client"
CLEARANCE_NONE="none"

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.date) or isinstance(obj, datetime.datetime):
			return "{USD::date}%s"%obj.strftime("%Y%m%d %H:%M:%S")
		else:
			try:
				from bson.objectid import ObjectId

				if isinstance(obj, ObjectId):
					return str(obj)
			except:
				pass
		return super(JSONEncoder, self).default(obj)

class JSONDecoder(json.JSONDecoder):
	def decode(self, json_string):
		json_data = json.loads(json_string)
		def recursive_decode(d):
			if isinstance(d, dict):
				for key in list(d.keys()):
					if isinstance(d[key], dict):
						d[key] = recursive_decode(d[key])	
					elif isinstance(d[key], list):
						newlist = []
						for i in d[key]:
							newlist.append(recursive_decode(i))
						d[key] = newlist
					elif isinstance(d[key], str) or isinstance(d[key], str):
						if key == "_id":
							from bson.objectid import ObjectId
							d[key] = ObjectId(d[key])
						elif str(Session.safely_printable(d[key])).find("{USD::date}")>-1:
							s = d[key][d[key].find("}")+1:]
							d[key] = datetime.datetime.strptime(s,"%Y%m%d %H:%M:%S" if s.find("+")==-1 else "%Y%m%d+%H:%M:%S")
			return d
		return recursive_decode(json_data)

class Session(object):

	__version__ = "1.2.2-6"

	def __init__(self, domain=None, username=None, api_key=None, pwd=None, hostname=None, port=None, proxy=None, verbose=False, dev=False):
		''' Setup; store credentials, authenticate, get a session key '''
		# Generate a session ID
		self._session_id = str(uuid.uuid4())
		self._session_key = None # Have no session ID yet
		self._verbose = verbose
		self._proxy = proxy
		self._dev = dev
		self._clearance = CLEARANCE_NONE
		self.verbose("Creating AccSyn Python API session (v%s)"%Session.__version__)
		# Migrate
		# Migrate
		for key in os.environ:
			if key.startswith("FILMHUB_"):
				Session.warning("Found old FilmHUB product environment variable '%s', please migrate!"%key)
		if domain is None:
			assert ('ACCSYN_DOMAIN' in os.environ or 'ACCSYN_ORG' in os.environ or 'FILMUB_DOMAIN' in os.environ or 'FILMHUB_ORG' in os.environ),("Please supply your AccSyn domain/organization or set ACCSYN_DOMAIN environment!")
		self._domain = domain or (os.environ['ACCSYN_DOMAIN'] if 'ACCSYN_DOMAIN' in os.environ else os.environ.get('ACCSYN_ORG', os.environ.get('FILMHUB_DOMAIN', os.environ.get('FILMHUB_ORG'))))
		if username is None:
			assert ('ACCSYN_API_USER' in os.environ or 'FILMHUB_API_USER' in os.environ),("Please supply your AccSyn user name (E-mail) or set ACCSYN_API_USER environment!")
		self._username = username or os.environ.get('ACCSYN_API_USER') or os.environ['FILMHUB_API_USER']
		if api_key:
			self._api_key = api_key
		else:
			self._api_key = os.environ.get('ACCSYN_API_KEY') or os.environ.get('FILMHUB_API_KEY')
		if len(self._api_key or "") == 0:
			if 0<len(pwd or ""):
				# Store it temporarily
				self._pwd = pwd
			else:
				raise Exception("Please supply your AccSyn API KEY or set ACCSYN_API_KEY environment!")
		self._hostname = hostname
		self._port = port or ACCSYN_PORT
		if self._hostname is None:
			if self._dev:
				self._hostname = "172.16.178.161"
			else:
				# Get domain
				result = self.rest("PUT", ACCSYN_CLOUD_REGISTRY_HOSTNAME, "registry/organization/domain", {'organization':self._domain})
				# Store hostname
				assert ('domain' in result),("No domain were provided for us!")
				self._hostname = "%s.%s"%(result['domain'], ACCSYN_CLOUD_DOMAIN) 
		self._last_message = None
		self.login()

	@staticmethod
	def get_hostname():
		return socket.gethostname()

	@staticmethod
	def info(s, standout=False):
		if standout:
			logging.info("-"*80)
		logging.info(s)
		if standout:
			logging.info("-"*80)

	@staticmethod
	def warning(s, standout=True):
		if standout:
			logging.warning("-"*80)
		logging.warning(s)
		if standout:
			logging.warning("-"*80)

	def verbose(self, s):
		if self._verbose:
			Session.info("[ACCSYN_API] %s"%(s))

	@staticmethod
	def safe_dumps(d, indent=None):
		return json.dumps(d, cls=JSONEncoder, indent=indent)

	@staticmethod
	def safely_printable(s):
		return ((s or "").encode()).decode("ascii", "ignore")
		#return unicodedata.normalize('NFKD', unicode(s)).encode('ascii', 'ignore')
		#if isinstance(s, str):
		#	try:
		#		u = str(s)
		#	except:
		#		u = str(s,'iso-8859-1')
		#elif isinstance(s, str):
		#	u = s
		#else:
		#	u = str(s)
		#return unicodedata.normalize('NFKD', u).encode('ascii', 'ignore')

	@staticmethod
	def json_serial(obj):
		"""JSON serializer for objects not serializable by default json code"""

		if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
			return obj.isoformat()
		raise TypeError ("Type %s not serializable" % type(obj))
	
	@staticmethod
	def str(d, indent=4):
		''' Return a string representation of a dict '''
		return json.dumps(d, default=Session.json_serial, indent=indent) if not d is None else ""

	@staticmethod
	def base64_encode(s):
		return (base64.b64encode((s).encode())).decode("utf-8", "ignore")

	def login(self, revive_session_key=None):
		# TODO: Load session key from safe disk storage/key chain?
		assert (self._session_key is None),("Already logged in!")
		d = {
			'session':self._session_id,
		}
		if revive_session_key:
			d['session_key_reuse'] = revive_session_key
		if self._api_key:
			headers = {
				"Authorization":"ASCredentials %s"%(Session.base64_encode('{"domain":"%s","username":"%s","api_key":"%s"}'%(self._domain, self._username, self._api_key)))  
			}
		else:
			headers = {
				"Authorization":"ASCredentials %s"%(Session.base64_encode('{"domain":"%s","username":"%s","pwd":"%s"}'%(self._domain, self._username, Session.base64_encode(self._pwd))))
			}
			self._pwd = None # Forget this now
		result = self.rest("PUT", self._hostname, "/user/login/auth", d, headers=headers, port=self._port)
		# Store session key
		assert ('session_key' in result),("No session key were provided for us!")
		self._session_key = result['session_key']
		self._clearance = result['clearance'] or CLEARANCE_NONE
		self._uid = result['id']
		return True

	def get_last_message(self):
		return self._last_message

	@staticmethod
	def obscure_dict_string(s):
		if s is None:
			return s
		for key in ['pwd','_key','token']:
			last_pos = 0
			while True:
				new_pos = s.find(key, last_pos)
				if new_pos == -1:
					break
				else:
					idx_start = s.find('"',new_pos+len(key)+1)
					idx_end = s.find('"',idx_start+1)
					s = s[:idx_start+1]+"*"+s[idx_end:]
					last_pos = idx_start
		return s

	# REST get

	def event(self, method, uri, data, query=None, entityid=None, timeout=None, ssl=True, quiet=False):
		''' Generate an Event and send using REST to AccSyn cloud '''
		assert (self._session_key),("Please login before attempting to post event!")
		event = {
			'audience':"api",
			'domain':self._domain,
			'eid':str(uuid.uuid4()),
			'session':self._session_id,
			'uri':uri,
			'ident':self._username,
			'created':datetime.datetime.now(),
			'hostname':Session.get_hostname()
		}
		did_compress_payload = False
		if not data is None and 0<len(data):
			# Check if should compress payload
			def recursive_estimate_dict_size(o):
				result = 0
				if not o is None:
					if isinstance(o, dict):
						d = o
						for key in d:
							result += len(key) + recursive_estimate_dict_size(d[key])
					elif isinstance(o, list):
						l = o
						for _o in l:
							result += recursive_estimate_dict_size(_o)
					elif isinstance(o, str) or isinstance(o, str):
						result += len(o)
					else:
						result += 10
				return result

			size = recursive_estimate_dict_size(data)
			if (DEFAULT_EVENT_PAYLOAD_COMPRESS_SIZE_TRESHOLD<size):
				out = io.StringIO()
				with gzip.GzipFile(fileobj=out, mode="w") as f:
				  f.write(Session.safe_dumps(data))
				b = out.getvalue()
				event['gz_data'] = binascii.b2a_base64(b)
				self.verbose("Compressed event payload %d>%d(%s%%)"%(size, len(event['gz_data']), (100*len(event['gz_data'])/size)))
				did_compress_payload = True
		if not did_compress_payload:
			event['data'] = data

		if query:
			event['query'] = query
		if entityid:
			event['id'] = entityid
		retval = self.rest(method, hostname=self._hostname, uri="/event", data=event, timeout=timeout, ssl=ssl, port=self._port, quiet=quiet)
		return retval

	def rest(self, method, hostname, uri, data, timeout=None, ssl=True, port=None, quiet=False, headers=None):
		''' Talk REST with FIlmHUB Cloud '''
		if port is None:
			port = self._port or ACCSYN_PORT
		if hostname is None:
			hostname = "%s.%s"%(self._domain, ACCSYN_DOMAIN)
		# Proxy set?
		proxy = self._proxy or os.environ.get('ACCSYN_PROXY')
		if 0<len(proxy or ""):
			if 0<proxy.find(":"):
				parts = proxy.split(":")
				hostname = parts[0]
				port = int(parts[1])
			else:
				hostname = proxy
				port = 80
			ssl = False
		elif self._dev and (uri or "").find("registry") != 0:
			ssl = False
			port = 80
		url = "http%s://%s:%d/api/v1.0%s"%("s" if ssl else "", hostname, port,("/" if not uri.startswith("/") else "")+uri)
		if timeout is None:
			timeout = 999999
		if data is None:
			data = {}
		#data = json.dumps({'name':'test', 'description':'some test repo'}) 
		#r = requests.post(github_url, data, auth=('user', '*****'))
		CONNECT_TO, READ_TO = (10, 2*60)  # Wait 10s to reach machine, 2min for it to send back data
		r = None
		#data = AccSyn.prepare_rest_serialize(data)
		initial_timeout = timeout
		if headers is None:
			if uri.find("registry/")!=0:
				assert (not self._session_key is None),("Need to be authenticated when communicating with AccSyn!")
				headers = {'Authorization':"ASSession %s"%(Session.base64_encode('{"domain":"%s","username":"%s","session_key":"%s"}'%(self._domain, self._username, self._session_key)))}
			else:
				headers = {}
		headers['ASDevice'] = "PythonAPI v%s @ %s %s(%s)"%(Session.__version__, sys.platform, Session.get_hostname(), os.name)
		for iteration in range(0,2):
			t_start = int(round(time.time() * 1000))
			try:
				self.verbose("REST %s %s, data: %s"%(method, url, data))
				if method.lower() == "get":
					r = requests.get(url, params = urllib.parse.quote(Session.safe_dumps(data)), timeout=(CONNECT_TO, READ_TO), verify=False, headers=headers)
				elif method.lower() == "put":
					r = requests.put(url, Session.safe_dumps(data), timeout=(CONNECT_TO, READ_TO), verify=False, headers=headers)
				elif method.lower() == "post":
					r = requests.post(url, Session.safe_dumps(data), timeout=(CONNECT_TO, READ_TO), verify=False, headers=headers)
				elif method.lower() == "delete":
					r = requests.delete(url, params = urllib.parse.quote(Session.safe_dumps(data)), timeout=(CONNECT_TO, READ_TO), verify=False, headers=headers)
				t_end = int(round(time.time() * 1000))
				#break
			except:
				sleep_time = 2
				t_end = int(round(time.time() * 1000))
				timeout -= int((t_end-t_start)/1000)
				timeout -= sleep_time
				if timeout<=0 or True:
					raise Exception("Could not reach %s:%d! Make sure cloud server(%s) can be reached from you location and no firewall is blocking outgoing traffic at port %s. Details: %s"%(hostname, port, port ,hostname,traceback.format_exc() if not quiet else "(quiet)"))
					
				Session.warning("Could not reach %s:%d! Waited %ds/%s, will try again in %ds... Details: %s"%(hostname, port, initial_timeout-timeout, "%ss"%initial_timeout if initial_timeout<99999999 else "INF", sleep_time, traceback.format_exc()))
				time.sleep(sleep_time)

			try:
				#retval = AccSyn.prepare_rest_deserialize(r.json())
				retval = json.loads(r.text, cls=JSONDecoder)
				if not quiet:
					self.verbose("%s/%s REST %s result of %s: %s (~%sms)"%(
						hostname, 
						uri, 
						method, 
						Session.obscure_dict_string(Session.safely_printable(str(data)).replace("'",'"')), 
						Session.obscure_dict_string(Session.safely_printable(str(retval)).replace("'",'"')), 
						t_start-t_end+1))
				do_retry = False
				if not retval.get('message') is None:
					# Some thing went wrong
					if retval.get('session_expired') is True:
						if not self._api_key is None: 
							# We should be able to get a new session and retry
							revive_session_key = self._session_key 
							self._session_key = None
							self.login(revive_session_key=revive_session_key)
							self.info("Authenticated using API KEY and reused expired session...")
							do_retry = True
					if not do_retry:
						self._last_message = retval['message']
				if not do_retry:
					break
			except:
				print(traceback.format_exc(), file=sys.stderr)
				message = "The %s:%d/%s REST %s %s operation failed! Details: %s %s"%(hostname, port, uri, method, Session.obscure_dict_string(Session.safely_printable(str(data)).replace("'",'"')), r.text, traceback.format_exc())
				Session.warning(message)
				raise Exception(message)
		if 'exception' in retval:
			message = "%s caused an exception! Please contact %s admin for more further support."%(uri, self._domain)
			Session.warning(message)
			if self._clearance in [CLEARANCE_ADMIN, CLEARANCE_CLOUDADMIN]:
				Session.warning(retval['exception'])
			raise Exception(message)
		elif 'message' in retval:
			message_effective = retval.get('message_hr') or retval['message'] 
			Session.warning(message_effective)
			raise Exception(message_effective)
		return retval

	def decode_query(self, query):
		# Scenarios:
		#   entities
		#   attributes WHERE entitytype="job"
		#   Job WHERE code="my_transfer"
		#   Job WHERE (dest="lars@edit.com" OR ..)

		# First replace tabs with spaces, remove double spaces
		s = ""
		is_escaped = False
		is_at_whitespace = False
		query = (query or "").replace("\t"," ").replace("\n","").strip()
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
						if idx_part_start<idx:
							# Add this part
							parts.append(query[idx_part_start:idx])
							idx_part_start = idx + 1
			else:
				is_at_whitespace = False
				if query[idx] == '"' and is_escaped:
					is_at_whitespace = False
				elif query[idx] == "(":
					if not is_escaped:
						paranthesis_depth += 1
				elif query[idx] == ")":
					if not is_escaped:
						paranthesis_depth -= 1
			if do_append:
				s += query[idx]
		if idx_part_start<len(query):
			parts.append(query[idx_part_start:])
		self.verbose("Query: '%s', parts: '%s'"%(query, parts))
		# ['Job', 'WHERE', '(dest="lars@edit.com" OR id=...)]
		assert (len(parts) in [1,3]),("Query has invalid syntax; statements supported can either be single ('entities') or with a WHERE statement ('job WHERE id=..')")
		if len(parts) == 1:
			if parts[0].lower() == "user":
				return {'entitytype':parts[0].lower(),'expression':"code=%s"%self._username}
			else:
				return {'entitytype':parts[0].lower()}
		else:
			assert (parts[1].strip().lower() == "where"),("Invalid query '%s', should be on the form '<entitytype> where <expression>'.")
			# Decode expression
			return {'entitytype':parts[0].lower(),'expression':parts[2].lower()}

	@staticmethod
	def get_base_uri(entitytype):
		uri_base = entitytype
		# Send query to server, first determine uri
		#if entitytype == "share":
		#	uri_base = "organization/share"
		if entitytype == "site":
			uri_base = "organization/site"
		elif entitytype == "queue":
			uri_base = "job"
		elif entitytype == "task":
			uri_base = "job/task"
		return uri_base

	# Create

	def create(self, entitytype, data, entitytype_id=None):
		''' Create an entity '''
		assert (0<len((entitytype or "").strip())),("You must provide the entity type!")		
		if isinstance(data, str) or isinstance(data, str):
			assert (0<len((data or "").strip())),("You must provide the data to create!")
			# Is it JSON as a string or JSON in a file pointed to?
			try:
				data = json.loads(data)
			except:
				# Not JSON string, maybe a path?
				if os.path.exists(data):
					data = json.load(open(data, "r"))
				else:
					raise Exception("Cannot build JSON payload data, not a valid JSON string or path to a JSON file!")
		else:
			assert (not data is None and 0<len(data)),("Empty create data submitted!")

		d = self.event("POST", "%s/create"%Session.get_base_uri(entitytype), data, query=entitytype_id)
		if d:
			if 'result' in d:
				return d['result'][0]
			else:
				return d

	# Query

	def find(self, query, attributes=None, archived=False, limit=None, skip=None):
		''' Return a list of something '''
		assert (0<len(query or "") and (isinstance(query, str) or isinstance(query, str))),("Invalid query type supplied, must be of string type!")
		retval = None
		d = self.decode_query(query)
		data = {}
		if d['entitytype'] == "entitytypes":
			# Ask cloud server, the Python API is rarely updated and should not need to know
			d = self.event("GET", "entitytypes", {})
			if d:
				retval = d['result']
		elif d['entitytype'] == "attributes":
			assert (d.get('expression')),("Please query which entity to obtain attributes for (i.e. 'attributes WHERE entitytype=job')")
			# Look at expression
			parts = d['expression'].split("=")
			assert (len(parts)==2 and parts[0].strip() == "entitytype"),("Please query attributes by expressions on the form 'attributes WHERE entitytype=job'")
			entitytype = parts[1].strip().replace("'","").replace('"',"")
			d = self.event("GET", "attributes", {'entitytype':entitytype})
			if d:
				retval = d['result']
		else:
			# Send query to server, first determine uri
			uri_base = Session.get_base_uri(d['entitytype'])
			if d['entitytype'] == "queue":
				data = {'type':2}
			elif d['entitytype'] == "job":
				data = {'type':1}
			if archived:
				data['archive']=True
			if limit:
				data['limit'] = limit
			if skip:
				data['skip'] = skip
			if attributes:
				data['attributes'] = attributes
			d = self.event("GET", "%s/find"%uri_base, data, query = d.get('expression'))
			if d:
				retval = d['result']
		return retval

	def find_one(self, query, attributes=None):
		''' Return a list of something '''
		assert (0<len(query or "") and (isinstance(query, str) or isinstance(query, str))),("Invalid query type supplied, must be of string type!")
		result = self.find(query, attributes=attributes)
		if result and 0<len(result):
			retval = result[0]
			return retval
		return None

	def report(self, query):
		''' Return a list of something '''
		d = self.decode_query(query)
		# Send query to server, first determine uri
		uri_base = Session.get_base_uri(d['entitytype'])
		data = {}
		d = self.event("GET", "%s/report"%uri_base, data, query = d.get('expression'))
		return d['report']

	# Update an entity

	def update_one(self, entitytype, entityid, data):
		''' Update an entity '''
		assert (0<len(entitytype or "") and (isinstance(entitytype, str) or isinstance(entitytype, str))),("Invalid entity type supplied, must be of string type!")
		assert (0<len(entityid or "") and (isinstance(entityid, str) or isinstance(entityid, str))),("Invalid entity ID supplied, must be of string type!")
		assert (0<len(data or {}) and isinstance(data, dict)),("Invalid data supplied, must be dict and have content!")
		d = self.event("PUT", "%s/edit"%Session.get_base_uri(entitytype), data, entityid=entityid)
		if d:
			return d['result']

	# Delete an entity

	def delete_one(self, entitytype, entityid):
		''' Update an entity '''
		assert (0<len(entitytype or "") and (isinstance(entitytype, str) or isinstance(entitytype, str))),("Invalid entity type supplied, must be of string type!")
		assert (0<len(entityid or "") and (isinstance(entityid, str) or isinstance(entityid, str))),("Invalid entity ID supplied, must be of string type!")
		d = self.event("DELETE", "%s/delete"%Session.get_base_uri(entitytype), {}, entityid=entityid)
		if d:
			return d['result'][0]

	# File operations
	def ls(self, p, recursive=False, maxdepth=None, files_only=False, directories_only=False):
		assert (0<len(p or "") and (isinstance(p, str) or isinstance(p, str) or isinstance(p, dict) or isinstance(p, list))),("No path supplied, or not a string/list!")
		data = {
			'op':"ls",
			'path':p,
			'download':True,
			'recursive':recursive
		}
		if maxdepth:
			data['maxdepth'] = maxdepth
		if directories_only:
			data['directories_only'] = directories_only
		if files_only:
			data['files_only'] = files_only
		d = self.event("GET", "organization/file", data)
		if d:
			return d['result']

	def getsize(self, p):
		assert (0<len(p or "") and (isinstance(p, str) or isinstance(p, str) or isinstance(p, dict) or isinstance(p, list))),("No path supplied, or not a string/list!")
		data = {
			'op':"getsize",
			'path':p,
		}
		d = self.event("GET", "organization/file", data)
		if d:
			return d['result']

	def exists(self, p):
		assert (0<len(p or "") and (isinstance(p, str) or isinstance(p, str) or isinstance(p, dict) or isinstance(p, list))),("No path supplied, or not a string/list!")
		data = {
			'op':"exists",
			'path':p,
		}
		d = self.event("GET", "organization/file", data)
		if d:
			return d['result']

	# Misc
	def get_api_key(self):
		return self.event("GET", "user/api_key", {})['api_key']

	def gui_is_running(self):
		result = self.event("GET", "client/find", {}, query="user={0} AND code={1} AND type={2}".format(self._uid, Session.get_hostname(), 0))['result']
		retval = None
		if 0<len(result):
			for c in result:
				retval = c['status'] in ["online","disabled"]
				if retval is True:
					break
		return retval

	def server_is_running(self):
		result = self.event("GET", "client/find", {}, query="user={0} AND code={1} AND type!={2}".format(self._uid, Session.get_hostname(), 0))['result']
		retval = None
		if 0<len(result):
			for c in result:
				retval = c['status'] in ["online","disabled"]
				if retval is True:
					break
		return retval

	# Help
	def help(self):
		print("Please have a look at the Python API reference: https://sites.google.com/accsyn.com/python-api")




