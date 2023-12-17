import base64
import json
import random
import string
import requests
import time
from flask import current_app as app, session

'''
    Function: get_state_key
    -----------------------
    Returns a randomly generated string of length n
    Used for CSRF protection when retrieving access token
'''
def get_state_key(n: int) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

'''
    Function: get_token
    -------------------
    Returns access token, refresh token, and expiration time in seconds
    Returns None if error occurs
'''
def get_token(code):
    client_id = app.config['CLIENT_ID']
    client_secret = app.config['CLIENT_SECRET']
    redirect_uri = app.config['REDIRECT_URI']
    
    token_url = 'https://accounts.spotify.com/api/token'

    headers = {
        'Authorization' : 'Basic ' + str(base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')), 'utf-8'),
        'Content-Type' : 'application/x-www-form-urlencoded'
        }
    
    body = {
        'grant_type' : 'authorization_code',
        'code' : code,
        'redirect_uri' : redirect_uri
    }

    response = requests.post(token_url, headers=headers, data=body)

    # 200 code indicates access token was properly granted
    if response.status_code == 200:
        json = response.json()
        return json['access_token'], json['refresh_token'], json['expires_in']
    else:
        app.logger.error('get_token:' + str(response.status_code))
        return None
    
'''
    Function: refresh_token
    -----------------------
    Returns new access token, refresh token, and expiration time in seconds
    Returns None if error occurs
'''
def refresh_token(token):
    client_id = app.config['CLIENT_ID']
    client_secret = app.config['CLIENT_SECRET']

    token_url = 'https://accounts.spotify.com/api/token'

    headers = {
        'Authorization' : 'Basic ' + str(base64.b64encode(bytes(client_id + ':' + client_secret, 'utf-8')), 'utf-8'),
        'Content-Type' : 'application/x-www-form-urlencoded'
    }
    
    body = {
        'grant_type' : 'refresh_token',
        'refresh_token' : token
    }

    response = requests.post(token_url, headers=headers, data=body)

    # 200 code indicates access token was properly granted
    if response.status_code == 200:
        json = response.json()
        new_refresh_token = json.get('refresh_token')
        if new_refresh_token is None:
            new_refresh_token = token
        return json['access_token'], new_refresh_token, json['expires_in']
    else:
        app.logger.error('refresh_token:' + str(response.status_code))
        return None

'''
    Function: check_token
    ---------------------
    Returns true if access token is still valid
    If access token is expired, refreshes token and returns true if successful
'''
def check_token(session):
    if time.time() > session['expires_in']:
        token = refresh_token(session['refresh_token'])
        if token is not None:
            session['token'] = token[0]
            session['expires_in'] = time.time() + token[1]
        else:
            app.logger.error('check_token_error')
            return False

    return True

'''
    Request Functions
'''

'''
    Function: get_request
    ---------------------
    Returns json response from get request
    Returns status code if error occurs
'''
def get_request(session, url, params={}):
    headers = {
        'Authorization' : 'Bearer ' + session['token']
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    
    if response.status_code == 401 and check_token(session):
        return get_request(session, url, params)
    else:
        app.logger.error('get_request:' + str(response.status_code))
        return response.text
    
'''
    Function: post_request
    ----------------------
    Returns json response from post request
    Returns status code if error occurs
'''
def post_request(session, url, params={}, data={}):
    headers = {
        'Authorization' : 'Bearer ' + session['token'],
        'Content-Type' : 'application/json'
    }

    response = requests.post(url, headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 201:
        return response.json()
    
    if response.status_code == 401 and check_token(session):
        return post_request(session, url, params, data=json.dumps(data))
    else:
        app.logger.error('post_request:' + str(response.status_code))
        return response.text
    
'''
    Function: put_request
    ---------------------
    Returns json response from put request
    Returns status code if error occurs
'''
def put_request(session, url, params={}, data={}):
    headers = {
        'Authorization' : 'Bearer ' + session['token'],
        'Accept': 'application/json', 
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.put(url, headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 204 or response.status_code == 202 or response.status_code == 200:
        return response.status_code
    
    if response.status_code == 401 and check_token(session):
        return put_request(session, url, params, data=json.dumps(data))
    else:
        app.logger.error('put_request:' + str(response.status_code))
        return response.text

'''
    Function: delete_request
    ------------------------
    Returns json response from delete request
    Returns status code if error occurs
'''
def delete_request(session, url, params={}, data={}):
    headers = {
        'Authorization' : 'Bearer ' + session['token'],
        'Content-Type' : 'application/json'
    }

    response = requests.delete(url, headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()
    
    if response.status_code == 401 and check_token(session):
        return delete_request(session, url, params, data=json.dumps(data))    
    else:
        app.logger.error('delete_request:' + str(response.status_code))
        return response.text
    
'''
    Function: toggle_shuffle
    ------------------------
    Toggles shuffle state
    Returns status code if error occurs
'''
def toggle_shuffle(session, state):
    url = 'https://api.spotify.com/v1/me/player/shuffle'

    params = {
        'state' : state
    }

    return put_request(session, url, params)

'''
    Function: toggle_repeat
    -----------------------
    Toggles repeat state
    Returns status code if error occurs
'''
def toggle_repeat(session, state):
    url = 'https://api.spotify.com/v1/me/player/repeat'

    params = {
        'state' : state
    }

    return put_request(session, url, params)

'''
    Function: transfer_playback
    ---------------------------
    Transfers playback to device
    Returns status code if error occurs
'''
def transfer_playback(session, device_id):
    url = 'https://api.spotify.com/v1/me/player'

    data = {
        "device_ids": [device_id]
    }

    return put_request(session, url, data=data)
'''
    Function: search_spotify
    ------------------------
    Returns json response from search request
    Returns status code if error occurs
'''
def search_spotify(session, query, type, limit=5):
    url = 'https://api.spotify.com/v1/search'

    if type == 'create':
        params = {
            'q' : query,
            'type' : 'artist,track',
            'limit' : limit
        }
    else:
        params = {
            'q' : query,
            'type' : type,
            'limit' : limit
        }

    response = get_request(session, url, params)
    if 'error' in response:
        app.logger.error('search_spotify:' + response)
        return None
        
    results = []

    if type == 'create':
        for artist in response['artists']['items']:
            results.append([artist['name'], 'a:'+artist['id'], artist['popularity']])
        for track in response['tracks']['items']:
            name = track['name'] + ' by ' + track['artists'][0]['name']
            results.append([name, 't:'+track['id'], track['popularity']])
        results.sort(key=lambda x: x[2], reverse=True)

    if type == 'artist':
        for artist in response['artists']['items']:
            results.append([artist['name'], artist['uri'], artist['popularity']])
        results.sort(key=lambda x: x[2], reverse=True)

    if type == 'track':
        for track in response['tracks']['items']:
            name = track['name'] + ' by ' + track['artists'][0]['name']
            results.append([name, track['uri'], track['popularity']])
        results.sort(key=lambda x: x[2], reverse=True)

    if type == 'playlist':
        for playlist in response['playlists']['items']:
            name = playlist['name'] + ' by ' + playlist['owner']['display_name']
            results.append([name, playlist['uri']])

    if type == 'album':
        for album in response['albums']['items']:
            name = album['name'] + ' by ' + album['artists'][0]['name']
            results.append([name, album['uri']])

    results_json = []
    for item in results:
        results_json.append({'label' : item[0], 'value' : item[1]})
    
    return results_json

'''
    Function: play
    --------------
    Plays track, artist, album, or playlist
    Returns status code if error occurs
'''
def play(session, type, uri):
    url = 'https://api.spotify.com/v1/me/player/play'

    if type == 'track':
        data = {
            "uris": [uri]
        }
    else:
        data = {
            "context_uri": uri
        }

    return put_request(session, url, data=data)
    
'''
    Function: get_recommendations
    -----------------------------
    Returns json response from recommendations request
    Returns status code if error occurs
'''
def get_recommendations(session, seeds, tune_params, limit=5):
    url = 'https://api.spotify.com/v1/recommendations'

    seed_artists = []
    seed_tracks = []
    for seed in seeds:
        if seed[0] == 'a':
            seed_artists.append(seed[2:])
        if seed[0] == 't':
            seed_tracks.append(seed[2:])
    
    params = {
        'seed_artists' : seed_artists,
        'seed_tracks' : seed_tracks,
        'limit' : limit
    }

    params.update(tune_params)

    response = get_request(session, url, params)

    if 'error' in response:
        app.logger.error('get_recommendations:' + response)
        return None
    
    uris = []

    for track in response['tracks']:
        uris.append(track['uri'])
    
    return uris

'''
    function: get_user
    ------------------
    Returns json response from user request
    Returns status code if error occurs
'''
def get_user(session):
    url = 'https://api.spotify.com/v1/me'

    response = get_request(session, url)

    if 'error' in response:
        app.logger.error('get_user:' + response)
        return None
    
    return response

'''
    function: create_playlist
    -------------------------
    Creates playlist
    Returns status code if error occurs
'''
def create_playlist(session, name):
    user = get_user(session)
    if user is None:
        return None
    
    url = 'https://api.spotify.com/v1/users/' + user['id'] + '/playlists'

    data = {
        'name' : name,
        'description' : 'created by cafégram'
    }

    response = post_request(session, url, data=data)

    if 'error' in response:
        app.logger.error('create_playlist:' + response)
        return None
    
    return response
    
'''
    function: add_tracks
    --------------------
    Adds tracks to a given playlist
    Returns status code if error occurs
'''
def add_tracks(session, playlist, track_uris):

    url = 'https://api.spotify.com/v1/playlists/' + playlist['id'] + '/tracks'

    data = {
        'uris' : track_uris
    }

    response = post_request(session, url, data=data)

    if 'error' in response:
        app.logger.error('add_tracks:' + response)
        return None
    
    return playlist['uri'], playlist['id']

'''
    function: get_tracks
    --------------------
    Returns json response from tracks request
    Returns status code if error occurs
'''
def get_tracks(session, time_range='short_term', limit=10):
    url = 'https://api.spotify.com/v1/me/top/tracks'

    params = {
        'time_range' : time_range,
        'limit' : limit
    }

    response = get_request(session, url, params)

    if 'error' in response:
        app.logger.error('get_tracks:' + response)
        return None
    
    return response

'''
    function: get_playlist_tracks
    -----------------------------
    Returns json response from playlist tracks request
    Returns status code if error occurs
'''
def get_playlist_tracks(session, playlist_id):
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'

    params = {
        'limit' : 50,
    }
    response = get_request(session, url, params)
    if 'error' in response:
        app.logger.error('get_playlist_tracks:' + response)
        return None
    track_uris = []
    for track in response['items']:
        track_uris.append(track['track']['uri'])
    return track_uris

'''
    function: delete_playlist
    -------------------------
    Deletes playlist
    Returns status code if error occurs
'''
def delete_playlist(session, playlist_id, track_uris):
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'

    tracks =[]
    for track in track_uris:
        tracks.append({'uri' : track})
    
    data = {
        'tracks' : tracks
    }

    response = delete_request(session, url, data=data)

    if 'error' in response:
        app.logger.error('delete_playlist:' + response)
        return None
    
    return response

'''
    function: get_playlist
    ----------------------
    Returns json response from playlist request
    Returns status code if error occurs
'''
def get_playlist(session, playlist_id):
    url = 'https://api.spotify.com/v1/playlists/{playlist_id}'.format(playlist_id=playlist_id)
    
    response = get_request(session, url)

    if 'error' in response:
        app.logger.error('get_playlist:' + response)
        return None
    
    return response

'''
    update_playlist_name
    ---------------
    update playlist name
    Returns status code if error occurs
'''
def update_playlist_name(session, playlist_id, playlist_name):
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id

    data = {
        'name' : playlist_name
    }

    response = put_request(session, url, data=data)

    if response != 200 and response != 202 and response != 204: 
        app.logger.error('change_playlist_name:' + response)
        return None

    return response
