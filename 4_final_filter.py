#
# TODO
# - remove any reference to OpenAI
# - Clean up manually the text
# - remove table and code answers
# - Get it up to 1k

import json

with open("conversations.json", "r") as f:
    conversations = json.load(f)
    conversations = json.loads(conversations)

clean_conversations = []

for conv in conversations:
    for text in conv:
        text["data"]["body"] = text["data"]["body"].replace("\n"," ")
        print(text["data"]["body"])