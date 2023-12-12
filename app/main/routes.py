import time
from app.main import bp
from flask import jsonify, render_template, current_app as app, session, redirect, request
from app.functions import get_state_key, get_token, get_tracks, toggle_shuffle, toggle_repeat, transfer_playback, refresh_token, search_spotify, play, get_recommendations, create_playlist, add_tracks

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/home', methods=['GET', 'POST'])
def home():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('home.html', title='home')
    return render_template('home.html', title='home', token=session['token'], refresh_token=session['refresh_token'], expires_in=session['expires_in'])

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
        return 'Error: State mismatch.'
    if request.args.get('error'):
        return 'Error: ' + request.args.get('error')
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
            return 'Error: Could not retrieve access token.'

    return redirect(session['previous_url'])

@bp.route('/create')
def create():
    if 'token' not in session or 'expires_in' not in session or time.time() > session['expires_in']:
        return render_template('create.html', title='create')
    return render_template('create.html', title='create', token=session['token'], refresh_token=session['refresh_token'], expires_in=session['expires_in'])

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

    return render_template('discover.html', title='discover', token=session['token'], refresh_token=session['refresh_token'], expires_in=session['expires_in'], track_ids=track_ids)

@bp.route('/discover/create-playlist', methods=['POST'])
def discover_create():
    playlist_uri = ''
    if 'short_term' in request.form:
        playist_name = request.form.get('short_term_name')
        playlist = create_playlist(session, playist_name)
        if playlist is None:
            return 'Error: Could not create playlist.'
        
        tracks = get_tracks(session, 'short_term', 50)
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])

        playlist_uri = add_tracks(session, playlist, track_uris)

    if 'medium_term' in request.form:
        playist_name = request.form.get('medium_term_name')
        playlist = create_playlist(session, playist_name)
        if playlist is None:
            return 'Error: Could not create playlist.'

        tracks = get_tracks(session, 'medium_term', 50)
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])
        
        playlist_uri = add_tracks(session, playlist, track_uris)

    if 'long_term' in request.form:
        playist_name = request.form.get('long_term_name')
        playlist = create_playlist(session, playist_name)
        if playlist is None:
            return 'Error: Could not create playlist.'
        
        tracks = get_tracks(session, 'long_term', 50)
        track_uris = []
        for track in tracks['items']:
            track_uris.append(track['uri'])

        playlist_uri = add_tracks(session, playlist, track_uris)

    if 'auto_update' in request.form:
        pass

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
        return 'Error: Could not retrieve access token.'
    
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

# create playlist endpoint
@bp.route('/api/create', methods=['POST', 'GET'])
def pcreate():
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
    playlist = create_playlist(session, playlist_name)

    if playlist is None:
        return 'Error: Could not create playlist.'
    
    playlist_uri = add_tracks(session, playlist, track_recommendations)

    return playlist_uri
    
