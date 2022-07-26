import base64
import json
import os.path
import time

import requests
from PIL import Image
from docarray import Document
from requests_oauthlib import OAuth1Session

# Twitter
API_KEY = ""
API_SECRET = ""
CONSUMER_KEY = ""
CONSUMER_SECRET = ""
# Wordnik
WORDNIK_API_KEY = ''

DALLE_SERVER_URL = 'grpcs://dalle-flow.dev.jina.ai'
NUM_IMAGES = 2  # you get back 2 times this number
DALLE_IMAGES_PATH = ''


def main():
    while True:
        sentence = get_sentence(get_word("noun"), get_word("verb"), get_word("verb"))
        if sentence:
            print(sentence)
            break
        print("sleeping 10 seconds....")
        time.sleep(10)

    get_and_save_images(sentence)
    media_ids = []
    # for each image, encode it and upload to twitter to get media_id
    for i in range(NUM_IMAGES * 2):
        img_path = os.path.join(DALLE_IMAGES_PATH, "image{}.png".format(i))
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            media_ids.append(upload_image_twitter(encoded_string))

    # Send tweet
    create_tweet(media_ids, sentence)


def get_sentence(subject, verb, object_pos):
    uri = 'https://lt-nlgservice.herokuapp.com/rest/english/realise?subject={}&verb={}&object={}'.format(subject, verb,
                                                                                                         object_pos)
    response = requests.get(uri)
    data = response.json()
    if not response.ok or data.get("result") != 'OK':
        print("Unable to get sentence! Try again")
        return None

    return data.get("sentence")


def get_word(part_of_speech):
    parts_of_speech = ["noun", "adjective", "verb", "adverb", "interjection", "pronoun", "preposition", "abbreviation",
                       "affix", "article", "auxiliary-verb", "conjunction", "definite-article", "family-name",
                       "given-name", "idiom", "imperative", "noun-plural", "noun-posessive", "past-participle",
                       "phrasal-prefix", "proper-noun", "proper-noun-plural", "proper-noun-posessive", "suffix",
                       "verb-intransitive", "verb-transitive"]
    parts_of_speech.remove(part_of_speech)
    uri = 'http://api.wordnik.com/v4/words.json/randomWord?hasDictionaryDef=true&api_key={}&includePartOfSpeech={}&excludePartOfSpeech={}'.format(
        WORDNIK_API_KEY, part_of_speech, ','.join(parts_of_speech))
    response = requests.get(uri)
    data = response.json()
    if not response.ok:
        print("Unable to get a {} from wordnik: {}".format(part_of_speech, data))
        return None
    return data.get("word")


def get_and_save_images(prompt):
    print("Generating image for prompt: {}".format(prompt))
    # Generate images and save as gif
    da = Document(text=prompt).post(DALLE_SERVER_URL, parameters={'num_images': NUM_IMAGES}).matches
    # da.plot_image_sprites(fig_size=(10, 10), show_index=True)
    save_gif_path = os.path.join(DALLE_IMAGES_PATH, "image_gen.gif")
    da.save_gif(save_gif_path)

    # Save individual pics from gif
    with Image.open(save_gif_path) as im:
        for i in range(NUM_IMAGES * 2):
            im.seek(im.n_frames // (NUM_IMAGES * 2) * i)
            im_save_path = os.path.join(DALLE_IMAGES_PATH, 'image{}.png'.format(i))
            im.save(im_save_path)


def upload_image_twitter(encoded_image):
    twitter_session = get_twitter_session()
    url = 'https://upload.twitter.com/1.1/media/upload.json'
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"media_data": encoded_image}
    response = twitter_session.post(url, data=data, headers=headers)
    data = response.json()
    if not response.ok:
        print("Unable to get image Id: {}".format(data['errors']))
        return False
    return data['media_id_string']


def create_tweet(media_ids, prompt):
    twitter = get_twitter_session()
    url = 'https://api.twitter.com/2/tweets'
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "text": "What sentence generated these Dall-E computer images? It's <= 5 words! #dalle",
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


def get_twitter_session():
    return OAuth1Session(API_KEY,
                         client_secret=API_SECRET,
                         resource_owner_key=CONSUMER_KEY,
                         resource_owner_secret=CONSUMER_SECRET)


if __name__ == '__main__':
    # noun verb preposition location [with object [in style of]]
    main()
