from flask import Blueprint, Markup, abort, escape, flash, g, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import Form, StringField
from wtforms.validators import DataRequired

import functools
import json

from ._macros import css_codify
from .auth import is_current_user, oidc
from . import db

bp = Blueprint('manage_list', __name__, url_prefix='/manage')

LEGACY_MANAGE_LIST_COOKIE_NAME = 'tenca_legacy_manage_list'

def legacy_admin_url_valid(hash_id, legacy_admin_url):
	entry = db.LegacyAdminURL.query.filter_by(hash_id=escape(hash_id)).first()
	return entry is not None and entry.admin_url == escape(legacy_admin_url)

def lookup_list_id(view):
	@functools.wraps(view)
	def wrapped_view(list_id, **kwargs):
		mailing_list = g.conn.get_list(escape(list_id))
		if mailing_list is None:
			abort(404)

		if LEGACY_MANAGE_LIST_COOKIE_NAME in session:
			hash_id, _, legacy_admin_url = session[LEGACY_MANAGE_LIST_COOKIE_NAME].partition('/')
			is_legacy_valid = mailing_list.hash_id == hash_id and legacy_admin_url_valid(hash_id, legacy_admin_url)
		else:
			is_legacy_valid = False

		if not (is_legacy_valid or mailing_list.is_owner(oidc.user_getfield('email'))):
			abort(404)
		return view(list_id, mailing_list=mailing_list, **kwargs)
	return wrapped_view

def edit_member(mailing_list):
	member_address = request.form.get('member_address')
	if not member_address:
		return True

	operations = [
		('remove_member', mailing_list.remove_member_silently, 'Removed {}'),
		('promote_member', mailing_list.promote_to_owner, 'Promoted {}'),
		('demote_member', mailing_list.demote_from_owner, 'Demoted {}'),
	]

	had_error = False
	for (name, func, success_string) in operations:
		if name in request.form:
			try:
				func(member_address)
			except Exception as e:
				flash(Markup('An Error occurred: {}'.format(escape(str(e)))), category='danger')
				had_error = True
			else:
				flash(Markup(success_string.format(css_codify(member_address))), category='success')

	if not had_error and is_current_user(member_address) and any(x in request.form for x in ['remove_member', 'demote_member']):
		# If you demote yourself, you cannot access the admin page anymore
		return redirect(url_for('dashboard.index'))
	
	return None


list_bool_options = {
	'notsubscribed_allowed_to_post': 'Not subscribed users are allowed to post.',
	'replies_addressed_to_list': 'Replies are addressed to the list per default.'
}

class DeleteListForm(FlaskForm):
	confirmation_phrase = StringField('Confirmation Phrase', [DataRequired()])

@bp.route('/<list_id>/', methods=('POST', 'GET'))
@oidc.require_login
@lookup_list_id
def index(list_id, mailing_list):
	delete_list_form = DeleteListForm(request.form)
	if request.method == 'POST':
		target = edit_member(mailing_list)
		if target is not None:
			return target

	lbo = [(name, description, getattr(mailing_list, name)) for name, description in list_bool_options.items()]

	return render_template('manage_list.html', mailing_list=mailing_list, list_bool_options=lbo, delete_list_form=delete_list_form)

@bp.route('/<list_id>/options/', methods=('POST', ))
@oidc.require_login
@lookup_list_id
def options(list_id, mailing_list):
	data = json.loads(request.data)
	try:
		name, value = data["name"], data["value"]
		if name not in list_bool_options or type(value) != bool:
			raise ValueError
		setattr(mailing_list, name, value)
	except:
		abort(400)
	else:
		return "OK"

@bp.route('/<list_id>/delete/', methods=('POST', ))
@oidc.require_login
@lookup_list_id
def delete(list_id, mailing_list):
	delete_list_form = DeleteListForm(request.form)

	if delete_list_form.validate():
		confirmation_phrase = delete_list_form.confirmation_phrase.data
		if confirmation_phrase != (mailing_list.fqdn_listname).upper():
			flash("Wrong confirmation phrase. Try again.", category="danger")
		else:
			try:
				g.conn.delete_list(mailing_list.fqdn_listname)
			except Exception as e:
				flash(Markup('Cannot delete: {}'.format(css_codify(str(e)))))
			else:
				flash(Markup('Deleted {}.'.format(css_codify(mailing_list.fqdn_listname))), category='success')
				return redirect(url_for('dashboard.index'))
		return redirect(url_for('.index', list_id=list_id))
	else:
		abort(400)
