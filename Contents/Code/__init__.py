# iTunes Store
# Multi-language support added by Aqntbghd
# 3.0 API update by ToMM

import countrycode
import json,urllib,urllib2
import os.path

from HTMLParser import HTMLParser
from urlparse import urlparse
from urlparse import parse_qs

# apiary.io debugging URL
# BASE_URL = 'http://private-ad99a-themoviedb.apiary.io/3'

SEARCH_BASE_URL = 'https://itunes.apple.com/search'

ID_BASE_URL = 'https://itunes.apple.com/lookup'

# Movies
ITUNES_STORE_MOVIE = '%s?id=%%s&country=%%s' % (ID_BASE_URL)
FANTV_MOVIE = 'https://www.fan.tv/movies/%s'

FANTV_TV = 'https://www.fan.tv/shows/%s'

#The Movie DB
API_KEY = 'a3dc111e66105f6387e99393813ae4d5'
THE_MOVIE_DB_BASE_URL = 'https://api.themoviedb.org/3'

THE_MOVIE_DB_IMDB_SEARCH_API = "%s/find/%%s?external_source=imdb_id&api_key=%s" % (THE_MOVIE_DB_BASE_URL, API_KEY)
THE_MOVIE_DB_TV_TVDB = '%s/tv/find/%%s?api_key=%s&external_source=tvdb_id' % (THE_MOVIE_DB_BASE_URL, API_KEY)
THE_MOVIE_DB_TV_SEASON = '%s/tv/%%s/season/%%s?api_key=%s&language=%%s' % (THE_MOVIE_DB_BASE_URL, API_KEY)
THE_MOVIE_DB_TV_IMAGES = '%s/tv/%%s/images?api_key=%s' % (THE_MOVIE_DB_BASE_URL, API_KEY)
THE_MOVIE_DB_TV = '%s/tv/%%s?api_key=%s&append_to_response=credits&language=%%s' % (THE_MOVIE_DB_BASE_URL, API_KEY)

THE_MOVIE_DB_TV_EXTERNAL = "%s/tv/%%s/external_ids?api_key=%s" % (THE_MOVIE_DB_BASE_URL, API_KEY)
THE_MOVIE_DB_MOVIE_EXTERNAL = "%s/movie/%%s/external_ids?api_key=%s" % (THE_MOVIE_DB_BASE_URL, API_KEY)


#Findable
FINDABLE_TV_SEARCH = "http://www.findable.tv/json/getTvSeries?pId=%s"
FINDABLE_TV_SEASON_SEARCH = "http://www.findable.tv/json/getTvSeries?pId=%s&sId=%s"


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
def GetiTunesMovieIDFromTheMovieDBID(the_movie_db_id):
    url = FANTV_MOVIE % (the_movie_db_id)
    Log(url)
    #go to fan.tv with the id and parse the page for itunes
    html = urllib.urlopen(url).read()
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
def GetiTunesMovieIDFromIMDBID(imdb_id):
  #Run the GetTheMovieDBIDFromIMDBID
  the_movie_db_id = GetTheMovieDBIDFromIMDBID(imdb_id)
  #Run the GetiTunesMovieIDFromTheMovieDBID
  return GetiTunesMovieIDFromTheMovieDBID(the_movie_db_id)
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
@expose
def GetFindableJSON(url, cache_time=CACHE_1MONTH):
  findable_dict = None

  try:
    request_headers = {
        "Referer": "http://www.findable.tv",
        "X-Requested-With": "XMLHttpRequest"
    }

    findable_dict = JSON.ObjectFromURL(url, headers=request_headers, sleep=1.0)
  except:
    Log('Error fetching JSON from The URL: ' + url)

  return findable_dict
####################################################################################################
@expose
def GetSelectedFindableTVSeasonJSON(the_tvdb_id, season_id = None):
  json = None

  if season_id is None:
    json = GetFindableJSON(FINDABLE_TV_SEARCH % (the_tvdb_id))
  else:
    json = GetFindableJSON(FINDABLE_TV_SEASON_SEARCH % (the_tvdb_id, season_id))


  if json is not None and "results" in json and len(json["results"]) > 0 and "program" in json["results"][0] and "selectedSeason" in json["results"][0]["program"]:
      return json["results"][0]["program"]["selectedSeason"]

  return None
####################################################################################################
def SearchFindableJSONForSeasonId(findable_seasons, season_number):
  for season in findable_seasons:
      if str(season_number) == str(season['idx']):
          return season["seasonId"]

  return None
