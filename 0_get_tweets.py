import requests
import snscrape.modules.twitter as sntwitter
import pandas as pd

#
# Get the tweets info
#
query = "chatgpt"
limit = 10_000
tweets = []

for tweet in sntwitter.TwitterSearchScraper(query).get_items():
    # only interested in screenshots    
    if tweet.media and type(tweet.media[0]) is sntwitter.Photo:
        tweets.append(
            {
                "media":[m.fullUrl for m in tweet.media if type(m) is sntwitter.Photo ],
                "content":tweet.content
            }
        )
        # status update and save to csv
        if len(tweets) % 100 == 0: 
            print("Found",len(tweets),"tweets...")
            tweets_df = pd.DataFrame(tweets)
            tweets_df.to_csv("downloaded_tweets.csv")
    # max number
    if len(tweets) == limit:
        break


