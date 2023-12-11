import time
from app.main import bp
from flask import jsonify, make_response, render_template, current_app as app, session, redirect, request
from app.functions import get_state_key, get_token, toggle_shuffle, toggle_repeat, transfer_playback, refresh_token, search_spotify, play

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
            session['refresh_token'] = token[1]
            session['expires_in'] = time.time() + token[2]
        else:
            return 'Error: Could not retrieve access token.'

    return redirect(session['previous_url'])

@bp.route('/create')
def create():
    return render_template('create.html', title='create')

# API endpoints
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

# autocomplete endpoint
@bp.route('/api/autocomplete', methods=['GET'])
def autocomplete():
    type = request.args.get('type')
    query = request.args.get('query')
    results = search_spotify(session, query, type)
    return jsonify(results)

# play endpoint
@bp.route('/api/play/<type>/<uri>', methods=['PUT'])
def play_results(type, uri):
    return jsonify(play(session, type, uri))