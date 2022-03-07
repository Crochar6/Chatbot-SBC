import pandas as pd


def import_raw():
    metadata = pd.read_csv('datasets/movies_metadata.csv',
                           usecols=['id', 'title', 'genres', 'vote_average', 'vote_count', 'original_language',
                                    'runtime', 'release_date', 'overview'],
                           header=0)
    metadata['id'] = metadata['id'].astype(str)
    keywords = pd.read_csv('datasets/keywords.csv', header=0)
    keywords['id'] = keywords['id'].astype(str)

    df = pd.merge(metadata, keywords, on='id', how='inner')

    return df


if __name__ == "__main__":
    database = import_raw()
    print(database.info())
