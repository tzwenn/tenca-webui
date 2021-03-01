from flask import Blueprint, Markup, abort, escape, flash, g, redirect, render_template, request, url_for

import functools

from ._macros import css_codify
from .auth import oidc

bp = Blueprint('manage_list', __name__, url_prefix='/manage')

def lookup_list_id(view):
	@functools.wraps(view)
	def wrapped_view(list_id, **kwargs):
		mailing_list = g.conn.get_list(escape(list_id))
		if mailing_list is None or not mailing_list.is_owner(oidc.user_getfield('email')):
			abort(404)
		return view(list_id, mailing_list=mailing_list, **kwargs)
	return wrapped_view


@bp.route('/<list_id>/')
@oidc.require_login
@lookup_list_id
def index(list_id, mailing_list):
	list_bool_options = [
		('notsubscribed_allowed_to_post', 'Not subscribed users are allowed to post.', mailing_list.notsubscribed_allowed_to_post),
		('replies_addressed_to_list', 'Replies are addressed to the list per default.', True),
	]

	return render_template('manage_list.html', mailing_list=mailing_list, list_bool_options=list_bool_options)

@bp.route('/<list_id>/delete/', methods=('POST', ))
@oidc.require_login
@lookup_list_id
def delete(list_id, mailing_list):
	print(request.method, request.form)
	if request.method == "POST" and "delete_submit" in request.form and "confirmation_phrase" in request.form:
		confirmation_phrase = escape(request.form["confirmation_phrase"])
		if confirmation_phrase != (mailing_list.fqdn_listname).upper():
			flash("Wrong confirmation phrase. Try again.", category="danger")
		else:
			try:
				g.conn.delete_list(mailing_list.fqdn_listname)
			except Exception as e:
				flash(Markup("Cannot delete: {}".format(css_codify(str(e)))))
			else:
				flash(Markup("Deleted {}.".format(css_codify(mailing_list.fqdn_listname))), category="success")
				return redirect(url_for('dashboard.index'))
		return redirect(url_for('.index', list_id=list_id))
	else:
		abort(400)