#!/usr/bin/env python3
import json
from collections import OrderedDict
from time import strftime, localtime

import requests
from bs4 import BeautifulSoup, SoupStrainer


def convert_timestamp(timestamp):
    """Return converted timestamp
    Timestamp assumed to be in milliseconds
    """
    return strftime('%d %B %Y', localtime(int(timestamp) / 1000))


class CounterScrape:
    """Class to handle and display HLTV match data"""
    MAPS = {
        'mrg': 'Mirage',
        'trn': 'Train',
        'ovp': 'Overpass',
        'inf': 'Inferno',
        'cch': 'Cache',
        'cbl': 'Cobblestone',
        'nuke': 'Nuke',
        'bo2': 'Best-of-two ',
        'bo3': 'Best-of-three ',
        'bo5': 'Best-of-five ',
        '-': 'Default win'
    }

    def __init__(self):
        self.session = requests.Session()
        self.current_date = strftime('%d %B %Y')
        self.url = 'https://www.hltv.org'

    def scrape(self, url, tag):
        """Return a parsed BeautifulSoup object"""
        response = self.session.get(url)
        response.raise_for_status()
        source = response.text
        parse_tag = SoupStrainer(class_=tag)
        return BeautifulSoup(source, 'lxml', parse_only=parse_tag)

    def get_maps(self, href, maps_played):
        """Return a space delimited string of
        maps played in a best-of-n series
        """
        soup = self.scrape(self.url + href, 'mapname')
        maps = [map_name.get_text() for map_name in soup('div', 'mapname')]
        return ' '.join(maps[:maps_played])

    def check_match_date(self, tag):
        """Helper method to get_results"""
        result = tag.name == 'div' and 'result-con' in tag.get('class', [])
        if not result:
            return False
        timestamp = tag['data-zonedgrouping-entry-unix']
        return convert_timestamp(timestamp) == self.current_date

    def get_results(self):
        """Return JSON text with current date results"""
        soup = self.scrape(self.url + '/results', 'result-con')
        match_results = OrderedDict()
        for result in soup(self.check_match_date):
            timestamp = result['data-zonedgrouping-entry-unix']
            team_one = result.select_one('.team1').get_text(strip=True)
            team_two = result.select_one('.team2').get_text(strip=True)
            score = result.select_one('.result-score').get_text().split()
            team_one_score = score[0]
            team_two_score = score[-1]
            event = result.select_one('.event-name').get_text()
            maps = result.select_one('.map-text').get_text()
            if 'bo' in maps:
                href = result.select_one('.a-reset')['href']
                game_score = int(team_one_score) + int(team_two_score)
                maps = self.get_maps(href, game_score)
            else:
                maps = self.MAPS[maps]

            match_results[timestamp] = {
                'team_one': team_one,
                'team_one_score': team_one_score,
                'team_two': team_two,
                'team_two_score': team_two_score,
                'event': event,
                'maps': maps
            }
        return json.dumps(match_results, indent=4, separators=(',', ':'))

    def results_dict(self):
        """Convert JSON text back to OrderedDict"""
        return json.loads(self.get_results(), object_pairs_hook=OrderedDict)

    def pprint(self):
        """Pretty print method to display match results"""
        results = self.results_dict()
        if not results:
            print('No match results for {}'.format(self.current_date))
        else:
            for match in results.values():
                print('{team_one:^20} {team_one_score:<2} - '
                      '{team_two_score:>2} {team_two:^20}'
                      ' {maps:<13}'.format(**match))
            print('\nCS:GO match results for {}'.format(self.current_date))
        print('Powered by HLTV.org')

    def __str__(self):
        return 'CounterScrape'

if __name__ == '__main__':
    cs = CounterScrape()
    cs.pprint()
