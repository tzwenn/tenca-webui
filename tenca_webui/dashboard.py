from flask import Blueprint, Markup, flash, g, redirect, render_template, request, url_for

from ._macros import css_codify
from .auth import oidc

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard/', methods=('GET', 'POST'))
@oidc.require_login
def index():
	if request.method == 'POST':
		try:
			new_list = g.conn.add_list(request.form['listname'], oidc.user_getfield('email'))
		except Exception as e:
			flash(Markup('An error occurred: {}'.format(e)), category='danger')
		else:
			flash(Markup('Successfully created {}.'.format(css_codify(new_list.fqdn_listname))),
				category='success')
			return redirect(url_for('manage_list.index', list_id=new_list.list_id))


	email = oidc.user_getfield('email')
	memberships = g.conn.get_owner_and_memberships(email)

	return render_template('dashboard.html', memberships=memberships)
