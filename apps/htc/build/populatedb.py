import os
import string
import json
from sys import stdout

from apps.htc.models import ThesaurusClass, Level2Class, Sense

IN_DIR = '/home/james/j/work/lex/oed/projects/htclassifier/db_json'


def populate_taxonomy():
    _empty_tables(['sense', 'thesaurusclass'])
    filepath = os.path.join(IN_DIR, 'taxonomy', 'taxonomy.json')
    classes = []
    with open(filepath, 'r') as filehandle:
        for line in filehandle:
            data = json.loads(line.strip())
            classes.append(ThesaurusClass(**data))
    ThesaurusClass.objects.bulk_create(classes)

    classes = []
    with open(filepath, 'r') as filehandle:
        for line in filehandle:
            data = json.loads(line.strip())
            if data['level'] in (1, 2):
                classes.append(Level2Class(**data))
    Level2Class.objects.bulk_create(classes)


def populate_senses():
    _empty_tables(['sense', ])

    for letter in string.ascii_uppercase:
        stdout.write('Inserting data for %s...\n' % letter)
        senses = []
        in_file = os.path.join(IN_DIR, 'senses', letter + '.json')
        with open(in_file, 'r') as filehandle:
            for line in filehandle:
                data = json.loads(line.strip())
                senses.append(Sense(**data))

                if len(senses) > 1000:
                    Sense.objects.bulk_create(senses)
                    senses = []

        Sense.objects.bulk_create(senses)


def _empty_tables(tables):
    """
    Empty the database tables of any existing content
    """
    tables = [t.lower() for t in tables]
    if 'sense' in tables:
        Sense.objects.all().delete()
    if 'thesaurusclass' in tables:
        ThesaurusClass.objects.all().delete()
        Level2Class.objects.all().delete()
