from app import db
from app.functions import add_tracks, delete_playlist, get_playlist, get_playlist_tracks, get_tracks, refresh_token
from flask import current_app as app
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

            token, refresh, expires_in = refresh_token(user.refresh_token)
            if token is None:
                db.session.delete(user)
                app.logger.info('Deleted user {}. Token unable to be updated.'.format(user.username))
                continue
            else:
                user.refresh_token = refresh

            session = {'token': token, 'refresh_token': user.refresh_token, 'expires_in': expires_in}

            def fetch_and_add_tracks(duration, playlist_attr):
                nonlocal updated
                playlist_id = getattr(user, playlist_attr)
                if playlist_id:
                    playlist_track_uris = get_playlist_tracks(session, playlist_id)
                    if playlist_track_uris is not None:
                        delete_playlist(session, playlist_id, playlist_track_uris)
                        tracks = get_tracks(session, duration, 50)
                        track_uris = [track['uri'] for track in tracks['items']]
                        playlist = get_playlist(session, playlist_id)
                        test = add_tracks(session, playlist, track_uris)
                        updated = True
                        app.logger.info('Updated playlist {} for user {}.'.format(playlist_attr, user.username))
                    else:
                        setattr(user, playlist_attr, None)
                        app.logger('Deleted playlist {} for user {}. Unable to get playlist tracks.'.format(playlist_attr, user.username))

            fetch_and_add_tracks('short_term', 'playlist_id_short')
            fetch_and_add_tracks('medium_term', 'playlist_id_medium')
            fetch_and_add_tracks('long_term', 'playlist_id_long')

            if not updated:
                db.session.delete(user)
                app.logger.info('Deleted user {}. No playlists able to be updated.'.format(user.username))

        db.session.commit()
        app.logger.info('Updated all user playlists.')