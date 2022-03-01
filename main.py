import pandas as pd

if __name__ == "__main__":
    metadata = pd.read_csv('datasets/movies_metadata.csv', low_memory=False, header=0)
    metadata['id'] = metadata['id'].astype(str)
    keywords = pd.read_csv('datasets/keywords.csv', header=0)
    keywords['id'] = keywords['id'].astype(str)

    pd.merge(metadata, keywords, on='id', how='inner')
