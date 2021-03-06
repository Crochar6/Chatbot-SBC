import pandas as pd
import ast
import re
import json
from os.path import exists
import bot
import constant as const
from KaggleDownloader import KaggleDownloader


def tokenize(message):
    """
    tokenize: Parses the input string into a list of tokens
    Special characters are removed and string is split by the spaces,
    also "'s" are removed from ends of words.
    :param message: String to be tokenized
    :return: List of tokens
    """
    # Eliminate unwanted characters
    regex_delete = re.compile('[,.!?+*\\/^()=`´#%|]|(-related(?=\s|$))')
    regex_space = re.compile('\'s(\s+|$)') # Search for " 's " and remove them
    message = regex_delete.sub('', message)
    message = regex_space.sub(' ', message)
    # Tokenization
    message = message.lower()
    message = message.split()
    return message


def import_raw():
    """
    import_raw: Creates a unified dataset
    Partial csv are cleaned and merged, many values are evaluated
    to turn them into python objects like lists and dictionaries.
    Some columns are duplicated as a unique set of values, to
    enable faster search.
    :return: Resulting dataframe
    """
    if not exists('datasets/movies_data.pkl'):
        print("Creating movies dataframe using csv files...")
        # Import datasets
        kaggle_downloader = KaggleDownloader('kaggle.json')
        if not exists('datasets/movies_metadata.csv') or not exists('datasets/keywords.csv') or not exists('datasets/credits.csv'):
            kaggle_downloader.download('rounakbanik/the-movies-dataset', 'datasets')
            
        metadata = pd.read_csv('datasets/movies_metadata.csv',
                               usecols=['id', 'title', 'original_title', 'genres', 'vote_average', 'vote_count', 'original_language',
                                        'runtime', 'release_date', 'overview'],
                               header=0,
                               converters={3: ast.literal_eval},)    # Reformat String -> List of Dictionaries
        metadata['id'] = metadata['id'].astype(str)
        keywords = pd.read_csv('datasets/keywords.csv',
                               header=0,
                               converters={1: ast.literal_eval})
        keywords['id'] = keywords['id'].astype(str)
        credits = pd.read_csv('datasets/credits.csv',
                               header=0,
                               converters={0: ast.literal_eval, 1: ast.literal_eval, 2: ast.literal_eval})
        credits['id'] = credits['id'].astype(str)

        # Create merged database
        tmp = pd.merge(metadata, keywords, on='id', how='inner')
        df = pd.merge(tmp, credits, on='id', how='inner')

        # Clean data (remove null rows)
        df.dropna(inplace=True)

        # Map to sets
        df['genres_set'] = df['genres'].map(lambda genres: set([dict['name'] for dict in genres]))
        df['cast_set'] = df['cast'].map(lambda cast: set([dict['name'] for dict in cast]))
        df['crew_set'] = df['crew'].map(lambda crew: set([dict['name'] for dict in crew]))
        df['keywords_set'] = df['keywords'].map(lambda keywords: set([dict['name'] for dict in keywords]))

        # Calculate initial likeness based on vote_average
        df['likeness'] = 0
        vote_count_mean = df['vote_count'].mean()                                               # Average votes
        validity_threshold = 2/3                                                                # % of votes relating to the average needed for score to be valid
        df.loc[df['vote_count'] > vote_count_mean * validity_threshold, 'likeness'] = df['vote_average']     # Initial likeness for movies with sufficient vote_counts
        vote_average_mean = df.loc[df['likeness'] > 0, 'vote_average'].mean()                   # Calculate average score for valid movies
        df.loc[df['likeness'] == 0, 'likeness'] = vote_average_mean                             # Assign average score for insufficiently voted movies
        print(f'Imported {len(df)} movies')

        # Save data
        df.to_pickle('datasets/movies_data.pkl')
        
        kaggle_downloader.delete('rounakbanik/the-movies-dataset', 'datasets') # if you haven't downloaded anything it won't delete anything

    # Read saved info
    movies_df = pd.read_pickle('datasets/movies_data.pkl')
    # Stats
    # print(movies_df.info())

    return movies_df


def import_keywords():
    """
    import_keywords: Loads the keywords.json file
    :return: Json data
    """
    with open('datasets/keywords.json') as f:
        data = json.load(f)
    return data


def import_responses():
    """
    import_responses: Loads the bot-responses.json file
    :return: Json data
    """
    with open('datasets/bot_responses.json') as f:
        data = json.load(f)
    return data


def identify_genre(genres, message):
    """
    identify_genre: Detects genres and keywords from a list of tokens
    :param genres: Json genre keyword data
    :param message: List of tokens
    :return: Set of genres, set of keywords
    """
    result_genres = set([])
    result_keywords = set([])
    for token in message:
        for genre in genres['keywords']['genres']:
            for keyword in genre['keywords']:
                if token == keyword or token == keyword + "s" or token == keyword + "es":
                    result_keywords.add(keyword)
                    # "extra" category for keywords with no genre
                    if genre['name'] != 'extra':
                        result_genres.add(genre['name'])
    return result_genres, result_keywords


def identify_persons(person_set, message):
    """
    identify_persons: Identifies 2 token names inside a list of tokens
    :param person_set: Set of possible names
    :param message: List of tokens
    :return: Set of found names
    """
    found_names = set([])
    for i in range(len(message)-1):
        name_candidate = message[i]+' '+message[i+1]
        if name_candidate in person_set:
            found_names.add(name_candidate)
    return found_names


