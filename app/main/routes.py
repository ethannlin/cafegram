import time
from app.main import bp
from flask import jsonify, render_template, current_app as app, session, redirect, request
from app.functions import get_state_key, get_token, get_tracks, get_user, toggle_shuffle, toggle_repeat, transfer_playback, refresh_token, search_spotify, play, get_recommendations, create_playlist, add_tracks
from app.models import TopTracks, Users, CustomPlaylists
from app import db

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/home', methods=['GET', 'POST'])
def home():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('home.html', title='home')

    user = get_user(session)
    if user == "User not registered in the Developer Dashboard":
        return render_template('home.html', title='home', token=session['token'], expires_in=session['expires_in'], error='Error: User not registered by admin in the Developer Dashboard.')

    return render_template('home.html', title='home', token=session['token'], expires_in=session['expires_in'])

@bp.route('/about')
def about():
    return render_template('about.html', title='about')

@bp.route('/login')
def login():
    client_id = app.config['CLIENT_ID']
    redirect_uri = app.config['REDIRECT_URI']
    scope = app.config['SCOPE']

    state = get_state_key(16)
    session['state'] = state

    session['previous_url'] = request.referrer

    authorize_url = 'https://accounts.spotify.com/authorize?'
    parameters = 'response_type=code&client_id={}&redirect_uri={}&scope={}&state={}'.format(client_id, redirect_uri, scope, state)

    return redirect(authorize_url + parameters)

@bp.route('/callback')
def callback():
    if request.args.get('state') != session['state']:
        return render_template('home.html', title='home', error='Error: State mismatch.')
    if request.args.get('error'):
        return render_template('home.html', title='home', error='Error: {}'.format(request.args.get('error')))
    else:
        code = request.args.get('code')
        session.pop('state', None)

        token = get_token(code)
        if token is not None:
            session['token'] = token[0]
            session['refresh_token'] = token[1]
            session['expires_in'] = time.time() + token[2]
        else:
            return render_template('home.html', title='home', error='Error: Could not retrieve access token.')

    return redirect(session['previous_url'])

@bp.route('/create')
def create():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('create.html', title='create')

    user = get_user(session)
    if user is None or user == "User not registered in the Developer Dashboard":
        return render_template('create.html', title='create', token=session['token'], error='Error: Could not retrieve user.')

    return render_template('create.html', title='create', token=session['token'])

@bp.route('/discover')
def discover():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('discover.html', title='discover')

    track_ids = [[] for i in range(3)]
    term = ['short_term', 'medium_term', 'long_term']
    # get user's top tracks
    for i in range(3):
        top_tracks = get_tracks(session, term[i], 10)
        if top_tracks is None or top_tracks == "User not registered in the Developer Dashboard":
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.')
        for track in top_tracks['items']:
            track_ids[i].append(track['id'])

    return render_template('discover.html', title='discover', token=session['token'], track_ids=track_ids)

'''
    API Endpoints
'''
# discover tab create playlist endpoint
@bp.route('/discover/create-playlist', methods=['POST'])
def discover_create():
    with app.app_context():
        short_term_uri = None
        medium_term_uri = None
        long_term_uri = None
        short_term_id = None
        medium_term_id = None
        long_term_id = None

        if 'short_term' in request.form:
            playist_name = request.form.get('short_term_name')
            playlist = create_playlist(session, playist_name)
            if playlist is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.')

            tracks = get_tracks(session, 'short_term', 50)
            if tracks is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.')
            track_uris = []
            for track in tracks['items']:
                track_uris.append(track['uri'])

            short_term_uri, short_term_id = add_tracks(session, playlist, track_uris)

        if 'medium_term' in request.form:
            playist_name = request.form.get('medium_term_name')
            playlist = create_playlist(session, playist_name)
            if playlist is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.')

            tracks = get_tracks(session, 'medium_term', 50)
            if tracks is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.')
            track_uris = []
            for track in tracks['items']:
                track_uris.append(track['uri'])

            medium_term_uri, medium_term_id = add_tracks(session, playlist, track_uris)

        if 'long_term' in request.form:
            playist_name = request.form.get('long_term_name')
            playlist = create_playlist(session, playist_name)
            if playlist is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.')

            tracks = get_tracks(session, 'long_term', 50)
            if tracks is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.')
            track_uris = []
            for track in tracks['items']:
                track_uris.append(track['uri'])

            long_term_uri, long_term_id = add_tracks(session, playlist, track_uris)

        if request.form.get('update') == 'on':
            user = get_user(session)
            if user is None:
                return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve user.')

            existing_user = Users.query.filter_by(username=user['id']).first()
            if existing_user is not None:
                existing_playlists = TopTracks.query.filter_by(user_id=existing_user.id).first()
                if existing_playlists is not None:
                    if short_term_uri:
                        existing_playlists.playlist_id_short = short_term_id
                    if medium_term_uri:
                        existing_playlists.playlist_id_medium = medium_term_id
                    if long_term_uri:
                        existing_playlists.playlist_id_long = long_term_id
                    app.logger.info('User {} top track playlists updated.'.format(user['id']))
            else:
                u = Users(username=user['id'], refresh_token=session['refresh_token'])
                db.session.add(u)
                db.session.commit()

                tt = TopTracks(user_id=u.id, playlist_id_short=short_term_id, playlist_id_medium=medium_term_id, playlist_id_long=long_term_id)
                db.session.add(tt)
                app.logger.info('User {} added to the db.'.format(user['id']))

            app.logger.info('User {} playlists to be autoupdated.'.format(user['id']))
        db.session.commit()
        if short_term_uri:
            return jsonify({'playlist_uri' : short_term_uri }), 200
        elif medium_term_uri:
            return jsonify({'playlist_uri' : medium_term_uri }), 200
        elif long_term_uri:
            return jsonify({'playlist_uri' : long_term_uri }), 200

