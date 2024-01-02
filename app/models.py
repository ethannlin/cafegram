import time
from app import db
from app.functions import add_tracks, delete_playlist, get_playlist, get_playlist_tracks, get_recommendations, get_tracks, refresh_token
from flask import current_app as app
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    refresh_token = db.Column(db.String(150), index=True, unique=True)

    def __init__(self, username, refresh_token):
        self.username = username
        self.refresh_token = refresh_token

    def __repr__(self):
        return '<User {}>'.format(self.username)

class TopTracks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',  ondelete='CASCADE'), nullable=False)
    user = db.relationship('Users', backref=db.backref('top_tracks', lazy=True))
    playlist_id_short = db.Column(db.String(30), index=True, unique=True)
    playlist_id_medium = db.Column(db.String(30), index=True, unique=True)
    playlist_id_long = db.Column(db.String(30), index=True, unique=True)

    def __init__(self, user_id, playlist_id_short=None, playlist_id_medium=None, playlist_id_long=None):
        self.user_id = user_id
        self.playlist_id_short = playlist_id_short
        self.playlist_id_medium = playlist_id_medium
        self.playlist_id_long = playlist_id_long

    def __repr__(self):
        return '<TopTracks {}>'.format(self.user.username)

    @staticmethod
    def update_playlists():
        topTracks = TopTracks.query.all()
        max_tries = 5
        retry_delay = 2

        def fetch_and_add_tracks(duration, playlist_attr):
            nonlocal updated
            playlist_id = getattr(track, playlist_attr)
            if playlist_id:
                playlist_track_uris = get_playlist_tracks(session, playlist_id)
                status = delete_playlist(session, playlist_id, playlist_track_uris)
                if playlist_track_uris is not None and status is not None:
                    tracks = get_tracks(session, duration, 50)
                    track_uris = [track['uri'] for track in tracks['items']]
                    playlist = get_playlist(session, playlist_id)
                    add_tracks(session, playlist, track_uris)
                    updated = True
                    app.logger.info('Updated playlist {} (id: {}) for user {}.'.format(playlist_attr, playlist_id, track.user.username))
                else:
                    setattr(track, playlist_attr, None)
                    app.logger.warning('Deleted playlist {} (id: {}) for user {}. Unable to get playlist tracks.'.format(playlist_attr, playlist_id, track.user.username))

        for i in range(max_tries):
            try:
                for track in topTracks:
                    updated = False

                    token, refresh, expires_in = refresh_token(track.user.refresh_token)
                    if token is None:
                        db.session.delete(track.user)
                        app.logger.warning('Deleted user {}. Token unable to be updated.'.format(track.user.username))
                        continue

                    track.user.refresh_token = refresh

                    session = {'token': token, 'refresh_token': refresh, 'expires_in': expires_in}

                    fetch_and_add_tracks('short_term', 'playlist_id_short')
                    fetch_and_add_tracks('medium_term', 'playlist_id_medium')
                    fetch_and_add_tracks('long_term', 'playlist_id_long')

                    if not updated:
                        db.session.delete(track.user)
                        app.logger.warning('Deleted user {}. No playlists able to be updated.'.format(track.user.username))

                db.session.commit()
                app.logger.info('Updated all user playlists.')
                break;
            except Exception as e:
                app.logger.warning('Error updating user playlists: {}'.format(str(e)))
                if i < max_tries-1:
                    delay = retry_delay * (2**i)
                    app.logger.warning('Retrying in {} seconds.'.format(delay))
                    time.sleep(delay)
                else:
                    app.logger.warning('Max retries reached. Some playlists may not be updated.')

class CustomPlaylists(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = db.relationship('Users', backref=db.backref('custom_playlists', lazy=True))
    playlist_name = db.Column(db.String(100), index=True)
    playlist_id = db.Column(db.String(30), index=True, unique=True)
    seed_artists = db.Column(db.String(1000))
    seed_tracks = db.Column(db.String(1000))
    seed_attr = db.Column(db.String(1000))

    def __init__(self, user_id, playlist_id, playlist_name, seed_artists, seed_tracks, seed_attr):
        self.user_id = user_id
        self.playlist_id = playlist_id
        self.playlist_name = playlist_name
        self.seed_artists = seed_artists
        self.seed_tracks = seed_tracks
        self.seed_attr = seed_attr

    def __repr__(self):
        return '<CustomPlaylists {}>'.format(self.playlist_name)

    @staticmethod
    def update_playlists():
        playlists = CustomPlaylists.query.all()
        max_tries = 5
        retry_delay = 2

        for i in range(max_tries):
            try:
                for playlist in playlists:
                    token, refresh, expires_in = refresh_token(playlist.user.refresh_token)
                    if token is None:
                        db.session.delete(playlist)
                        app.logger.warning('Deleted playlist {}(id: {}) for {}. Token unable to be updated.'.format(playlist.playlist_name, playlist.playlist_id, playlist.user.username))
                        continue

                    playlist.user.refresh_token = refresh

                    session = {'token': token, 'refresh_token': refresh, 'expires_in': expires_in}

                    seeds = {'seed_artists': playlist.seed_artists.split(','), 'seed_tracks': playlist.seed_tracks.split(',')}
                    tune_params = playlist.seed_attr.split(',')
                    tune_params = {tune_param.split(':')[0]: tune_param.split(':')[1] for tune_param in tune_params}
                    limit = tune_params.pop('n', 100)

                    track_uris = get_playlist_tracks(session, playlist.playlist_id)

                    if track_uris is not None:
                        status = delete_playlist(session, playlist.playlist_id, track_uris)
                        if status is not None:
                            playlist_info = get_playlist(session, playlist.playlist_id)
                            tracks = get_recommendations(session, seeds, tune_params, limit)
                            add_tracks(session, playlist_info, tracks)
                            app.logger.info('Updated playlist {} (id: {}) for {}.'.format(playlist.playlist_name, playlist.playlist_id, playlist.user.username))
                        else:
                            db.session.delete(playlist)
                            app.logger.warning('Deleted playlist {} (id: {}) for {}. Unable to get playlist tracks.'.format(playlist.playlist_name, playlist.playlist_id, playlist.user.username))
                    else:
                        db.session.delete(playlist)
                        app.logger.warning('Deleted playlist {} (id: {}) for {}. Unable to get playlist tracks.'.format(playlist.playlist_name, playlist.playlist_id, playlist.user.username))

                db.session.commit()
                app.logger.info('Updated all custom playlists.')
                break;
            except Exception as e:
                app.logger.warning('Error updating custom playlists: {}'.format(str(e)))
                if i < max_tries-1:
                    delay = retry_delay * (2**i)
                    app.logger.warning('Retrying in {} seconds.'.format(delay))
                    time.sleep(delay)
                else:
                    app.logger.warning('Max retries reached. Some playlists may not be updated.')