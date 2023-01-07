import json
import random

import openai
from requests_oauthlib import OAuth1Session

from word_data import WordData

NUM_IMAGES = 2  # you get back 2 times this number


def main():
    with open("credentials.json", "r") as credentials_file:
        credentials_dict = json.load(credentials_file)
    guess_dalle = GuessDalle(credentials_dict)
    guess_dalle.execute()


class GuessDalle:

    def __init__(self, credentials_dict):
        # OpenAI
        self.OPENAI_API_KEY = credentials_dict['OPENAI_API_KEY']
        # Twitter
        self.API_KEY = credentials_dict['API_KEY']
        self.API_SECRET = credentials_dict['API_SECRET']
        self.CONSUMER_KEY = credentials_dict['CONSUMER_KEY']
        self.CONSUMER_SECRET = credentials_dict['CONSUMER_SECRET']

    def execute(self):
        # Get noun and adjective
        adj, noun = self.get_word_pair()
        prompt = "{} {}".format(adj, noun)
        base64_encodings = self.get_openai_image(prompt)
        media_ids = []
        for encoding in base64_encodings:
            media_id = self.upload_image_twitter(encoding)
            media_ids.append(media_id)
        self.create_tweet(media_ids, prompt)

    def get_word_pair(self):
        """
        Gets adjective noun word pair
        :return:
        """
        adjs = WordData.adjs['adjs']
        nouns = WordData.nouns['nouns']
        rand_one = random.randrange(start=0, stop=len(adjs) - 1)
        rand_two = random.randrange(start=0, stop=len(nouns) - 1)
        return adjs[rand_one], nouns[rand_two]

    def upload_image_twitter(self, encoded_image):
        twitter_session = self.get_twitter_session()
        url = 'https://upload.twitter.com/1.1/media/upload.json'
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"media_data": encoded_image}
        response = twitter_session.post(url, data=data, headers=headers)
        data = response.json()
        if not response.ok:
            print("Unable to get image Id: {}".format(data['errors']))
            return False
        return data['media_id_string']

    def create_tweet(self, media_ids, prompt):
        twitter = self.get_twitter_session()
        url = 'https://api.twitter.com/2/tweets'
        headers = {"Content-Type": "application/json"}
        data = json.dumps({
            "text": "What two word prompt generated these Dall-E computer images?? #dalle #GuessThePrompt",
            "media": {
                "media_ids": media_ids
            }
        })
        response = twitter.post(url, data=data, headers=headers)
        data = response.json()
        if not response.ok:
            print("Unable to create tweet: {}".format(data.get('errors')))
        else:
            print("Tweet sent successfully!")
            twitter_id = data.get('data').get('id')
            # Reply to tweet
            reply_data = json.dumps({
                "text": "Prompt:\n\n\n {}".format(prompt),
                "reply": {
                    "in_reply_to_tweet_id": twitter_id
                }
            })
            response = twitter.post(url, data=reply_data, headers=headers)
            data = response.json()
            if not response.ok:
                print("Unable to reply to tweet: {}".format(data.get('errors')))

    def get_openai_image(self, prompt):
        openai.api_key = self.OPENAI_API_KEY
        response = openai.Image.create(
            prompt=prompt,
            n=4,
            size="1024x1024",
            response_format="b64_json"

        )
        base64_encodings = [x['b64_json'] for x in response['data']]
        return base64_encodings

    def get_twitter_session(self):
        return OAuth1Session(self.API_KEY,
                             client_secret=self.API_SECRET,
                             resource_owner_key=self.CONSUMER_KEY,
                             resource_owner_secret=self.CONSUMER_SECRET)


if __name__ == '__main__':
    # noun verb preposition location [with object [in style of]]
    main()
