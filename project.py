from flask import Flask, render_template, request, redirect,jsonify, url_for, flash

         #create instance of class Flask

APPLICATION_NAME = "pizzanode"
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(
        SECRET_KEY='dev',
     )


from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User

from flask import session as login_session
import random, string
import connect
app.register_blueprint(connect.bp)



#Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()




#Show all restaurants
@app.route('/')
@app.route('/restaurant/')

def showRestaurants():
    restaurants = session.query(Restaurant).all()
    #print (login_session['user_id'])
    if 'username' not in login_session:
        return render_template('publicrestaurants.html', restaurants=restaurants)
    else:
        return render_template('restaurants.html', restaurants=restaurants)

#Create a new restaurant
@app.route('/restaurant/new/', methods=['GET','POST'])
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

#Edit a restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
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


#Delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
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

#Show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')

def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    c = getUserInfo(restaurant.user_id)
    creator = c.id if c else None


    items = session.query(MenuItem).filter_by(
        restaurant_id=restaurant_id).all()
    if 'username' not in login_session or creator != login_session['user_id']:
        return render_template('publicmenu.html', items=items, restaurant=restaurant, creator=creator)
    else:
        return render_template('menu.html', items=items, restaurant=restaurant, creator=creator)



#Create a new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
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



#Edit a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
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


#Delete a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET','POST'])
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

# ----------------------  User Helper Functions ----------------------------#


# ----------------------  User Helper Functions ----------------------------#

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    #user = session.query(User).filter_by(id=login_session['user_id']).one()
    return login_session['user_id']


def getUserInfo(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except:
        return None
def getUserID(user_id):
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user.id
    except:
        return None





if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
