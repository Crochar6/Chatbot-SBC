import pandas as pd
import ast
import re


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
    print(df.info())

    return df


if __name__ == "__main__":
    database = import_raw()
    while True:
        user_msg = input()
        print(tokenize(user_msg))

