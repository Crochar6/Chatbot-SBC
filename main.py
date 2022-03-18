import pandas as pd
import ast
import re
import json
from os.path import exists


def tokenize(message):
    # Eliminate unwanted characters
    regex_delete = re.compile('[,.!?+*/^()=`´#%|]')
    regex_space = re.compile('\'s(\s+|$)') # Search for " 's " and remove them
    message = regex_delete.sub('', message)
    message = regex_space.sub(' ', message)
    # Tokenization
    message = message.lower()
    message = message.split()
    print(message)
    return message


def import_raw():

    if not exists('datasets/movies_data.pkl'):
        print("Creating movies dataframe using csv files...")
        # Import datasets
        metadata = pd.read_csv('datasets/movies_metadata.csv',
                               usecols=['id', 'title', 'genres', 'vote_average', 'vote_count', 'original_language',
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

        # Map to sets
        df['genres_set'] = df['genres'].map(lambda genres: set([dict['name'] for dict in genres]))
        df['cast_set'] = df['cast'].map(lambda cast: set([dict['name'] for dict in cast]))
        df['crew_set'] = df['crew'].map(lambda crew: set([dict['name'] for dict in crew]))
        df['keywords_set'] = df['keywords'].map(lambda keywords: set([dict['name'] for dict in keywords]))

        # Add custom columns
        df['likeness'] = 0

        # Clean data (remove null rows)
        df.dropna(inplace=True)

        # Save data
        df.to_pickle('datasets/movies_data.pkl')

    # Read saved info
    movies_df = pd.read_pickle('datasets/movies_data.pkl')
    # Stats
    # print(movies_df.info())

    return movies_df


def import_keywords():
    with open('datasets/keywords.json') as f:
        data = json.load(f)
    return data


def identify_genre(genres, message):
    result_genres = set([])
    result_keywords = set([])
    for token in message:
        for genre in genres:
            for keyword in genre['keywords']:
                if token == keyword or token == keyword + "s" or token == keyword + "es":
                    result_keywords.add(keyword)
                    # "extra" category for keywords with no genre
                    if genre['name'] != 'extra':
                        result_genres.add(genre['name'])
    return result_genres, result_keywords


def identify_persons(person_set, message):
    found_names = set([])
    for i in range(len(message)-1):
        name_candidate = message[i]+' '+message[i+1]
        if name_candidate in person_set:
            found_names.add(name_candidate)
    return found_names


# Generates "persons.txt" that contains all relevant names
def generate_person_list(df):
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
    incremented = 0
    for index, row in df.iterrows():
        if len(row['genres_set'].intersection(genres)) > 0:
            df.loc[index, 'likeness'] += weight
            incremented += 1
    return incremented


def punctuate_keywords(df, keywords, weight):
    incremented = 0
    for index, row in df.iterrows():
        if len(row['keywords_set'].intersection(keywords)) > 0 or \
                any([word in row['overview'] for word in keywords]):    # Search keywords inside
            df.loc[index, 'likeness'] += weight
            incremented += 1
    return incremented


if __name__ == "__main__":
    database = import_raw()
    persons = generate_person_list(database)
    keywords = import_keywords()
    genre_keywords = keywords['keywords']['genres']
    print('Initialization complete!')
    print(punctuate_genres(database, {'Horror'}, 1))
    print(punctuate_keywords(database, {'fun', 'kids', 'family', 'spirit'}, 1.5))
    while True:
        user_msg = input()
        user_msg = tokenize(user_msg)
        msg_genres, msg_keywords = identify_genre(genre_keywords, user_msg)
        msg_names = identify_persons(persons, user_msg)
        print(f'Genres: {msg_genres}, Keywords: {msg_keywords}, Person names: {msg_names}')
