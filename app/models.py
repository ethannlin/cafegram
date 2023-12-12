from app import db

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    refresh_token = db.Column(db.String(150), index=True, unique=True)
    playlist_id_short = db.Column(db.String(150), index=True, unique=True)
    playlist_id_medium = db.Column(db.String(150), index=True, unique=True)
    playlist_id_long = db.Column(db.String(150), index=True, unique=True)

    def __init__(self, username, refresh_token, playlist_id_short, playlist_id_medium, playlist_id_long):
        self.username = username
        self.refresh_token = refresh_token
        self.playlist_id_short = playlist_id_short
        self.playlist_id_medium = playlist_id_medium
        self.playlist_id_long = playlist_id_long

    def __repr__(self):
        return '<User {}>'.format(self.username)