from datetime import datetime
from futurelinks import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Stuff', backref='user', lazy="dynamic")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def getNets(self):
        return self.posts.filter(Stuff.type == "net").all()

    def getCsv(self):
        return self.posts.filter(Stuff.type == "csv").all()


class Stuff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    path = db.Column(db.Text, nullable=False,
                     default='futurelinks/uploadedNets/')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.type}', '{self.date_posted}', '{self.path}')"

    def getPath(self):
        return self.path + self.title
