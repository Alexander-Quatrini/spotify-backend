import config
import requests
import base64
from flask import Flask, redirect, request
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
        header = request.headers.get('Authorization')
        print(header)
        response = requests.get("https://api.spotify.com/v1/me/tracks", headers={'Authorization': header})
        print(response.json())
        if (response.status_code == 401):
            refresh = request_refresh(request.cookies['accessToken'])
            
            if(refresh == None):
                return redirect('http://localhost:5000/login')  
        return response.json()
        
    @app.route('/api/getuserinfo')
    def getUserInfo():
        header = request.headers.get('Authorization')
        response = requests.get("https://api.spotify.com/v1/me", headers={'Authorization': header})
        print(response.json())

        return response.json()
    
    @app.route('/api/getqueue')
    def getQueue():
        header = request.headers.get('Authorization')
        response = requests.get("https://api.spotify.com/v1/me/player/queue", headers={'Authorization': header})
        print(response.json())
        
        return response.json()
    
    return app

def request_refresh(access_token):
    if not (access_token in accessList):
        accessList.pop(access_token)
        return None
    
    refreshTokenParams = dict(grant_type = 'refresh_token', refresh_token = accessList.get(access_token))
    refreshTokenHeaders = dict({'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic ' + b64})

    response = requests.post('https://accounts.spotify.com/api/token', params=refreshTokenParams, headers=refreshTokenHeaders)

    if(response.status_code == 401):
        return None
    
    if(response.status_code == 200):
        accessToken = response.json()['access_token']
        refresh_token = response.json()['refresh_token']
        accessList.update(accessToken, refresh_token)
        return accessToken
    else:
        return None
