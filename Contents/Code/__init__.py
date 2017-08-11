# iTunes Store
# Multi-language support added by Aqntbghd
# 3.0 API update by ToMM

import countrycode
import json,urllib,urllib2,ssl
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
FANTV_MOVIE_API = 'https://api.fan.tv/1.0/metadata/fantv/movies/%s/synonym_ids?access_token=%s'

FANTV_MOVIE = 'https://www.fan.tv/movies/%s'
FANTV_TV = 'https://www.fan.tv/shows/%s'

#The Movie DB
TMDB_BASE_URL = 'http://127.0.0.1:32400/services/tmdb?uri=%s'
TMDB_CONFIG = '/configuration'

TMDB_TV_TVDB = '/find/%s?external_source=tvdb_id'
TMDB_MOVIE_IMDB = "/find/%s?external_source=imdb_id"

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
    ## For now the api needs to be registered and we dont have that.
    # fantvapi = Prefs["fantvapi"]
    #
    # url = FANTV_MOVIE_API % (the_movie_db_id, fantvapi)
    # Log(url)
    #
    # fan_tv_dict = GetJSON(url)
    #
    # if not fan_tv_dict["data"]:
    #     return None
    #
    # for id in fan_tv_dict["data"]:
    #     Log(id["source"])
    #     if "itunes" in id["source"]:
    #         return id['id']["key"]

    url = FANTV_MOVIE % (the_movie_db_id)
    Log(url)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    #go to fan.tv with the id and parse the page for itunes
    html = urllib2.urlopen(url, context=ctx).read()
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
  config_dict = GetTMDBJSON(url=TMDB_CONFIG, cache_time=CACHE_1WEEK * 2)
  if config_dict is None or 'images' not in config_dict or 'base_url' not in config_dict['images']:
    config_dict = dict(images=dict(base_url=''))

  #search api of the movie db with the imdb id.
  tmdb_dict = GetTMDBJSON(url=TMDB_MOVIE_IMDB % (imdb_id))

  Log(TMDB_MOVIE_IMDB % (imdb_id))

  if not isinstance(tmdb_dict, dict) or 'movie_results' not in tmdb_dict or len(tmdb_dict['movie_results']) == 0:
    Log('No Results from the movie db')
    return None

  tmdb_dict = tmdb_dict['movie_results'][0]
  the_movie_db_id = tmdb_dict['id']

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
  dict = None

  try:
   dict = JSON.ObjectFromURL(url, sleep=2.0, headers={'Accept': 'application/json'}, cacheTime=cache_time)
  except:
    Log('Error fetching JSON: %s' % (TMDB_BASE_URL % String.Quote(url, True)))

  return dict

####################################################################################################
def GetTMDBJSON(url, cache_time=CACHE_1MONTH):

  tmdb_dict = None

  try:
    tmdb_dict = JSON.ObjectFromURL(TMDB_BASE_URL % String.Quote(url, True), sleep=2.0, headers={'Accept': 'application/json'}, cacheTime=cache_time)
  except:
    Log('Error fetching JSON from The Movie Database: %s' % (TMDB_BASE_URL % String.Quote(url, True)))

  return tmdb_dict

####################################################################################################
class iTunesStoreAgent(Agent.Movies):

  name = 'iTunes Store'
  languages = LANGUAGES
  contributes_to = ['com.plexapp.agents.imdb']
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
    itunes_id = GetiTunesMovieIDFromIMDBID(metadata.id)
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
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "10000x10000bb-100")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "10000x10000bb-100")
        elif "100x100bb" in itunes_store_dict['artworkUrl100']:
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
        else:
            url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
            previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")

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
          config_dict = GetTMDBJSON(url=TMDB_CONFIG, cache_time=CACHE_1WEEK * 2)
          if config_dict is None or 'images' not in config_dict or 'base_url' not in config_dict['images']:
              config_dict = dict(images=dict(base_url=''))

          tmdb_dict = GetTMDBJSON(url=TMDB_TV_TVDB % (media.primary_metadata.id))

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
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "10000x10000bb-100")
                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "1000x1000bb-100")
            elif "100x100bb" in itunes_store_dict['artworkUrl100']:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
                previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")
            else:
                url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
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
                url = itunes_store_dict['artworkUrl100']
                previewURL = itunes_store_dict['artworkUrl100']
                if "100x100bb-85" in itunes_store_dict['artworkUrl100']:
                    url = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "10000x10000bb-100")
                    previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb-85", "1000x1000bb-100")
                elif "100x100bb" in itunes_store_dict['artworkUrl100']:
                    url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
                    previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")
                else:
                    url = itunes_store_dict['artworkUrl100'].replace("100x100bb", "10000x10000bb")
                    previewURL = itunes_store_dict['artworkUrl100'].replace("100x100bb", "1000x1000bb")

                valid_names.append(url)

            #Change jpg to lsr and we have apple tv parallax images
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