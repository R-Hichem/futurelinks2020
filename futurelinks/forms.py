from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from futurelinks.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur',
                           validators=[DataRequired(), Length(min=5, max=20, message="Le nom d'utilisateur doit être entre 5 et 20 charactères")])
    email = StringField('Email',
                        validators=[DataRequired(), Email(message="Veillez saisir une adresse email valide !")])
    password = PasswordField('Mot de passe', validators=[
                             DataRequired(), Length(min=5, message="Le mot de passe doit contenir au moins 5  charactères")])
    confirm_password = PasswordField('Confirmez le mot de passe',
                                     validators=[DataRequired(), EqualTo('password', message="Le mot de passe ne corespond pas !")])
    submit = SubmitField('Inscription')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        # if user:
        #     raise ValidationError(
        #         'Ce nom d\'utilisateur existe déja. Veillez en choisir un autre')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Cette adresse mail existe déja. Veillez choisir une autre adresse mail')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Connexion')
