import urllib.error
import os

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for
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

	conn = tenca.connection.Connection() #db.SQLHashStorage)

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

	@app.route('/<hash_id>/<legacy_admin_token>/')
	@oidc.require_login
	def legacy_manage_list(hash_id, legacy_admin_token):
		mailing_list = change_membership.find_mailing_list(hash_id)

		# If owner: Forward
		# If member: Promote & Forward
		# If not member: Request to join first
		return 'Forwarding to the management form of "%s", if "%s" is the correct token.' % (mailing_list.fqdn_listname, escape(legacy_admin_token))

	return app
