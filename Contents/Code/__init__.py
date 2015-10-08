# iTunes Store
# Multi-language support added by Aqntbghd
# 3.0 API update by ToMM

import countrycode
import json,urllib

from urllib2 import urlopen
from HTMLParser import HTMLParser
from urlparse import urlparse
from urlparse import parse_qs

# apiary.io debugging URL
# BASE_URL = 'http://private-ad99a-themoviedb.apiary.io/3'

SEARCH_BASE_URL = 'https://itunes.apple.com/search'

ID_BASE_URL = 'https://itunes.apple.com/lookup'

# Movies
ITUNES_STORE_MOVIE_SEARCH = '%s?term=%%s&country=%%s&entity=movie' % (SEARCH_BASE_URL)
ITUNES_STORE_MOVIE = '%s?id=%%s&country=%%s' % (ID_BASE_URL)
FANTV_MOVIE = 'https://www.fan.tv/movies/%s'



#The Movie DB
THE_MOVIE_DB_IMDB_SEARCH_API = "https://api.themoviedb.org/3/find/%s?external_source=imdb_id&api_key=2798bf23aa9f616f20c1b1e212b2de8f"

LANGUAGES = [
             Locale.Language.English, Locale.Language.Czech, Locale.Language.Danish, Locale.Language.German,
             Locale.Language.Greek, Locale.Language.Spanish, Locale.Language.Finnish, Locale.Language.French,
             Locale.Language.Hebrew, Locale.Language.Croatian, Locale.Language.Hungarian, Locale.Language.Italian,
             Locale.Language.Latvian, Locale.Language.Dutch, Locale.Language.Norwegian, Locale.Language.Polish,
             Locale.Language.Portuguese, Locale.Language.Russian, Locale.Language.Slovak, Locale.Language.Swedish,
             Locale.Language.Thai, Locale.Language.Turkish, Locale.Language.Vietnamese, Locale.Language.Chinese,
             Locale.Language.Korean
            ]

RE_IMDB_ID = Regex('^tt\d{7}$')

####################################################################################################
def Start():

  pass

####################################################################################################
@expose
def GetiTunesIDFromTheMovieDBID(the_movie_db_id):
    url = FANTV_MOVIE % (the_movie_db_id)
    Log(url)
    #go to fan.tv with the id and parse the page for itunes
    html = urlopen(url).read()
    p = iTunesParser()
    p.feed(html)
    iTunesURL = p.iTunesURL
    p.close()
    Log(iTunesURL)
    if iTunesURL is None:
        return None

    parsed_result = urlparse(iTunesURL)
    result = parse_qs(parsed_result.query)

    if "id" in result:
        return result['id'][0]

    return None

####################################################################################################
@expose
def GetiTunesIDFromIMDBID(imdb_id):
  #Run the GetTheMovieDBIDFromIMDBID
  the_movie_db_id = GetTheMovieDBIDFromIMDBID(imdb_id)
  #Run the GetiTunesIDFromTheMovieDBID
  return GetiTunesIDFromTheMovieDBID(the_movie_db_id)
####################################################################################################
@expose
def GetTheMovieDBIDFromIMDBID(imdb_id):
  #search api of the movie db with the imdb id.
  the_movie_dict = GetJSON(url=THE_MOVIE_DB_IMDB_SEARCH_API % (imdb_id))

  Log(THE_MOVIE_DB_IMDB_SEARCH_API % (imdb_id))

  if not isinstance(the_movie_dict, dict) or 'movie_results' not in the_movie_dict or len(the_movie_dict['movie_results']) == 0:
    Log('No Results from the movie db')
    return None

  the_movie_dict = the_movie_dict['movie_results'][0]
  the_movie_db_id = the_movie_dict['id']

  return the_movie_db_id
####################################################################################################
def GetJSON(url, cache_time=CACHE_1MONTH):

  itunes_store_dict = None

  try:
    data = urllib.urlopen(url).read()
    itunes_store_dict = json.loads(data)
  except:
    Log('Error fetching JSON from The URL: ' + url)

  return itunes_store_dict

####################################################################################################
class iTunesStoreAgent(Agent.Movies):

  name = 'iTunes Store'
  languages = LANGUAGES
  contributes_to = ['com.plexapp.agents.imdb', 'com.plexapp.agents.themoviedb']
  primary_provider = False

  def search(self, results, media, lang, manual):

    Log('In the search function!!!!!!')

    # If search is initiated by a different, primary metadata agent.
    # This requires to set the primary id
    if media.primary_metadata:
      results.Append(MetadataSearchResult(
          id = media.primary_metadata.id,
          score = 100
      ))

  #####################################################

  def update(self, metadata, media, lang):

    itunes_id = None

    if RE_IMDB_ID.search(metadata.id):
      itunes_id = GetiTunesIDFromIMDBID(metadata.id)
      if itunes_id == None:
          return None

    elif media.primary_agent == 'com.plexapp.agents.themoviedb':
      moviedb_id = media.primary_metadata.id
      itunes_id = GetiTunesIDFromTheMovieDBID(moviedb_id)
      if itunes_id is None:
        return None

    Log('In the update function with the itunes id of ' + itunes_id)

    itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (itunes_id, countrycode.COUNTRY_TO_CODE[Prefs["country"]]))

    if not isinstance(itunes_store_dict, dict) or 'results' not in itunes_store_dict or len(itunes_store_dict['results']) == 0:
      return None

    itunes_store_dict = itunes_store_dict['results'][0]

    # Title of the film.
    metadata.title = itunes_store_dict['trackName']

    # Release date.
    try:
      metadata.originally_available_at = Datetime.ParseDate(itunes_store_dict['releaseDate']).date()
      metadata.year = metadata.originally_available_at.year
    except:
      pass

    # Content rating.
    if itunes_store_dict['country'].lower() == "usa":
      metadata.content_rating = itunes_store_dict['contentAdvisoryRating']
    else:
      metadata.content_rating = '%s/%s' % (itunes_store_dict['country'].lower(), itunes_store_dict['contentAdvisoryRating'])


    # Summary.
    metadata.summary = itunes_store_dict['longDescription']

    # Runtime.
    try: metadata.duration = int(itunes_store_dict['trackTimeMillis']) * 60 * 1000
    except: pass

    # Genres.
    metadata.genres.clear()
    metadata.genres.add(itunes_store_dict['primaryGenreName'].strip())

    # Collections.
    metadata.collections.clear()
    if Prefs['collections'] and 'collectionName' in itunes_store_dict:
      metadata.collections.add(itunes_store_dict['collectionName'])

    valid_names = list()

    if 'artworkUrl100' in itunes_store_dict['artworkUrl100']:
        url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "2000x2000bb-100")

        if url not in metadata.posters:
            try:
                metadata.posters[url] = Proxy.Preview(HTTP.Request(url, sleep=0.5).content, sort_order=100)
                valid_names.append(url)
            except:
                try:
                    metadata.posters[itunes_store_dict['artworkUrl100']] = Proxy.Preview(HTTP.Request(itunes_store_dict['artworkUrl100'], sleep=0.5).content, sort_order=1)
                    valid_names.append(itunes_store_dict['artworkUrl100'])
                except:
                  pass

    metadata.posters.validate_keys(valid_names)

####################################################################################################



class iTunesParser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.iTunesURL = None
  def handle_starttag(self, tag, attrs):
    if tag == 'a':
      foundiTunes = False
      for name, value in attrs:
        if name == 'data-tooltip' and value == 'iTunes':
          foundiTunes = True
      if foundiTunes:
        for name, value in attrs:
            if name == 'href':
                self.iTunesURL = value