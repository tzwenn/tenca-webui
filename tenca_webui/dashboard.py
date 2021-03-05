from flask import Blueprint, Markup, flash, g, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import Form, StringField
from wtforms.validators import DataRequired

from ._macros import css_codify
from .auth import oidc

bp = Blueprint('dashboard', __name__)

class CreateNewListForm(FlaskForm):
	listname = StringField('Listname', [DataRequired()])

@bp.route('/dashboard/', methods=('GET', 'POST'))
@oidc.require_login
def index():
	form = CreateNewListForm(request.form)

	if request.method == 'POST' and form.validate():
		try:
			new_list = g.conn.add_list(form.listname.data, oidc.user_getfield('email'))
		except Exception as e:
			flash(Markup('An error occurred: {}'.format(e)), category='danger')
			form.listname.errors = ['']
		else:
			flash(Markup('Successfully created {}.'.format(css_codify(new_list.fqdn_listname))),
				category='success')
			return redirect(url_for('manage_list.index', list_id=new_list.list_id))


	email = oidc.user_getfield('email')
	memberships = g.conn.get_owner_and_memberships(email)

	return render_template('dashboard.html', form=form, memberships=memberships)
