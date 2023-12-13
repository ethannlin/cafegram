import logging
import time
from app.main import bp
from flask import jsonify, render_template, current_app as app, session, redirect, request
from app.functions import delete_playlist, get_playlist, get_playlist_tracks, get_state_key, get_token, get_tracks, get_user, toggle_shuffle, toggle_repeat, transfer_playback, refresh_token, search_spotify, play, get_recommendations, create_playlist, add_tracks
from app.models import Users
from app import db

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/home', methods=['GET', 'POST'])
def home():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('home.html', title='home')
    return render_template('home.html', title='home', token=session['token'])

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
            print(len(token[1]))
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
    if user is None:
        return render_template('create.html', title='create', token=session['token'], error='Error: Could not retrieve user.')
    
    existing_user = Users.query.filter_by(username=user['id']).first()
    update = False
    if existing_user is not None and existing_user.playlist_id_recs is not None:
        update = True

    return render_template('create.html', title='create', token=session['token'], update=update)

@bp.route('/discover')
def discover():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('discover.html', title='discover')
    
    track_ids = [[] for i in range(3)]
    term = ['short_term', 'medium_term', 'long_term']
    # get user's top tracks
    for i in range(3):
        top_tracks = get_tracks(session, term[i], 10)
        for track in top_tracks['items']:
            track_ids[i].append(track['id'])

    user = get_user(session)
    if user is None:
        return render_template('discover.html', title='discover', token=session['token'], track_ids=track_ids, error='Error: Could not retrieve user.', code=app.config['AUTO_UPDATE_CODE'])

    return render_template('discover.html', title='discover', token=session['token'], track_ids=track_ids, code=app.config['AUTO_UPDATE_CODE'])

@bp.route('/discover/create-playlist', methods=['POST'])
def discover_create():
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
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.', code=app.config['AUTO_UPDATE_CODE'])
        
        tracks = get_tracks(session, 'short_term', 50)
        if tracks is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.', code=app.config['AUTO_UPDATE_CODE'])
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])

        short_term_uri, short_term_id = add_tracks(session, playlist, track_uris)

    if 'medium_term' in request.form:
        playist_name = request.form.get('medium_term_name')
        playlist = create_playlist(session, playist_name)
        if playlist is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.', code=app.config['AUTO_UPDATE_CODE'])
        
        tracks = get_tracks(session, 'medium_term', 50)
        if tracks is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.', code=app.config['AUTO_UPDATE_CODE'])
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])
        
        medium_term_uri, medium_term_id = add_tracks(session, playlist, track_uris)

    if 'long_term' in request.form:
        playist_name = request.form.get('long_term_name')
        playlist = create_playlist(session, playist_name)
        if playlist is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not create playlist.', code=app.config['AUTO_UPDATE_CODE'])
        
        tracks = get_tracks(session, 'long_term', 50)
        if tracks is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve tracks.', code=app.config['AUTO_UPDATE_CODE'])
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])

        long_term_uri, long_term_id = add_tracks(session, playlist, track_uris)
    
    if request.form.get('update') == 'on' and request.form.get('update_code') == app.config['AUTO_UPDATE_CODE']:
        user = get_user(session)
        if user is None:
            return render_template('discover.html', title='discover', token=session['token'], track_ids=[], error='Error: Could not retrieve user.', code=app.config['AUTO_UPDATE_CODE'])
        
        existing_user = Users.query.filter_by(username=user['id']).first()
        if existing_user is not None:
            if short_term_uri:
                existing_user.playlist_id_short = short_term_id
            if medium_term_uri:
                existing_user.playlist_id_medium = medium_term_id
            if long_term_uri:
                existing_user.playlist_id_long = long_term_id
            db.session.commit()
        else:
            u = Users(username=user['id'], refresh_token=session['refresh_token'], playlist_id_short=short_term_id, playlist_id_medium=medium_term_id, playlist_id_long=long_term_id, playlist_id_recs=None)
            db.session.add(u)
            db.session.commit()
            
        logging.info('User {} playlists to be autoupdated.'.format(user['id']))

    if short_term_uri:
        return short_term_uri
    elif medium_term_uri:
        return medium_term_uri
    elif long_term_uri:
        return long_term_uri

# create playlist endpoint
@bp.route('/recommend', methods=['POST', 'GET'])
def recommendation_playlist():
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
    existing_user = Users.query.filter_by(username=user['id']).first()

    if existing_user is not None:
        if request.form.get('update') == 'true' and existing_user.playlist_id_recs is not None:
            playlist = get_playlist(session, existing_user.playlist_id_recs)
            if playlist is None:
                return render_template('create.html', title='create', token=session['token'], update=True, error='Error: Could not retrieve playlist.')
            
            playlist_tracks = get_playlist_tracks(session, existing_user.playlist_id_recs)
            if playlist_tracks is None:
                return render_template('create.html', title='create', token=session['token'],update=True, error='Error: Could not retrieve playlist tracks.')
            
            delete_playlist(session, existing_user.playlist_id_recs, playlist_tracks)
        else:
            playlist = create_playlist(session, playlist_name)
            if playlist is None:
                return render_template('create.html', title='create', token=session['token'], error='Error: Could not create playlist.')
            existing_user.playlist_id_recs = playlist['id']
            db.session.commit()
    else:
        playlist = create_playlist(session, playlist_name)
        if playlist is None:
            return render_template('create.html', title='create', token=session['token'], error='Error: Could not create playlist.')
        
        u = Users(username=user['id'], refresh_token=session['refresh_token'], playlist_id_short=None, playlist_id_medium=None, playlist_id_long=None, playlist_id_recs=playlist['id'])
        db.session.add(u)
        db.session.commit()
    
    playlist_uri = add_tracks(session, playlist, track_recommendations)

    return playlist_uri

'''
    API Endpoints
'''
# toggle shuffle endpoint
@bp.route('/api/shuffle/<state>', methods=['PUT'])
def shuffle(state):
    return jsonify(toggle_shuffle(session, state))

# toggle repeat endpoint
@bp.route('/api/repeat/<state>', methods=['PUT'])
def repeat(state):
    return jsonify(toggle_repeat(session, state))

# transfer playback endpoint
@bp.route('/api/transfer/<device_id>', methods=['PUT'])
def transfer(device_id):
    return jsonify(transfer_playback(session, device_id))

# refresh token endpoint
@bp.route('/api/refresh', methods=['POST'])
def refresh():
    token = refresh_token(session['refresh_token'])
    if token is not None:
        session['token'] = token[0]
        session['expires_in'] = time.time() + token[1]
    else:
        return render_template('home.html', title='home', error='Error: Could not retrieve access token.')
    
    return jsonify({'token' : session['token'], 'expires_in' : session['expires_in']})

# play endpoint
@bp.route('/api/play/<type>/<uri>', methods=['PUT'])
def play_results(type, uri):
    return jsonify(play(session, type, uri))

'''
    Endpoints for searching and creating playlists
'''
# autocomplete endpoint
@bp.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    type = request.args.get('type')
    query = request.args.get('query')
    results = search_spotify(session, query, type)
    return jsonify(results)