####################################################################################################
@expose
def GetiTunesIDForFindableTVSeason(the_tvdb_id, season_id = None):
  selectedSeason = GetSelectedFindableTVSeasonJSON(the_tvdb_id, season_id)

  if selectedSeason is None or "sources" not in selectedSeason or len(selectedSeason["sources"]) == 0:
      return None

  the_source = None

  current_price = 0.0

  for source in selectedSeason["sources"]:
      if source["siteName"] == "ITUNES_US":
          price = source["price"]
          price = price.replace("$","")
          price = float(price)
          Log(price)
          if price > current_price:
            the_source = source

  if the_source is None:
      for source in selectedSeason["sources"]:
          if source["siteName"] == "ITUNES_US":
              the_source = source
              break

  if the_source is None or "site" not in the_source:
      return None

  iTunesURL = the_source["site"]

  Log(iTunesURL)
  if iTunesURL is None:
      return None

  path = urlparse(iTunesURL).path
  sections = path.split("/")

  baseId = sections[len(sections)-1]

  return baseId.replace("id","")
####################################################################################################
def GetJSON(url, cache_time=CACHE_1MONTH):

  the_json = None

  try:
    data = urllib.urlopen(url).read()
    the_json = json.loads(data)
  except:
    Log('Error fetching JSON from The URL: ' + url)

  return the_json

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

    Log("In the update function")

    itunes_id = None

    if RE_IMDB_ID.search(metadata.id):
      itunes_id = GetiTunesMovieIDFromIMDBID(metadata.id)
      if itunes_id == None:
          return None

    elif media.primary_agent == 'com.plexapp.agents.themoviedb':
      moviedb_id = media.primary_metadata.id
      itunes_id = GetiTunesMovieIDFromTheMovieDBID(moviedb_id)
      if itunes_id is None:
        return None

    Log('In the update function with the itunes id of ' + itunes_id)

    itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (itunes_id, countrycode.COUNTRY_TO_CODE[Prefs["country"]]))

    if not isinstance(itunes_store_dict, dict) or 'results' not in itunes_store_dict or len(itunes_store_dict['results']) == 0:
      return None

    itunes_store_dict = itunes_store_dict['results'][0]

    if Prefs['justartwork'] == False:
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

    if 'artworkUrl100' in itunes_store_dict:
        url = itunes_store_dict['artworkUrl100']
        previewURL = itunes_store_dict['artworkUrl100']
        if "100x100bb-85" in itunes_store_dict['artworkUrl100']:
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "4000x4000bb-100")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "1000x1000bb-100")
        elif "100x100bb" in itunes_store_dict['artworkUrl100']:
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "4000x4000bb")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")
        else:
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "4000x4000bb")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")

        valid_names.append(url)

        if url not in metadata.posters:
            try: metadata.posters[url] = Proxy.Preview(HTTP.Request(previewURL).content, sort_order=1)
            except:
                try:
                    metadata.posters[itunes_store_dict['artworkUrl100']] = Proxy.Preview(HTTP.Request(itunes_store_dict['artworkUrl100']).content, sort_order=100)
                    valid_names.append(itunes_store_dict['artworkUrl100'])
                except:
                  pass
    metadata.posters.validate_keys(valid_names)

