import csv
import itertools
import pandas as pd
import ast

NUM_READ = 4  # Número de línies a llegir del fitxer


if __name__ == "__main__":
    outfile = open("parsed_data.csv", 'w', encoding="utf8")
    outfile_header = "title,language,genres,summary\n"  # Header ha de coincidir amb les dades
    outfile.write(outfile_header)

    with open("datasets/movies_metadata.csv", 'r', encoding="utf8") as infile:
        reader = csv.reader(infile, delimiter=",")
        header = next(reader)
        for row in itertools.islice(reader, NUM_READ):

            # Agafar les dades que volem
            title = row[header.index("original_title")]
            language = row[header.index("original_language")]
            genres = row[header.index("genres")]
            summary = row[header.index("overview")]

            # Escriure al fitxer
            line = f"{title},{language},{genres},{summary}\n"
            outfile.write(line)