# iTunes Store
# Multi-language support added by Aqntbghd
# 3.0 API update by ToMM

import countrycode
import json,urllib

# apiary.io debugging URL
# BASE_URL = 'http://private-ad99a-themoviedb.apiary.io/3'

SEARCH_BASE_URL = 'https://itunes.apple.com/search'

ID_BASE_URL = 'https://itunes.apple.com/lookup'

# Movies
ITUNES_STORE_MOVIE_SEARCH = '%s?term=%%s&country=%%s&entity=movie' % (SEARCH_BASE_URL)
ITUNES_STORE_MOVIE = '%s?id=%%s&country=%%s' % (ID_BASE_URL)

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
  #go to fan.tv with the id and parse the page for itunes
  return "421072264"

####################################################################################################
@expose
def GetiTunesIDFromIMDBID(imdb_id):
  #Run the GetTheMovieDBIDFromIMDBID
  #get the movie db id from that api.
  #Run the GetiTunesIDFromTheMovieDBID
  return "421072264"
####################################################################################################
@expose
def GetTheMovieDBIDFromIMDBID(imdb_id):
  #search api of the movie db with the imdb id.

  return "421072264"
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
      imdb_id = RE_IMDB_ID.search(metadata.id)
      itunes_id = GetiTunesIDFromIMDBID(imdb_id)

    elif media.primary_agent == 'com.plexapp.agents.themoviedb':
      moviedb_id = media.primary_metadata.id
      itunes_id = GetiTunesIDFromTheMovieDBID(moviedb_id)

    Log('In the update function with the itunes id of ' + itunes_id)

    itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (itunes_id, countrycode.COUNTRY_TO_CODE[Prefs["country"]]))

    if not isinstance(itunes_store_dict, dict) or 'results' not in itunes_store_dict or len(itunes_store_dict['results']) == 0:
      return None

    itunes_store_dict = itunes_store_dict['results'][0]

    Log(itunes_store_dict)

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
