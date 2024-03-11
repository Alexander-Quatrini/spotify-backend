import config
import requests
import base64
from flask import Flask, redirect, request, make_response
from flask_cors import CORS;
from urllib.parse import urlencode

accessList = {}

byte = base64.b64encode(bytes(config.clientID + ":" + config.clientSecret, 'utf-8'))
b64 = byte.decode('utf-8')

def create_app():

    app = Flask(__name__, instance_relative_config=True)
    CORS(app, origins= 'https://localhost:3000')


    @app.route('/api/login')
    def login():
        scopeNeeded = 'user-read-currently-playing user-read-playback-state user-library-read'
        params = dict(response_type = 'code', client_id = config.clientID, scope= scopeNeeded, redirect_uri = "http://localhost:5000/callback")

        return redirect('https://accounts.spotify.com/authorize?' + urlencode(params))
    
    @app.route('/callback')
    def access_token():

        accessTokenParams = dict(grant_type = "authorization_code", code=request.args.get('code'), redirect_uri="http://localhost:5000/callback")
        accessTokenHeaders = dict({'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic ' + b64})

        access = requests.post('https://accounts.spotify.com/api/token', params=accessTokenParams, headers=accessTokenHeaders)
        
        accessToken = access.json()['access_token']
        refreshToken = access.json()['refresh_token']

        accessList.update({accessToken: refreshToken})
        
        response = redirect("nuclear-spotify://"+accessToken)

        return response

    @app.route('/api/getlibrary')
    def getSpotifyLibrary():
        return getFromSpotifyAPI("https://api.spotify.com/v1/me/tracks", request)
        
    @app.route('/api/getuserinfo')
    def getUserInfo():
        return getFromSpotifyAPI("https://api.spotify.com/v1/me", request)
    
    @app.route('/api/getqueue')
    def getQueue():
        return getFromSpotifyAPI("https://api.spotify.com/v1/me/player/queue", request)
    
    @app.route('/api/getLibrarySlice')
    def getLibrarySlice():

        offset = request.args.get('offset', None)
        limit = request.args.get('limit', 50)
        if(offset == None):
            err = make_response('Invalid Request', 400)
            return err
        
        return getFromSpotifyAPI("https://api.spotify.com/v1/me/tracks", request, parameters={'offset': offset, 'limit': limit})
    
    @app.route('/api/getAudioFeatures')
    def getAudioFeatures():
        return getFromSpotifyAPI("https://api.spotify.com/v1/audio-features/", request)

    @app.route('/api/getCurrentlyPlaying')
    def getCurrentlyPlaying():
        return getFromSpotifyAPI("https://api.spotify.com/v1/me/player/currently-playing", request)

    return app

def getFromSpotifyAPI(path, req, parameters=None):
    header = req.headers.get('Authorization')        
    response = requests.get(path, params=parameters, headers={'Authorization': header})

    if (response.ok):
        return response.json()
    else:
        errorHandle(response.status_code, header.split()[1])

def errorHandle(status, access_token):
    match status:
        case 401:
            accessToken = request_refresh(access_token)
        case 403:
            err = make_response('Malformed access token', 500)


def request_refresh(access_token):
    if not (access_token in accessList):
        return None
    
    refreshTokenParams = dict(grant_type = 'refresh_token', refresh_token = accessList.get(access_token))
    refreshTokenHeaders = dict({'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic ' + b64})

    response = requests.post('https://accounts.spotify.com/api/token', params=refreshTokenParams, headers=refreshTokenHeaders)

    if (not response.ok):
        return None
    
    else:
        accessToken = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        accessList.update(accessToken, refresh_token)
        return accessToken