####################################################################################################
class iTunesStoreAgent(Agent.TV_Shows):

  name = 'iTunes Store'
  languages = LANGUAGES
  contributes_to = ['com.plexapp.agents.thetvdb', 'com.plexapp.agents.themoviedb']
  primary_provider = False

  def search(self, results, media, lang, manual):

    # If search is initiated by a different, primary metadata agent.
    # This requires to set the primary id
    if media.primary_metadata:
        # If TMDB is used as a secondary agent for TVDB, find the TMDB id
        if media.primary_agent == 'com.plexapp.agents.thetvdb':
          tmdb_dict = GetJSON(url=THE_MOVIE_DB_TV_TVDB % (media.primary_metadata.id))

          if isinstance(tmdb_dict, dict) and 'tv_results' in tmdb_dict and len(tmdb_dict['tv_results']) > 0:
            tmdb_id = tmdb_dict['tv_results'][0]['id']

            results.Append(MetadataSearchResult(
              id = str(tmdb_id),
              score = 100
            ))

          return
        else:
          results.Append(MetadataSearchResult(
              id = media.primary_metadata.id,
              score = 100
          ))

  def update(self, metadata, media, lang):

    Log("In the update function")

    # Get the TVDB id from the Movie Database Agent
    tvdb_id = Core.messaging.call_external_function(
        'com.plexapp.agents.themoviedb',
        'MessageKit:GetTvdbId',
        kwargs = dict(
            tmdb_id = metadata.id
        )
    )

    Log("The TV DB Id: " + tvdb_id)

    if tvdb_id is None:
        return None

    json = GetFindableJSON(FINDABLE_TV_SEARCH % (tvdb_id))

    if json is None or "results" not in json or len(json["results"]) == 0:
        return None

    program = json["results"][0]

    if "program" in program:
        program = program["program"]
    else:
        return None

    findable_seasons = None

    if "seasons" in program and len(program["seasons"]):
        findable_seasons = program["seasons"]
    else:
        return None

    itunesID = GetiTunesIDForFindableTVSeason(tvdb_id)

    itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (itunesID, countrycode.COUNTRY_TO_CODE[Prefs["country"]]))

    if isinstance(itunes_store_dict, dict) and 'results' in itunes_store_dict and len(itunes_store_dict['results']) > 0:
        itunes_store_dict = itunes_store_dict['results'][0]

        # Season poster.
        valid_names = list()

        if 'artworkUrl100' in itunes_store_dict:
            url = itunes_store_dict['artworkUrl100']
            previewURL = itunes_store_dict['artworkUrl100']
            if "100x100bb-85" in itunes_store_dict['artworkUrl100']:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "4000x4000bb-100")
                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "1000x1000bb-100")
            elif "100x100bb" in itunes_store_dict['artworkUrl100']:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "4000x4000bb")
                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")
            else:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "4000x4000bb")
                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")

            valid_names.append(url)

            if url not in metadata.posters:
                try: metadata.posters[url] = Proxy.Preview(HTTP.Request(previewURL).content, sort_order=1)
                except:
                    try:
                        metadata.posters[itunes_store_dict['artworkUrl100']] = Proxy.Preview(HTTP.Request(itunes_store_dict['artworkUrl100'], sleep=0.5).content, sort_order=100)
                        valid_names.append(itunes_store_dict['artworkUrl100'])
                    except:
                      pass
        metadata.posters.validate_keys(valid_names)

    # Get episode data.
    @parallelize
    def UpdateEpisodes():

      # Loop over seasons.
      for s in media.seasons:
        season = metadata.seasons[s]


        # Set season metadata.
        @task
        def UpdateSeason(season=season, s=s):

            seasonId = SearchFindableJSONForSeasonId(findable_seasons, s)
            if seasonId is None:
                return None

            Log("Season ID: " + seasonId)

            itunesID = GetiTunesIDForFindableTVSeason(tvdb_id, seasonId)

            Log("iTunes ID: " + itunesID)

            itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (itunesID, countrycode.COUNTRY_TO_CODE[Prefs["country"]]))

            if not isinstance(itunes_store_dict, dict) or 'results' not in itunes_store_dict or len(itunes_store_dict['results']) == 0:
              return None

            itunes_store_dict = itunes_store_dict['results'][0]

            Log(itunes_store_dict)

            if Prefs['justartwork'] == False:
                season.summary = itunes_store_dict['longDescription']

            # Season poster.
            valid_names = list()

            if 'artworkUrl100' in itunes_store_dict:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "20000x20000bb-100")

                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "1000x1000bb-85")

                valid_names.append(url)

                if url not in metadata.posters:
                    try: season.posters[url] = Proxy.Preview(HTTP.Request(previewURL).content, sort_order=1)
                    except:
                        try:
                            season.posters[itunes_store_dict['artworkUrl100']] = Proxy.Preview(HTTP.Request(itunes_store_dict['artworkUrl100'], sleep=0.5).content, sort_order=100)
                            valid_names.append(itunes_store_dict['artworkUrl100'])
                        except:
                          pass
            season.posters.validate_keys(valid_names)


class iTunesParser(HTMLParser):

  def __init__(self):
    HTMLParser.__init__(self)
    self.recording = 0
    self.iTunesURL = None
  def handle_starttag(self, tag, attrs):
    if tag == 'a':
      foundiTunes = False
      for name, value in attrs:
        if name == 'track-context' and "itunes" in value.lower():
          foundiTunes = True
      if foundiTunes:
        for name, value in attrs:
            if name == 'href':
                self.iTunesURL = value