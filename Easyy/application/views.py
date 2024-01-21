from flask import Blueprint, render_template, request, flash, Flask, request, jsonify
from flask_login import login_required, current_user
from application.models import User
from .forms import VoiceSearchForm  

views = Blueprint('views', __name__)

@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    return render_template("home.html", user=current_user)

@views.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@views.route('/view-users')
@login_required
def view_users():
    users = User.query.all()
    return render_template('view_users.html', users=users)

@views.route('/voice', methods=['GET', 'POST'])
@login_required
def voice():
    form = VoiceSearchForm() 
    users = User.query.all()
    return render_template('voice.html', users=users, user=current_user, form=form)


@views.route('/')
# @login_required
def index():
    users = User.query.all()  
    return render_template('index.html', users=users, user=current_user) 