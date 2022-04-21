"""
anji.py

Package 

Author:
    kinami

Created:
    3/23/22
"""
import csv
import datetime
from collections import namedtuple

import questionary
from chinese import ChineseAnalyzer
from dragonmapper.transcriptions import numbered_to_accented

from env import DESTINATION, ORIGIN, EXCLUDED_START, EXCLUDED_END

fieldnames = [
    'word',
    'meaning',
    'meaning_whitelist',
    'meaning_blacklist',
    'reading',
    'reading_whitelist',
    'reading_blacklist',
    'audio',
    'sort_id',
    'do_not_modify'
]
word = namedtuple('word', fieldnames)
analyzer = ChineseAnalyzer()


def read(fp: str) -> list[str]:
    res = []
    with open(fp, 'r+', encoding='utf-8') as f:
        reader = csv.reader(f)
        for w in reader:
            res.append(w[0])
    return res


def note(w: str, res: list[word], i: int) -> list[word] | tuple[list[word], int]:
    """
    Generates the card info from a word
    :param res:
    :param w:
    :return:
    """
    info = analyzer.parse(w)
    if w not in info:
        print(f'\'{w}\' not added because a definition could not be found')
        return res, i
    else:
        info = info[w]

    if not info:
        print(f'\'{w}\' not added because a definition could not be found')
        return res, i

    info = questionary.checkbox(
        f'Please select the correct definition for \'{w}\'',
        [
            questionary.Choice(
                f'({" ".join(r.pinyin)}) {", ".join(r.definitions)}',
                r
            )
            for r
            in info
        ]
    ).ask() if len(info) > 1 else info

    for inf in info:
        defs = [
            de
            for de
            in inf.definitions
            if all([
                not de.startswith(e)
                for e
                in EXCLUDED_START
            ]) and all([
                not de.endswith(e)
                for e
                in EXCLUDED_END
            ])
        ]
        if defs:
            res.append(word(
                w,
                '<br>'.join([de.title() for de in defs]),
                ', '.join(defs),
                '',
                numbered_to_accented(' '.join(inf.pinyin)),
                ''.join(inf.pinyin),
                '',
                '',
                i,
                '-'
            ))
            i += 1

    return res, i


def write(notes: list[word]):
    """
    Exports a list of notes into a file and saves all the audios into Anki's collection.media folder
    :param notes:
    """
    with open(f'{DESTINATION}/{datetime.datetime.now()}.txt', 'w+', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter='\t')
        writer.writerows([no._asdict() for no in notes if no])


if __name__ == '__main__':
    INIT = int(questionary.text(
        'Please enter the starting index of the words you want to add',
        validate=lambda x: x.isnumeric()
    ).ask())
    match questionary.select(
        'Do you want to add the words from a file or manually?',
        choices=[
            questionary.Choice('File', 0),
            questionary.Choice('Manual', 1)
        ]
    ).ask():
        case 0:
            res = []
            i = INIT
            for s in read(ORIGIN):
                res, i = note(s, res, i)
            write(res)
        case 1:
            while True:
                w = questionary.text('Please enter a word').ask()
                if w == '':
                    break
                i = INIT
                res, i = note(w, [], i)
                write(res)
