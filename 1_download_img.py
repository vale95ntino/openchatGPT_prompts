import requests
import pandas as pd
import ast
import os

tweets_df = pd.read_csv("downloaded_tweets.csv")

if not os.path.exists('downloaded_img/'):
    os.makedirs('downloaded_img')

print("Downloading images for",len(tweets_df),"tweets...")
for index, row in tweets_df.iterrows():
    if index % 20 == 0 : print(index+1,"...")
    urls = ast.literal_eval(row.media)
    for idx, fullUrl in enumerate(urls):
        r = requests.get(fullUrl)
        with open(f"""./downloaded_img/{index}_{idx}.jpg""", 'wb') as fp:
            fp.write(r.content)