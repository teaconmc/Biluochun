'''
Defines data model used by Biluochun.
'''

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
import flask_login
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import Identity

# Note
# With Flask-SQLAlchemy, __tablename__ is auto-filled with class name,
# converted from CamelCase to snake_case. You can still manually 
# supply one if you want to override.

db = SQLAlchemy()


class Team(db.Model):
    """
    A team describes a base unit of participation.
    """
    id = db.Column(db.Integer, Identity(start=1), primary_key=True)
    name = db.Column(db.Unicode(128, collation="utf8mb4", convert_unicode=True), nullable=False, unique=True)
    mod_name = db.Column(db.Unicode(128, collation="utf8mb4", convert_unicode=True), nullable=False, unique=True)
    invite = db.Column(db.String(16), nullable=False, unique=True)
    profile_pic_id = db.Column(db.Integer, db.ForeignKey("image.id"), nullable=False)
    profile_pic = db.relationship('Image')
    description = db.Column(db.UnicodeText(collation="utf8mb4", convert_unicode=True))
    repo = db.Column(db.Text)
    members = db.relationship('User', back_populates="team", lazy=True)

    def __repr__(self):
        return f"<Team #{self.id} '{self.name}' repo={self.repo}>"

class TeamCreation(db.Model):
    id = db.Column(db.Integer, db.ForeignKey("team.id"), primary_key=True)
    creation = db.Column(db.DateTime)

class User(db.Model, flask_login.UserMixin):
    """
    A user describes a participtant of the event.
    """
    id = db.Column(db.Integer, Identity(start=1), primary_key=True)
    ms_id = db.Column(db.String(16), nullable=False, unique=True)
    name = db.Column(db.Unicode(128, collation="utf8mb4", convert_unicode=True), nullable=False, unique=True)
    profile_pic_id = db.Column(db.Integer, db.ForeignKey("image.id"), nullable=False)
    profile_pic = db.relationship('Image')
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    team = db.relationship(Team, back_populates="members")

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"<User #{self.id} '{self.name}'"


class Image(db.Model):
    """
    Defines the table 'image', used as a simple k-v storage for images.
    """
    # Some notes on auto-increment of primary key:
    #   - In SQLite, column type INTEGER PRIMARY KEY is automatically detected, 
    #     and inserting a row with NULL value into that column will trigger 
    #     auto-increment.
    #     https://sqlite.org/autoinc.html
    #   - In MariaDB, column should be explicitly marked as AUTO_INCREMENT 
    #     in order to trigger auto-increment. Doing so, on inserting NULL or 
    #     DEFAULT into that column, auto-increment is triggered.
    #     https://mariadb.com/kb/en/auto_increment/
    #     SQLAlchemy will detect 1st non-foreign integer primary key and mark 
    #     it with autoincrement = True.
    #     TODO Is the behavior of MySQL the same as MariaDB on this regard?
    #   - In PostgreSQL, mark a column as IDENTITY will implicitly create a 
    #     new sequence, and the column will receive new value(s) from that
    #     implicit sequence.
    #     https://www.postgresql.org/docs/10/sql-createtable.html
    # In general, when inserting into this table, we should use id = None 
    # (i.e. NULL in SQL) in order to trigger auto-increment.
    id = db.Column(db.Integer, Identity(start=3), primary_key=True)
    data = db.Column(db.LargeBinary)

    def __repr__(self):
        return f"<Image #{self.id}>"


class OAuth(db.Model, OAuthConsumerMixin):
    """
    An OAuth object represents the OAuth data of the user.
    """
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


class Blacklist(db.Model):
    """
    A blacklist entry defines a blocked user.
    """
    entry_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)


class QQ(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    qq = db.Column(db.String(16), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    verify_code = db.Column(db.String(64), nullable=False)


def init_db(app):
    """
    Initialize the database. Tables are created if not existed yet.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if Image.query.get(1) is None:
            db.session.add(Image(id=1, data=b''))
        if Image.query.get(2) is None:
            db.session.add(Image(id=2, data=b''))
        db.session.commit()
