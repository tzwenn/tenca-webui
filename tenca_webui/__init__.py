import urllib.error
import os

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from markupsafe import escape

import tenca.connection
import tenca.settings
import tenca.exceptions


def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='development',
		BRAND_CAPTION='Tenca',
	)

	if test_config is None:
		app.config.from_pyfile('config.py', silent=False)
	else:
		app.config.from_mapping(test_config)

	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	################################################################################

	from . import db
	db.init_db(app)

	from .auth import oidc
	oidc.init_app(app)

	conn = tenca.connection.Connection() # db.SQLCachedDescriptionStorage)

	@app.before_request
	def before_request():
		g.oidc = oidc
		g.conn = conn

	@app.errorhandler(404)
	def page_not_found(e):
		return render_template('404.html'), 404

	################################################################################

	@app.route('/')
	def index():
		if oidc.user_loggedin:
			return redirect(url_for('dashboard.index'))
		else:
			return render_template('index.html')

	from . import action
	app.register_blueprint(action.bp)

	from . import dashboard
	app.register_blueprint(dashboard.bp)

	from . import manage_list
	app.register_blueprint(manage_list.bp)

	@app.route('/login/')
	@oidc.require_login
	def login():
		return redirect(url_for('dashboard.index'))

	@app.route('/logout/')
	def logout():
		oidc.logout()
		return redirect(url_for('index'))

	from . import change_membership
	app.register_blueprint(change_membership.bp)

	@app.route('/<hash_id>/<legacy_admin_url>/')
	@oidc.require_login
	def legacy_manage_list(hash_id, legacy_admin_url):
		if not manage_list.legacy_admin_url_valid(hash_id, legacy_admin_url):
			abort(404)

		mailing_list = change_membership.find_mailing_list(hash_id) # Becomes escaped
		current_user_mail = oidc.user_getfield('email')
		if mailing_list.is_member(current_user_mail):
			if not mailing_list.is_owner(current_user_mail):
				mailing_list.promote_to_owner(current_user_mail)
		else:
			session[manage_list.LEGACY_MANAGE_LIST_COOKIE_NAME] = '{}/{}'.format(hash_id, legacy_admin_url)

		return redirect(url_for('manage_list.index', list_id=mailing_list.list_id))

	return app
