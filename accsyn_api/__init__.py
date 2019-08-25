'''
AccSyn fast filmdelivery and pipeline sync Python API

Talks CRUD REST over HTTPS 443 with AccSyn cloud server.

'''

import sys

if (sys.version_info > (3, 0)):
	# Python 3 code in this block
	from .session import Session
else:
	# Python 2 code in this block
	from .session_py2 import Session


__version__ = Session.__version__

