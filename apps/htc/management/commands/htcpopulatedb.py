"""
Management wrapper for running database build processes
(see htc/build/populatedb.py)
"""

from django.core.management.base import BaseCommand

from apps.htc.build import populatedb


class Command(BaseCommand):
    help = 'Run database build processes for HT Classifier'

    def handle(self, *args, **options):
        populatedb.populate_taxonomy()
        populatedb.populate_senses()
