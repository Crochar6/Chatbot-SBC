import os
from os.path import isfile, join
import json

class KaggleDownloader:
    def __init__(self, path):
        self.files_per_dataset = {}
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
        
        initial_files = [f for f in os.listdir(target) if isfile(join(target, f))]
        
        api.dataset_download_files(dataset, path=target, unzip=True)
        
        if not dataset in self.files_per_dataset:
            self.files_per_dataset[dataset] = []
        self.files_per_dataset[dataset].extend([f for f in os.listdir(target) if isfile(join(target, f)) and f not in initial_files])
    
    def delete(self, dataset, target):
        """
        delete: Delete a Kaggle dataset previously loaded in one folder
        :param dataset: Name of the dataset
        :param target: Path where to store the files
        """
        for file in self.files_per_dataset[dataset]:
            os.remove(join(target, file))