#! /usr/bin/python2
from __future__ import print_function
import re
import sys
import time

import requests
import bs4
from bs4 import BeautifulSoup
import pandas as pd

base_url = "http://www.moviebodycounts.com/"

r = requests.get(base_url + "movies.htm")
soup = BeautifulSoup(r.text)
anchors = soup.findAll('a')
movie_pages = [a['href'] for a in anchors if a['href'].startswith('movies-')]

data = {'title':[], 'year':[], 'kills':[], 'imdb':[]}

kill_phrases = ["entire film:", "on screen kills:", "film:", "Kills*"]

def findStringChildNodes(node):
    tags = [child.strip().replace("\r\n", " ")
            for child in node.recursiveChildGenerator() if
        isinstance(child, bs4.element.NavigableString) and child.strip() != '']
    return tags

def flatten(list_of_lists):
    return reduce(lambda x,y: x+y, list_of_lists)

for page in movie_pages:
    r = requests.get(base_url + page)
    soup = BeautifulSoup(r.text)
    movies = [a['href'] for a in soup.findAll('a') if (a['href'].endswith('.htm')
        and a.text != '' and a['href'] not in ['movies.htm', 'contact.htm'])]
    for movie in movies:
        try:
            print("Crawling", movie)
            r = requests.get(base_url + movie)
            soup = BeautifulSoup(r.text)

            title = flatten([findStringChildNodes(node) for node in
                    soup.findAll('span', attrs={'style':"color: rgb(153, 153, 153);"})])[0]

            tags = flatten([findStringChildNodes(node) for node in
                    soup.findAll('font', attrs={'size':'-1'})])
            kills = [tag for tag in tags if any(
                map(lambda s: s in tag.replace("\r\n", " ").lower(), kill_phrases))]
            kills = int(re.sub("[^0-9]", "", kills[0].split(":")[-1].split("(")[0]))

            year = soup.findAll(['a', 'span'], attrs={"style":"color: rgb(198, 213, 217);"})
            if len(year) != 1:
                print("Ambiguous year lines, skipping", movie)
                continue
            year = int(year[0].text)

            imdb = [a['href'] for a in soup.findAll('a') if
                    (a.has_attr('href') and 'imdb.com' in a['href'] and 'imdb' in a.text.lower())]
            if len(imdb) != 1:
                print("Ambiguous imdb lines, skipping", movie)
                continue
            imdb = imdb[0].split('/title/')[1].strip('/')

            data['title'].append(title)
            data['year'].append(year)
            data['kills'].append(kills)
            data['imdb'].append(imdb)
        except:  # catch all exception types
            e = sys.exc_info()[0]
            print("Error processing", movie, ":", e)
        # sleep a little to not spam the server too much
        time.sleep(0.1)

data = pd.DataFrame(data)
data.to_csv('moviebodycounts.csv')
