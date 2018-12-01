#! /usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash    #import flask class

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random, string

# imports for OAuth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

#  --------------------  declare Client ID to OAuth ------------------------#

CLIENT_ID = json.loads(
    open('./instance/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "pizzanode"
app = Flask(__name__)


 #create instance of class Flask

#  --------------------  instantiate DB engine ------------------------#

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# ----------------------  User Helper Functions ----------------------------#

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# -----------------------  define URL routing and pages ------------ #


@app.route('/')
@app.route('/restaurant/')
#                            Show all my restaurants"
def showRestaurants():
    restaurants = session.query(Restaurant).all()

    if 'username' not in login_session:
        return render_template('publicrestaurants.html', restaurants=restaurants)
    else:
        return render_template('restaurants.html', restaurants=restaurants)

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
#    return 'This page will show the menu for restaurant ID %s' %restaurant_id
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    creator = getUserInfo(restaurant.user_id)
    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
    else:
        return render_template('menu.html', items=items, restaurant=restaurant, creator=creator)



@app.route('/restaurant/new', methods = ['GET','POST'])
#    return 'This page will be for creating new restaurant'
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/')
    if request.method == 'POST':
        newRest = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newRest)
        session.commit()
        flash("new restaurant created!")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods = ['GET','POST'])
#   return 'This page will be for editing name of restaurant %s' %restaurant_id
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
          restaurant.name = request.form['name']
          session.add(restaurant)
          session.commit()
          flash("restaurant edited!")
          return redirect(url_for('showRestaurants'))
    else:
      return render_template('editRestaurant.html', restaurant=restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete', methods = ['GET','POST'])
#    return 'This page will be for deleting menu item {0} for restaurant {1} <p> And by the way,<p><h1> Brian is bad Ass!</h1>'.format(menu_id,restaurant_id)
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    restToDel = restaurant.name
    if request.method == 'POST':
      session.delete(restaurant)
      session.commit()
      flash("restaurant deleted!")
      return redirect(url_for('showRestaurants'))
    else:
      return render_template('deleteRestaurant.html', restaurant=restToDel)



@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods = ['GET','POST'])
#    return 'This page will be for adding a bad ass new menu item to restaurant %s' %restaurant_id
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], description=request.form[
                           'description'], price=request.form['price'], course=request.form['course'], restaurant_id=restaurant_id, user_id=restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash ("new menu item created!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant=restaurant)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit', methods = ['GET','POST'])
#    return 'This page will be for editing menu item {0} for restaurant {1} <p> And by the way,<p><h1> Brian is Cool!</h1>'.format(menu_id,restaurant_id)
def editMenuItem(restaurant_id,menu_id):
    if 'username' not in login_session:
        return redirect('/')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['price']:
            item.price = request.form['price']
        if request.form['course']:
            item.course = request.form['course']
        session.add(item)
        session.commit()
        flash("menu item succesfully edited!")
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant =restaurant_id, item=item)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete', methods = ['POST','GET'])
#    return 'This page will be for deleting menu item {0} for restaurant {1} <p> </h1>'.format(menu_id,restaurant_id)
def deleteMenuItem(restaurant_id,menu_id):
    if 'username' not in login_session:
        return redirect('/')
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    itemToDel = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
      session.delete(itemToDel)
      session.commit()
      flash("menu item deleted!")
      return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
      return render_template('deletemenuitem.html', restaurant=restaurant, item=itemToDel)

#  --------------------  API enpoints ------------------------#

@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurant/JSON')
def restaurantJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants=[item.serialize for item in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    menuItem = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(MenuItem=menuItem.serialize)

#  --------------------  User Login via Google OAuth ------------------------#

# Create anti-forgery state token
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
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
    print('code =' + code)

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('./instance/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    print 'in gconnect, access token is %s' % access_token
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
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
    code = request.data

    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    print 'In gdisconnect access token is %s' % access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
 	print 'Access Token is None'
    	response = make_response(json.dumps('Current user not connected.'), 401)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['credentials']
    	del login_session['gplus_id']
    	del login_session['username']
    	del login_session['email']
    	del login_session['picture']
    	response = make_response(json.dumps('Successfully disconnected.'), 200)
    	response.headers['Content-Type'] = 'application/json'
        flash("you are successfully logged out.")
    	return redirect(url_for('showRestaurants'))
    else:

    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response


#  --------------------  Call main  ------------------------#

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)