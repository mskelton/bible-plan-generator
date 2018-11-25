import os
import sys
import json
import math
import itertools

from trello import TrelloClient

from books import books

dir_name = os.path.dirname(__file__)
bible_path = os.path.join(dir_name, '..', 'config', 'esv-counts.json')
with open(bible_path, 'r') as bible_file:
    BIBLE = json.load(bible_file)

# Constants
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 90


def get_total_words() -> int:
    total = 0

    # Loop through each book and get to total words
    for book_name in books:
        # Get the book from the bible dict
        book = BIBLE[book_name]
        # Get the total words in this book by summing to totals in each chapter
        total += sum([book[chapter] for chapter in book.keys()])

    return total


def get_numbers(section: dict) -> list:
    return sorted(list(map(lambda key: int(key), section.keys())))


def count_words_in_chapter(book: int, chapter: int) -> int:
    return BIBLE[books[book]][str(chapter)]


def next_chapter(book: int, chapter: int) -> tuple:
    total_chapters = len(BIBLE[books[book]].keys())

    if chapter == total_chapters:
        return (book + 1, 1)

    return (book, chapter + 1)


def previous_chapter(book: int, chapter: int) -> tuple:
    if chapter == 1:
        total_chapters = len(BIBLE[books[book - 1]].keys())
        return (book - 1, total_chapters)

    return (book, chapter - 1)


def get_last_chapter() -> int:
    return len(BIBLE[books[-1]].keys())


def is_last_chapter(book: int, chapter: int) -> bool:
    return book == len(books) - 1 and chapter == get_last_chapter()


def get_day(book: int, chapter: int, words: int, day: int) -> list:
    length = 0
    next_length = count_words_in_chapter(book, chapter)
    readings = []

    while length + next_length < words or day == DAYS - 1:
        # Add the latest words to the total before resetting the next_length
        length += next_length

        # Add this chapter to the readings
        readings.append([book, chapter])

        # Increment the chapter
        book, chapter = next_chapter(book, chapter)

        # Get the next chapter and count the number of words
        next_length = count_words_in_chapter(book, chapter)

        # If this is the last chapter, return
        if is_last_chapter(book, chapter):
            # Add the final reading
            readings.append([book, chapter])

            return readings, book, chapter, length + next_length

    # Find the closer chapter
    if length + next_length - words <= words - length:
        readings.append([book, chapter])
        length += next_length

        # Increment the chapter so we don't read the same chapter twice
        book, chapter = next_chapter(book, chapter)

    # Return the information
    return readings, book, chapter, length


def get_reading(readings: list) -> str:
    groups = []

    # Group the readins by book
    for book, g in itertools.groupby(readings, lambda x: x[0]):
        # Convert the itertools groupby object to a list
        group = list(g)
        # We always have one reading per group, so add it
        reading = f'{books[book]} {group[0][1]}'

        # If there is more than one chapter for this book,
        #   add the last chapter
        if len(group) > 1:
            reading += f'-{group[len(group) - 1][1]}'

        # Add the reading to the groups
        groups.append(reading)

    return ', '.join(groups)


def get_reading_width(readings: list) -> int:
    return max([len(reading) for reading, _ in readings])


def get_greatest_delta(plan: list) -> int:
    # Simplify the plan to just the words per day
    words = [words for _, words in plan]
    # Return the maximun number of words minus the minimum number of words
    return max(words) - min(words)


def print_plan(plan: list) -> None:
    # Print stats
    print(f'Greatest delta: {get_greatest_delta(plan):,}')
    print()

    readings = []

    # Convert the reading indicies to strings
    for r, words in plan:
        readings.append([get_reading(r), words])

    # Print header row
    reading_width = get_reading_width(readings)
    print(f'| Day | Reading {" " * (reading_width - 8)} | Words |')
    print(f'|-----|{"-" * (reading_width + 2)}|-------|')

    # Print reading plan
    for index, [reading, words] in enumerate(readings):
        print(f'| {index + 1:<3} | {reading:<{reading_width}} | {words:<5,} |')


def export_plan_to_trello(plan: list) -> None:
    # Get the Trello API keys
    with open(os.path.join(dir_name, '..', 'config', 'secrets.json'), 'r') as secrets_file:
        secrets = json.load(secrets_file)

    # Create the Trello client
    client = TrelloClient(
        api_key=secrets['api_key'],
        token=secrets['token'],
        token_secret=secrets['token_secret']
    )

    # Create the new board
    print('Creating board')
    board = client.add_board('Bible reading plan', default_lists=False)

    # Keep track of the current day index
    # This will be used to test if we have added the last day
    day_index = 0

    # Add the lists for the weeks
    for week in range(1, math.ceil(DAYS / 7) + 1):
        # Create the list
        print(f'Creating list "Week {week}"')
        trello_list = board.add_list(f'Week {week}', week)

        # Create the day names for the cards
        days = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')

        # Add the cards for each day
        for day in days:
            # Create the card for the current day
            print(f'Creating card "{day}"')
            card = trello_list.add_card(day)

            # Get the readings array for this day
            readings = [f'{books[book]} {chapter}' for book, chapter in plan[day_index][0]]

            # Add the readings as a checklist
            card.add_checklist('Readings', readings)

            # Decrement the total days so we know when to stop
            day_index += 1

            # If this is the last day, stop the day loop
            if day_index == DAYS:
                break

    print('Reading plan exported to Trello')


def main() -> None:
    plan = []
    book = 0
    chapter = 1
    total_words = get_total_words()

    for day in range(DAYS):
        words = total_words // (DAYS - day)

        # Get the reading for today
        readings, book, chapter, words_today = get_day(book, chapter, words, day)
        total_words -= words_today

        # Add this days reading to the plan
        plan.append([readings, words_today])

        if is_last_chapter(book, chapter):
            break

    print_plan(plan)
    # export_plan_to_trello(plan)


if __name__ == '__main__':
    main()
