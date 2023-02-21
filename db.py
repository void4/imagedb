import os
import json
import uuid
from glob import glob
from collections import Counter
from copy import deepcopy

import dataset
from flask import g

from app import *
from utils import *

"""
If it doesn't exist yet, Dataset will create a new file, database.db in this directory
Together with the database.db-shm and database.db-wal files
which are created on reads and writes (do not delete these!), it makes up the database
Open database.db with DB Browser for SQLite to inspect its contents
You can copy these three files somewhere to make a backup of your database
"""

DATABASE = "sqlite:///database.db?check_same_thread=False"

def loads(s):
	return json.loads(s)

def dumps(j):
	return json.dumps(j)

def get_table():
	"""can be called by any function to get access to the database table called 'metadata'"""

	db = getattr(g, "_database", None)

	if db is None:
		db = g._database = dataset.connect(DATABASE)

	return db["metadata"]

def save_metadata(path, title="", description="", tags=None):
	"""creates a new row in the database. dataset will insert columns automatically if they don't exist yet
	the same goes for the table and the database file"""

	if tags is None:
		tags = []

	table = get_table()

	row = {
		"path": path,
		"sha256sum": sha256sum(path),
		"title": title,
		"description": description,
		"tags": dumps(tags),
		"created": time(),
		"updated": time()
	}

	table.insert(row)

def load_metadata(path):
	"""will return None if no row with that input"""

	table = get_table()

	result = table.find_one(path=path)

	if result is None:
		return None

	result["tags"] = loads(result["tags"])

	return result

def update_metadata(metadata):
	table = get_table()

	metadata = deepcopy(metadata)

	metadata["tags"] = dumps(metadata["tags"])

	metadata["updated"] = time()

	table.update(metadata, ["id"])

def update_db():
	print("Updating database index...")
	paths = glob("static/files/**/*", recursive=True)

	table = get_table()

	checked_paths = {}

	for path in paths:
		if not os.path.isfile(path):
			continue

		#print(os.path.dirname(path), os.path.basename(path))
		checksum = sha256sum(path)
		samechecksum = table.find_one(sha256sum=checksum)
		if samechecksum is None:
			save_metadata(path)
		else:
			if samechecksum["path"] != path:
				if os.path.exists(samechecksum["path"]):
					print("Found duplicate file with same content at", samechecksum["path"])
				else:
					print("File purportedly moved from", samechecksum["path"], ", updating path")
					samechecksum["path"] = path
					table.update(samechecksum, ["id"])

		checked_paths[path] = True

	for file in table.all():
		if file["path"] not in checked_paths:
			print("Warning: Not found in filesystem:", file["path"])

	print("Updated database index.")

def none2list(user, key):
	v = user.get(key)
	return loads(v) if v is not None else []

def search_all_tags(positive=None, negative=None, allownsfw=False):

	if positive is None:
		positive = []

	if negative is None:
		negative = []


	# TODO: if none, no results on default page?

	tagcounter = Counter()
	results = []
	metas = get_table()
	for meta in metas.all():

		tags = none2list(meta, "tags")

		if len(positive) == 0 or all([tag in tags for tag in positive]):
			if len(negative) == 0 or not any([tag in tags for tag in negative]):
				tagcounter.update(tags)

				results.append(meta)

	results = results[::-1]

	mostcommon = tagcounter.most_common()

	return mostcommon, results


"""
Utility to execute requests interactively with context

$ python
>>> from db import *
>>> code = wc(save_json, {'test': 123})
>>> code
'516a1030-eeec-43a4-b247-c5cf81690c91'
>>> wc(load_json, code)
{'test': 123}
"""
def wc(f, *args, **kwargs):
    with app.app_context():
        return f(*args, **kwargs)
