from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests, random, string
import project

CLIENT_ID = json.loads(open('./keys/client_secrets.json', 'r').read())['web']['client_id']

bp = Blueprint('connect', __name__)


@bp.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    print ("The session state is {}".format (login_session['state']))
    return render_template('login.html', STATE=state)


@bp.route('/gconnect', methods=['POST'])
def gconnect():
    # round-trip verification
    print('gconnect module ' + login_session['state'])
    print('state' + request.args.get('state'))
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    print('code =' + str(code))

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('./keys/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    print ('in gconnect, access token is {}'.format(access_token))
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    print('data = ')
    print(data)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = "dummy@gmail.com"
    login_session['user_id'] = data['id']

    # see if user exists, if it doesn't make a new one

    user_id = project.getUserID(data["id"])


    if not user_id:
        user_id = project.createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '


    flash("you are now logged in as {}".format(login_session['username']))

    print ("done!")
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session

@bp.route('/gdisconnect')
def gdisconnect():
    code = request.data

    credentials = login_session.get('credentials')

    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['credentials']
    print ('In gdisconnect access token is %s' % access_token)
    print ('User name is: ')
    print (login_session['username'])

    if access_token is None:
 	    print ('Access Token is None')
 	    response = make_response(json.dumps('Current user not connected.'), 401)
 	    response.headers['Content-Type'] = 'application/json'
 	    return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['credentials']
        del login_session['user_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("you are successfully logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response