# create tab create playlist endpoint
@bp.route('/recommend', methods=['POST', 'GET'])
def recommendation_playlist():
    with app.app_context():
    # print(request.form)
        playlist_name = request.form.get('name')

        seeds = []
        for i in range(int(request.form.get('seed_count'))):
            seeds.append(request.form.get(str(i)))

        tune_params = {}
        if 'slider_acoustic' in request.form:
            tune_params['target_acousticness'] = request.form.get('slider_acoustic')

        if 'slider_danceability' in request.form:
            tune_params['target_danceability'] = request.form.get('slider_danceability')

        if 'slider_energy' in request.form:
            tune_params['target_energy'] = request.form.get('slider_energy')

        if 'slider_instrumental' in request.form:
            tune_params['target_instrumentalness'] = request.form.get('slider_instrumental')

        if 'slider_lively' in request.form:
            tune_params['target_liveness'] = request.form.get('slider_lively')

        if 'slider_popularity' in request.form:
            tune_params['target_popularity'] = request.form.get('slider_popularity')

        if 'slider_speech' in request.form:
            tune_params['target_speechiness'] = request.form.get('slider_speech')

        if 'slider_valence' in request.form:
            tune_params['target_valence'] = request.form.get('slider_valence')

        limit = request.form.get('slider_limit')

        track_recommendations = get_recommendations(session, seeds, tune_params, limit)
        if track_recommendations is None:
            return render_template('create.html', title='create', token=session['token'], error='Error: Could not retrieve recommendations.')

        user = get_user(session)
        if user is None:
            return render_template('create.html', title='create', token=session['token'], error='Error: Could not retrieve user.')

        if request.form.get('update') == 'true':
            seed_artists = ""
            seed_tracks = ""
            seed_attr = ""

            for seed in seeds:
                if seed[0] == 'a':
                    seed_artists += seed[2:] + ','
                elif seed[0] == 't':
                    seed_tracks += seed[2:] + ','

            # remove trailing comma
            seed_artists = seed_artists[:-1]
            seed_tracks = seed_tracks[:-1]

            for key, value in tune_params.items():
                seed_attr += key + ':' + value + ','
            seed_attr += 'n:' + limit
            existing_user = Users.query.filter_by(username=user['id']).first()

            if existing_user is not None:
                playlist = create_playlist(session, playlist_name)
                if playlist is None:
                    return render_template('create.html', title='create', token=session['token'], error='Error: Could not create playlist.')

                c = CustomPlaylists(user_id=existing_user.id, playlist_id=playlist['id'], playlist_name=playlist_name, seed_artists=seed_artists, seed_tracks=seed_tracks, seed_attr=seed_attr)
                db.session.add(c)
                app.logger.info('{} created for user {}.'.format(playlist_name, user['id']))
            else:
                playlist = create_playlist(session, playlist_name)
                if playlist is None:
                    return render_template('create.html', title='create', token=session['token'], error='Error: Could not create playlist.')

                u = Users(username=user['id'], refresh_token=session['refresh_token'])
                db.session.add(u)
                db.session.commit()

                c = CustomPlaylists(user_id=u.id, playlist_id=playlist['id'], playlist_name=playlist_name, seed_artists=seed_artists, seed_tracks=seed_tracks, seed_attr=seed_attr)
                db.session.add(c)
                app.logger.info('User {} added to the db.'.format(user['id']))
        else:
            playlist = create_playlist(session, playlist_name)
            if playlist is None:
                return render_template('create.html', title='create', token=session['token'], error='Error: Could not create playlist.')

        db.session.commit()

        playlist_uri = add_tracks(session, playlist, track_recommendations)

        return jsonify({'playlist_uri' : playlist_uri[0]}), 200

# toggle shuffle endpoint
@bp.route('/api/shuffle/<state>', methods=['PUT'])
def shuffle(state):
    return jsonify(toggle_shuffle(session, state)), 200

# toggle repeat endpoint
@bp.route('/api/repeat/<state>', methods=['PUT'])
def repeat(state):
    return jsonify(toggle_repeat(session, state)), 200

# transfer playback endpoint
@bp.route('/api/transfer/<device_id>', methods=['PUT'])
def transfer(device_id):
    return jsonify(transfer_playback(session, device_id)), 200

# refresh token endpoint
@bp.route('/api/refresh', methods=['POST'])
def refresh():
    token = refresh_token(session['refresh_token'])
    if token is not None:
        session['token'] = token[0]
        session['refresh_token'] = token[1]
        session['expires_in'] = time.time() + token[2]
    else:
        return render_template('home.html', title='home', error='Error: Could not retrieve access token.')

    return jsonify({'token' : session['token'], 'refresh_token' : session['refresh_token'], 'expires_in' : session['expires_in']}), 200

# play endpoint
@bp.route('/api/play/<type>/<uri>', methods=['PUT'])
def play_results(type, uri):
    return jsonify(play(session, type, uri)), 200

'''
    Endpoints for searching and creating playlists
'''
# autocomplete endpoint
@bp.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    type = request.args.get('type')
    query = request.args.get('query')
    results = search_spotify(session, query, type)
    return jsonify(results), 200

# update playlist endpoint for manual playlist updates
@bp.route('/api/update-playlists', methods=['POST'])
def update():
    with app.app_context():
        TopTracks.update_playlists()
        CustomPlaylists.update_playlists()

    return jsonify({'message': 'Playlist update triggered successfully'}), 200