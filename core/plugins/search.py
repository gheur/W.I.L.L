# Internal imports
from core.plugin_handler import subscribe
import tools

# External imports
import wolframalpha
import wikipedia
import google
from bs4 import BeautifulSoup

# Builtin imports
import logging
import urllib2

log = logging.getLogger()

def search_google(query):
    '''Search google and determine if wikipedia is in it'''
    search_object = google.search(query)
    #Determine if a wikipedia url is in the first 5 searches
    urls = []
    for i in range(0, 4):
        url = search_object.next()
        urls.append(url)
        if "wikipedia.org/wiki" in url:
            response = wikipedia.summary(wikipedia.suggest(query)) + "(wikipedia)"
            return response
    #If there were no wikipedia pages
    first_url = urls[0]
    html = urllib2.urlopen(first_url).read()
    #Parse the html using bs4
    soup = BeautifulSoup(html)
    [s.extract() for s in soup(['style', 'script', '[document]', 'head', 'title'])]
    text = soup.getText()
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    soup_text = '\n'.join(chunk for chunk in chunks if chunk)
    response = format(soup_text) + "({0})".format(first_url)
    return response
def search_wolfram(query, api_key):
    '''Search wolframalpha'''
    client = wolframalpha.Client(api_key)
    # Santize query
    query = str(query).decode('ascii', 'ignore')
    res = client.query(query)
    try:
        next_result = next(res.results).text
        if next_result:
            # Sanitze result
            result = next_result.encode('ascii', 'ignore')
            log.debug("Sanitized wolfram result is {0}".format(result))
            return result
        else:
            return False
    except StopIteration:
        log.error("StopIteration raised with wolfram query {0}".format(
            query
        ))
        return False
    except AttributeError:
        return False


def is_search(event):
    '''Determine whether it's a search command'''
    command = event["command"]
    if "search" in event["verbs"]:
        return True
    question_words = [
        "what",
        "when",
        "why",
        "how",
        "who",
        "are",
        "is"
    ]
    first_word = command.split(" ")[0].lower()
    log.debug("First word in command is {0}".format(first_word))
    if first_word in question_words:
        return True
    return False


@subscribe({"name": "search", "check": is_search})
def main(data):
    '''Start the search'''
    query = data["command"]
    log.info("In main search function with query {0}".format(query))
    db = data["db"]
    answer = False
    wolfram_key = tools.load_key("wolfram", db)
    wolfram_response = search_wolfram(query, wolfram_key)
    # If it found an answer answer will be set to that, if not it'll still be false
    answer = wolfram_response
    if answer:
        return answer
    else:
        return search_google(query)
