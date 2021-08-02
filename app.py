#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler, log
from flask_wtf import FlaskForm as Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
from Models import db, Venue, Artist, Show


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  cities = db.session.query(Venue.city).distinct().all()
  data = []
  for c in cities:
    item = {"city": c.city}
    venue = Venue.query.filter_by(city = c.city).first()
    item["state"] = venue.state
    venues = []
    all_venues = Venue.query.filter_by(city = c.city).all()
    shows_counter = 0
      
    for v in all_venues:
      venue = {}
      venue["id"] = v.id
      venue["name"] = v.name
      venue["num_upcoming_shows"] = shows_counter
      shows_counter += 1
      venues.append(venue)
      
    item["venues"] = venues
    data.append(item)
  
  return render_template('pages/venues.html', areas=data)



@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.values['search_term']
  venues = db.session.query(Venue).filter(func.lower(Venue.name).contains(search_term.lower(), autoescape=True)).all()
  
  count = 0 
  data = []
  
  for venue in venues:
    v = {}
    v["id"] = venue.id
    v["name"] = venue.name
    v["num_upcoming_shows"] = count
    count += 1
    data.append(v)

  response={
    "count": count,
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  data = {}

  data["id"] = venue.id
  data["name"] = venue.name
  data["city"] = venue.city
  data["state"] = venue.state
  data["address"] = venue.address
  data["phone"] = venue.phone
  data["image_link"] = venue.image_link
  data["facebook_link"] = venue.facebook_link
  data["genres"] = venue.genres
  data["website"] = venue.website
  data["seeking_talent"] = venue.seeking_talent
  data["seeking_description"] = venue.seeking_description
  
  data["past_shows"] = []
  past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.date_time<datetime.now()).all()

  for show in past_shows:
    item = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.date_time)
    }
    data["past_shows"].append(item)


  data["upcoming_shows"] = []
  upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.date_time>datetime.now()).all()

  for show in upcoming_shows:
    item = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.date_time)
    }
    data["upcoming_shows"].append(item)
  
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():  
  try:
    print(request.form)
    
    seeking_talent = False
    if (request.form.keys().__contains__(seeking_talent)):
      seeking_talent = True
    
    seeking_description = ""
    if (request.form.keys().__contains__(seeking_description)):
      seeking_description = request.form["seeking_description"]

    genres = request.form.getlist('genres')

    venue = Venue(name=request.form['name'] ,city=request.form['city'] ,state=request.form['state'] ,address=request.form['address'] ,phone=request.form['phone'] ,image_link=request.form['image_link'] ,facebook_link=request.form['facebook_link'] ,genres=genres ,website=request.form['website_link'] ,seeking_talent=seeking_talent ,seeking_description=seeking_description )
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    db.session.close()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  Venue.query.filter_by(id=venue_id).delete()
  db.session.commit()
  return redirect('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []

  for a in artists:
    item = {"id": a.id,
            "name": a.name
            }
    data.append(item)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.values['search_term']
  artists = db.session.query(Artist).filter(func.lower(Artist.name).contains(search_term.lower(), autoescape=True)).all()
  
  count = 0 
  data = []
  
  for artist in artists:
    a = {}
    a["id"] = artist.id
    a["name"] = artist.name
    a["num_upcoming_shows"] = count
    count += 1
    data.append(a)

  response={
    "count": count,
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  data={
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

  data["past_shows"] = []
  past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.date_time<datetime.now()).all()

  for show in past_shows:
    item = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.date_time)
    }
    data["past_shows"].append(item)


  data["upcoming_shows"] = []
  upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.date_time>datetime.now()).all()

  for show in upcoming_shows:
    item = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.date_time)
    }
    data["upcoming_shows"].append(item)
  
  data["past_shows_count"] = len(data["past_shows"])
  data["upcoming_shows_count"] = len(data["upcoming_shows"])
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  data={
    "id": artist.id,
    "name": artist.name,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "genres": artist.genres,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  try:
    artist = Artist.query.get(artist_id)
    
    seeking_talent = False
    if (request.form.keys().__contains__(seeking_talent)):
      seeking_talent = True
    
    seeking_description = ""
    if (request.form.keys().__contains__(seeking_description)):
      seeking_description = request.form["seeking_description"]

    genres = request.form.getlist('genres')

    artist.name=request.form['name'] 
    artist.city=request.form['city'] 
    artist.state=request.form['state'] 
    artist.phone=request.form['phone'] 
    artist.image_link=request.form['image_link'] 
    artist.facebook_link=request.form['facebook_link'] 
    artist.genres=genres 
    artist.website=request.form['website_link'] 
    artist.seeking_venue=seeking_talent 
    artist.seeking_description=seeking_description
    
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    db.session.close()    
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')  


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  data = {}

  data["id"] = venue.id
  data["name"] = venue.name
  data["city"] = venue.city
  data["state"] = venue.state
  data["address"] = venue.address
  data["phone"] = venue.phone
  data["image_link"] = venue.image_link
  data["facebook_link"] = venue.facebook_link
  data["genres"] = venue.genres
  data["website"] = venue.website
  data["seeking_talent"] = venue.seeking_talent
  data["seeking_description"] = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.get(venue_id)

  try:
    venue = Venue.query.get(venue_id)
    
    seeking_talent = False
    if (request.form.keys().__contains__(seeking_talent)):
      seeking_talent = True
    
    seeking_description = ""
    if (request.form.keys().__contains__(seeking_description)):
      seeking_description = request.form["seeking_description"]

    genres = request.form.getlist('genres')

    venue.name=request.form['name'] 
    venue.city=request.form['city'] 
    venue.state=request.form['state'] 
    venue.address=request.form['address'] 
    venue.phone=request.form['phone'] 
    venue.image_link=request.form['image_link'] 
    venue.facebook_link=request.form['facebook_link'] 
    venue.genres=genres 
    venue.website=request.form['website_link'] 
    venue.seeking_talent=seeking_talent 
    venue.seeking_description=seeking_description
    
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    db.session.close()    
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')  

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    
    seeking_venue = False
    if (request.form.keys().__contains__(seeking_venue)):
      seeking_venue = True
    
    seeking_description = ""
    if (request.form.keys().__contains__(seeking_description)):
      seeking_description = request.form["seeking_description"]

    genres = request.form.getlist('genres')

    artist = Artist(name=request.form['name'] ,city=request.form['city'] ,state=request.form['state'] ,phone=request.form['phone'] ,image_link=request.form['image_link'] ,facebook_link=request.form['facebook_link'] ,genres=genres ,website=request.form['website_link'] ,seeking_venue=seeking_venue ,seeking_description=seeking_description )
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    db.session.close()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data = []

  for show in shows:
    artist = Artist.query.get(show.artist_id)
    item = {
      "venue_id": show.venue_id,
      "venue_name": Venue.query.get(show.venue_id).name,
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": str(show.date_time)
    }
    data.append(item)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show(artist_id=request.form['artist_id'] ,venue_id=request.form['venue_id'] ,date_time=format_datetime(request.form['start_time']))
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')  
  except:
    db.session.rollback()
    db.session.close()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
