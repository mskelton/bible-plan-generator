import json
import os


def main():
    dir_name = os.path.dirname(__file__)
    bible_path = os.path.join(dir_name, '..', 'config', 'esv.json')

    with open(bible_path, 'r') as bible_file:
        bible = json.load(bible_file)

    for book in bible.keys():
        for chapter in bible[book].keys():
            length = 0

            for verse in bible[book][chapter].keys():
                length += len(bible[book][chapter][verse].split())

            bible[book][chapter] = length

    # Export the counts
    counts_path = os.path.join(dir_name, '..', 'config', 'esv-counts.json')
    json.dump(bible, open(counts_path, 'w'), indent=4)


if __name__ == "__main__":
    main()
