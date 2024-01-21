from application import utils
from . import db
import os
import secrets
import cv2
import pytesseract
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, Flask
import numpy as np
from gtts import gTTS
from application import app
from application.forms import MyForm
from .models import User
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from easyocr import Reader
from werkzeug.utils import secure_filename


auth = Blueprint('auth', __name__)


@auth.route("/")
def home():
    return render_template('home.html')


@auth.route('/dictionary')
def dictionary():
    return render_template('dictionary.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)


@app.route('/upload', methods=["POST", "GET"])
def upload():
    if request.method == 'POST':
        sentence = ""
        f = request.files.get('file')
        _, extension = secure_filename(f.filename).rsplit(".", 1)

        generated_filename = secrets.token_hex(20) + f".{extension}"
        file_location = os.path.join(app.config["UPLOADED_PATH"], generated_filename)

        # Ensure the destination directory exists
        if not os.path.exists(app.config["UPLOADED_PATH"]):
            os.makedirs(app.config["UPLOADED_PATH"])

      
        print("File Location:", file_location)

        f.save(file_location)

        reader = Reader(['en'])  

        img = cv2.imread(file_location)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = reader.readtext(img)

        for detection in result:
            sentence += detection[1] + " "

        session['sentence'] = sentence
        os.remove(file_location)
        return redirect('/decoded/')
    else:
        return render_template("upload.html", user=current_user)
    

SUPPORTED_LANGUAGES = {'en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh', 'ru','af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'ny', 'zh-cn', 'zh-tw',
                        'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu', 'ht', 'ha', 'haw', 'iw', 'he', 'hi', 'hmn', 'hu', 'is', 'ig', 
                        'id', 'ga', 'it', 'ja', 'jw', 'kn', 'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mi', 'mr', 'mn', 'my', 'ne', 'no', 
                        'or', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd','sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tg', 'ta', 'te', 'th', 'tr', 
                        'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'}



@auth.route('/decoded', methods=['POST', 'GET'])
def decoded():
    sentence = session.get("sentence")
    form = MyForm()

    if request.method == "POST":
        text_data = form.text_field.data
        translate_to = form.language_field.data

        if translate_to not in SUPPORTED_LANGUAGES:
           
            translated_text = "Language not supported"
            translate_to = 'en'                                                                                                     # Setting a default language code
        else:
            translated_text = utils.translate_text(text_data, dest=translate_to)

        form.text_field.data = translated_text

        # generation of audio file
        generated_audio_filename = secrets.token_hex(10) + ".mp4"
        tts = gTTS(translated_text, lang=translate_to)
        file_location = os.path.join(app.config["AUDIO_FILE_UPLOAD"], generated_audio_filename)
        tts.save(file_location)

        return render_template("decoded.html", form=form, user=current_user, audio=True, file=generated_audio_filename)
    else:
        
        form.text_field.data = sentence
        session['sentence'] = ""
        return render_template("decoded.html", form=form, user=current_user, audio=False)


 


from werkzeug.security import generate_password_hash, check_password_hash

# ...

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        # Check if the old password matches the current user's password
        if check_password_hash(current_user.password, old_password):
            # Hash and update the password using 'sha256' method
            hashed_password = generate_password_hash(new_password, method='sha256')
            current_user.password = hashed_password
            db.session.commit()
            flash('Password changed successfully!', category='success')
            return redirect(url_for('auth.home'))
        else:
            flash('Incorrect old password. Please try again.', category='error')

    return render_template('change_password.html')
