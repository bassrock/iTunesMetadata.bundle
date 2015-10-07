# iTunes Store
# Multi-language support added by Aqntbghd
# 3.0 API update by ToMM

import countrycode

# apiary.io debugging URL
# BASE_URL = 'http://private-ad99a-themoviedb.apiary.io/3'

SEARCH_BASE_URL = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch'

ID_BASE_URL = 'https://itunes.apple.com/lookup'

# Movies
ITUNES_STORE_MOVIE_SEARCH = '%s?term=%%s&country=%s&entity=movie' % (SEARCH_BASE_URL, "us")
ITUNES_STORE_MOVIE = '%s?id=%%s&country=%s' % (ID_BASE_URL, "us")

LANGUAGES = [
             Locale.Language.English, Locale.Language.Czech, Locale.Language.Danish, Locale.Language.German,
             Locale.Language.Greek, Locale.Language.Spanish, Locale.Language.Finnish, Locale.Language.French,
             Locale.Language.Hebrew, Locale.Language.Croatian, Locale.Language.Hungarian, Locale.Language.Italian,
             Locale.Language.Latvian, Locale.Language.Dutch, Locale.Language.Norwegian, Locale.Language.Polish,
             Locale.Language.Portuguese, Locale.Language.Russian, Locale.Language.Slovak, Locale.Language.Swedish,
             Locale.Language.Thai, Locale.Language.Turkish, Locale.Language.Vietnamese, Locale.Language.Chinese,
             Locale.Language.Korean
            ]

####################################################################################################
def Start():

  pass

####################################################################################################


####################################################################################################
def GetJSON(url, cache_time=CACHE_1MONTH):

  itunes_store_dict = None

  try:
    itunes_store_dict = JSON.ObjectFromURL(url, sleep=2.0, headers={'Accept': 'application/json'}, cacheTime=cache_time)
  except:
    Log('Error fetching JSON from The iTunes Store.')

  return itunes_store_dict

####################################################################################################
class iTunesStoreAgent(Agent.Movies):

  name = 'iTunes Store'
  primary_provider = True
  languages = LANGUAGES
  accepts_from = ['com.plexapp.agents.localmedia']
  contributes_to = ['com.plexapp.agents.imdb']

  def search(self, results, media, lang, manual):

    # If search is initiated by a different, primary metadata agent.
    # This requires the other agent to use the itunes id as key.
    if media.primary_metadata is not None:
      results.Append(MetadataSearchResult(
        id = media.primary_metadata.id,
        score = 100
      ))
    else:
      # If this a manual search (Fix Incorrect Match). We then pass the itunes id
      if manual:
        itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (media.primary_metadata.id))

        if isinstance(itunes_store_dict, dict) and 'results' in itunes_store_dict and len(itunes_store_dict['results']) == 1:

          ourresult = itunes_store_dict['results'][0]

          results.Append(MetadataSearchResult(
            id = str(ourresult['trackId']),
            name = ourresult['trackName'],
            year = int(ourresult['releaseDate'].split('-')[0]),
            score = 100,
            lang = lang
          ))

      # If this is an automatic search and iTunes Store agent is used as a primary agent.
      else:
        if media.year and int(media.year) > 1900:
          year = media.year
        else:
          year = ''

        include_adult = 'false'
        if Prefs['adult']:
          include_adult = 'true'

        # Historically we've StrippedDiacritics() here, but this is a pretty aggressive function that won't pass
        # anything that can't be encoded to ASCII, and as such has a tendency to nuke whole titles in, e.g., Asian
        # languages (See GHI #26).  If we have a string that was modified by StripDiacritics() and we get no results,
        # try the search again with the original.
        #
        stripped_name = String.StripDiacritics(media.name)
        itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE_SEARCH % (String.Quote(stripped_name)))
        if media.name != stripped_name and (itunes_store_dict == None or len(itunes_store_dict['results']) == 0):
          Log('No results for title modified by strip diacritics, searching again with the original: ' + media.name)
          itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE_SEARCH % (String.Quote(media.name)))

        if isinstance(itunes_store_dict, dict) and 'results' in itunes_store_dict:
          for movie in enumerate(itunes_store_dict['results']):
            score = 90
            score = score - abs(String.LevenshteinDistance(movie['trackName'].lower(), media.name.lower()))

            if 'releaseDate' in movie and movie['releaseDate']:
              release_year = int(movie['releaseDate'].split('-')[0])
            else:
              release_year = None

            if media.year and int(media.year) > 1900 and release_year:
              year_diff = abs(int(media.year) - release_year)

              if year_diff <= 1:
                score = score + 10
              else:
                score = score - (5 * year_diff)

            if score <= 0:
              continue
            else:
              results.Append(MetadataSearchResult(
                id = str(movie['trackId']),
                name = movie['trackName'],
                year = release_year,
                score = score,
                lang = lang
              ))

  def update(self, metadata, media, lang):



    itunes_store_dict = GetJSON(url=ITUNES_STORE_MOVIE % (metadata.id))

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
    metadata.genres.add(itunes_store_dict['trackTimeMillis'].strip())

    # Collections.
    metadata.collections.clear()
    if Prefs['collections'] and itunes_store_dict['collectionName']:
      metadata.collections.add(itunes_store_dict['collectionName'])

    # Note: for TMDB artwork, number of votes is a good predictor of poster quality. Ratings are assigned
    # using a Baysean average that appears to be poorly calibrated, so ratings are almost always between
    # 5 and 6 or zero.  Consider both of these, weighting them according to the POSTER_SCORE_RATIO.

    # No votes get zero, use TMDB's apparent initial Baysean prior mean of 5 instead.
    valid_names = list()

    if itunes_store_dict['artworkUrl100']:
      valid_names.append(itunes_store_dict['artworkUrl100'])

    metadata.posters.validate_keys(valid_names)

####################################################################################################
