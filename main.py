import pandas as pd
import ast
import re
import json


def tokenize(message):
    # Eliminate unwanted characters
    regex = re.compile('[,.!?+*/^()=`´#%|]')
    message = regex.sub('', message)
    # Tokenization
    message = message.lower()
    message = message.split()
    return message


def import_raw():
    # Import datasets
    metadata = pd.read_csv('datasets/movies_metadata.csv',
                           usecols=['id', 'title', 'genres', 'vote_average', 'vote_count', 'original_language',
                                    'runtime', 'release_date', 'overview'],
                           header=0,
                           converters={3: ast.literal_eval})    # Reformat String -> List of Dictionaries
    metadata['id'] = metadata['id'].astype(str)
    keywords = pd.read_csv('datasets/keywords.csv',
                           header=0,
                           converters={1: ast.literal_eval})    # Reformat String -> List of Dictionaries
    keywords['id'] = keywords['id'].astype(str)

    # Create merged database
    df = pd.merge(metadata, keywords, on='id', how='inner')

    # Clean data
    df.dropna(inplace=True)

    # Stats
    #print(df.info())

    return df


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
                    result_genres.add(genre['name'])
                    result_keywords.add(keyword)
    return result_genres, result_keywords


if __name__ == "__main__":
    database = import_raw()
    keywords = import_keywords()
    genre_keywords = keywords['keywords']['genres']
    while True:
        user_msg = input()
        user_msg = tokenize(user_msg)
        msg_genres, msg_keywords = identify_genre(genre_keywords, user_msg)
        print(msg_genres, msg_keywords)


