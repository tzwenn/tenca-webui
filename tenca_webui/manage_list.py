from flask import Markup, escape, flash, g, render_template, request, url_for

def index(list_id):
	mailing_list = g.conn.get_list(escape(list_id))
	if mailing_list is None or not mailing_list.is_owner(g.oidc.user_getfield('email')):
		abort(404)

	return render_template('manage_list.html', mailing_list=mailing_list)
