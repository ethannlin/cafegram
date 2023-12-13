import logging

from app import db
from app.functions import add_tracks, delete_playlist, get_playlist, get_playlist_tracks, get_tracks, refresh_token

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    refresh_token = db.Column(db.String(150), index=True, unique=True)
    playlist_id_short = db.Column(db.String(30), index=True, unique=True)
    playlist_id_medium = db.Column(db.String(30), index=True, unique=True)
    playlist_id_long = db.Column(db.String(30), index=True, unique=True)
    playlist_id_recs = db.Column(db.String(30), index=True, unique=True)

    def __init__(self, username, refresh_token, playlist_id_short=None, playlist_id_medium=None, playlist_id_long=None, playlist_id_recs=None):
        self.username = username
        self.refresh_token = refresh_token
        self.playlist_id_short = playlist_id_short
        self.playlist_id_medium = playlist_id_medium
        self.playlist_id_long = playlist_id_long
        self.playlist_id_recs = playlist_id_recs

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    @staticmethod
    def update_playlists():
        users = Users.query.all()

        for user in users:
            updated = False

            token, expires_in = refresh_token(user.refresh_token)
            if token is None:
                db.session.delete(user)
                continue

            session = {'token': token, 'refresh_token': user.refresh_token, 'expires_in': expires_in}

            if user.playlist_id_short:
                playlist_track_uris = get_playlist_tracks(session, user.playlist_id_short)
                if delete_playlist(session, user.playlist_id_short, playlist_track_uris) is not None:
                    tracks = get_tracks(session, 'short_term', 50)
                    track_uris = []
                    for track in tracks['items']:
                        track_uris.append(track['uri'])

                    short_term_playlist = get_playlist(session, user.playlist_id_short)
                    add_tracks(session, short_term_playlist, track_uris)
                    updated = True
                else:
                    user.playlist_id_short = None
                
            if user.playlist_id_medium:
                playlist_track_uris = get_playlist_tracks(session, user.playlist_id_medium)
                if delete_playlist(session, user.playlist_id_medium, playlist_track_uris) is not None:
                    tracks = get_tracks(session, 'medium_term', 50)
                    track_uris = []
                    for track in tracks['items']:
                        track_uris.append(track['uri'])

                    medium_term_playlist = get_playlist(session, user.playlist_id_medium)
                    add_tracks(session, medium_term_playlist, track_uris)
                    updated = True
                else:
                    user.playlist_id_medium = None
                
            if user.playlist_id_long:
                playlist_track_uris = get_playlist_tracks(session, user.playlist_id_long)
                delete_playlist(session, user.playlist_id_long, playlist_track_uris)

                tracks = get_tracks(session, 'long_term', 50)
                track_uris = []
                for track in tracks['items']:
                    track_uris.append(track['uri'])

                long_term_playlist = get_playlist(session, user.playlist_id_long)
                add_tracks(session, long_term_playlist, track_uris)
                updated = True
            else:
                user.playlist_id_long = None
            
            if not updated:
                db.session.delete(user)
        
        db.session.commit()
            
        logging.info('Updated all user playlists.')