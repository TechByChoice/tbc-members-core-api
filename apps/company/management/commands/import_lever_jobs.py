import json
from datetime import datetime
from html import unescape

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
import requests
from xml.etree import ElementTree as ET

from apps.company.models import CompanyProfile
from apps.company.views import sync_jobs_for_company


class Command(BaseCommand):
    help = "Sync jobs from Lever for all companies"

    def handle(self, *args, **kwargs):
        for company in CompanyProfile.objects.filter(lever_xml_feed_url__isnull=False):
            sync_jobs_for_company(company)

        self.stdout.write(self.style.SUCCESS('Successfully synced jobs from Lever for all companies'))
