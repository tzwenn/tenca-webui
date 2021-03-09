from flask import current_app, g
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy

from tenca.hash_storage import HashStorage, MailmanDescriptionHashStorage, NotInStorageError, TwoLevelHashStorage

db = SQLAlchemy()

def init_db(app):
	db.init_app(app)
	db.create_all(app=app)


class HashEntry(db.Model):
	hash_id = db.Column(db.String(80), primary_key=True, nullable=False)
	list_id = db.Column(db.String(128), nullable=False)

	def __repr__(self):
		return '<HashEntry %r->%r>' % (self.hash_id, self.list_id)
		

class LegacyAdminURL(db.Model):
	hash_id = db.Column(db.String(80), primary_key=True, nullable=False)
	admin_url = db.Column(db.String(32), nullable=False)

	def __repr__(self):
		return '<LegacyAdminURL %r/%r>' % (self.hash_id, self.admin_url)

class SQLHashStorage(HashStorage):

	def _entry_for(self, hash_id):
		return HashEntry.query.get(hash_id)

	def __contains__(self, hash_id):
		return self._entry_for(hash_id) is not None

	def get_list_id(self, hash_id):
		entry = self._entry_for(hash_id)
		if entry is None:
			raise NotInStorageError()
		return entry.list_id

	def store_list_id(self, hash_id, list_id):
		entry = HashEntry(hash_id=hash_id, list_id=list_id)
		db.session.add(entry)
		db.session.commit()

	def get_hash_id(self, list_id):
		entry = HashEntry.query.filter_by(list_id=list_id).first()
		if entry is None:
			raise NotInStorageError()
		return entry.hash_id

	def delete_hash_id(self, hash_id):
		entry = self._entry_for(hash_id)
		if entry is not None:
			db.session.delete(entry)
			db.session.commit()

	def hashes(self):
		return (e.hash_id for e in HashEntry.query.all())

class SQLCachedDescriptionStorage(TwoLevelHashStorage):

	l1_class = SQLHashStorage
	l2_class = MailmanDescriptionHashStorage