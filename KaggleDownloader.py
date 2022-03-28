import os
import json

class KaggleDownloader:
    def __init__(self, path):
        with open(path) as file:
            data = json.load(file)
            os.environ['KAGGLE_USERNAME'] = data['username']
            os.environ['KAGGLE_KEY'] = data['key']
    
    def download(self, dataset, target):
        """
        download: Downloads a Kaggle dataset
        :param dataset: Name of the dataset
        :param target: Path where to store the files
        """
        from kaggle.api.kaggle_api_extended import KaggleApi # that's why we need if __name__ == '__main__'...
        
        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(dataset, path=target, unzip=True)