def generate_person_list(df):
    """
    generate_person_list: Generates a file of relevant persons
    from every movie, both from crew and cast
    :param df: Dataframe with movie info
    :return: Set of unique person names
    """
    if not exists('datasets/persons.txt'):
        print("Creating person name list using database data...")
        person_set = set([])
        for row in df.itertuples():
            for role in row.cast:
                person_set.add(role['name'])
            for role in row.crew:
                job = role['job']
                if job == 'Producer' or job == 'Director' or job == 'Music' \
                        or job == 'Original Music Composer' or job == 'Original Story' \
                        or job == 'Director of Photography' or job == 'Writer' \
                        or job == 'Co-Writer':
                    person_set.add(role['name'].lower())

        with open('datasets/persons.txt', 'w', encoding="utf-8") as f:
            f.write(str(sorted(person_set)))

    with open('datasets/persons.txt', 'r', encoding="utf-8") as f:
        return ast.literal_eval(f.read())


def punctuate_genres(df, genres, weight):
    """
    punctuate_genres: Increases the "likeness" of movies with
    the specified genre
    :param df: Dataframe with movie info
    :param genres: Set of genres to identify
    :param weight: Value to increment likeness by
    :return: Number of moves modified
    """
    #print('punctuate_genres')
    incremented = 0
    if len(genres) > 0:
        for index, row in df.iterrows():
            if len(row['genres_set'].intersection(genres)) > 0:
                df.loc[index, 'likeness'] += weight
                incremented += 1
    return incremented


def punctuate_keywords(df, keywords, weight):
    """
    punctuate_genres: Increases the "likeness" of movies with
    the specified keywords in the 'keywords' column or inside
    their 'overview'.
    :param df: Dataframe with movie info
    :param keywords: Set of keywords to identify
    :param weight: Value to increment likeness by
    :return: Number of moves modified
    """
    #print('punctuate_keywords')
    incremented = 0
    if len(keywords) > 0:
        for index, row in df.iterrows():
            if len(row['keywords_set'].intersection(keywords)) > 0 or \
                    any([word in row['overview'] for word in keywords]):    # Search keywords inside
                df.loc[index, 'likeness'] += weight
                incremented += 1
    return incremented


def punctuate_persons(df, persons, weight):
    """
    punctuate_persons: Increases the "likeness" of movies with
    the specified persons
    :param df: Dataframe with movie info
    :param persons: Set of persons to identify
    :param weight: Value to increment likeness by
    :return: Number of moves modified
    """
    #print('punctuate_persons')
    incremented = 0
    if len(persons) > 0:
        for index, row in df.iterrows():
            if len(row['cast_set'].intersection(persons)) > 0 or len(row['crew_set'].intersection(persons)) > 0:
                df.loc[index, 'likeness'] += weight
                incremented += 1
    return incremented


def punctuate_language(df, languages, weight):
    """
    punctuate_language: Increases the "likeness" of movies with
    the specified original language
    :param df: Dataframe with movie info
    :param languages: Set of languages to punctuate
    :param weight: Value to increment likeness by
    :return: Number of moves modified
    """
    #print('punctuate_language')
    incremented = 0
    if len(languages) > 0:
        for language in languages:
            incremented += len(df.loc[df['original_language'] == language])
            df.loc[df['original_language'] == language, 'likeness'] += weight
    return incremented


def punctuate_movies(df, titles, weight):
    """
    punctuate_movies: Increases the "likeness" of movies with
    the specified title, either the original one or translated to english
    :param df: Dataframe with movie info
    :param titles: Set of titles to punctuate
    :param weight: Value to increment likeness by
    :return: Number of moves modified
    """
    #print('punctuate_movies')
    incremented = 0
    if len(titles) > 0:
        for title in titles:
            incremented += len(df.loc[(df[['original_title', 'title']] == title).any(axis=1)])
            df.loc[(df[['original_title', 'title']] == title).any(axis=1), 'likeness'] += weight
    return incremented


def get_top_n_movies(df, n):
    """
    get_top_n_movies: Returns the top n movies based
    on the 'likeness' score
    :param df: Dataframe with movie info
    :param n: Number of movies to retrieve
    :return: Number of moves modified
    """
    return df.sort_values('likeness', ascending=False).head(n)


if __name__ == "__main__":
    database = import_raw()
    persons = generate_person_list(database)
    keywords = import_keywords()
    responses = import_responses()
    bot = bot.Bot(responses)
    print('Initialization complete!')
    print('You can begin talking with the bot!')
    user_msg = ''
    while user_msg != ['end']:
        user_msg = input()
        user_msg = tokenize(user_msg)
        msg_genres, msg_keywords = identify_genre(keywords, user_msg)
        msg_names = identify_persons(persons, user_msg)
        punctuate_genres(database, msg_genres, const.GENRE_WEIGHT)
        # print(f'Genres: {msg_genres}, Keywords: {msg_keywords}, Person names: {msg_names}')
        bot.increment_information(len({*msg_names, *msg_genres, *msg_keywords}))
        bot_answer, should_end = bot.calculate_response(user_msg, msg_keywords, msg_names, [])  # TODO: buscar noms de pel·lis
        print(bot_answer)
        punctuate_persons(database, msg_names, const.PERSON_WEIGHT)
        punctuate_keywords(database, msg_keywords, const.KEYWORD_WEIGHT)
        if should_end:
            break
    print(get_top_n_movies(database, 5)[['title', 'likeness']])
