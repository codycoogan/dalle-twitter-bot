import base64
import io
import json
import os.path

from PIL import Image
from docarray import Document
from requests_oauthlib import OAuth1Session

API_KEY = ""
API_SECRET = ""
CONSUMER_KEY = ""
CONSUMER_SECRET = ""

DALLE_SERVER_URL = 'grpcs://dalle-flow.dev.jina.ai'
NUM_IMAGES = 2  # you get back 2 times this number
DALLE_IMAGES_PATH = '/Users/codycoogan/Documents/dalle_images/'


def main():
    get_and_save_images()
    media_ids = []
    # for each image, encode it and upload to twitter to get media_id
    for i in range(NUM_IMAGES * 2):
        img_path = os.path.join(DALLE_IMAGES_PATH, "image{}.png".format(i))
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            media_ids.append(upload_image_twitter(encoded_string))

    # Send tweet
    create_tweet(media_ids)


def get_and_save_images():
    prompt = 'a goat watching tv'
    print("Generating image for prompt: {}".format(prompt))
    # Generate images and save as gif
    da = Document(text=prompt).post(DALLE_SERVER_URL, parameters={'num_images': NUM_IMAGES}).matches
    # da.plot_image_sprites(fig_size=(10, 10), show_index=True)
    save_gif_path = os.path.join(DALLE_IMAGES_PATH, "image_gen.gif")
    da.save_gif(save_gif_path)

    # Save individual pics from gif
    with Image.open(save_gif_path) as im:
        for i in range(NUM_IMAGES*2):
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


def create_tweet(media_ids):
    twitter = get_twitter_session()
    url = 'https://api.twitter.com/2/tweets'
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "text": "Can you guess the prompt for these Dall-E computer generated images? It's 4 words. #dalle",
        "media": {
            "media_ids": media_ids
        }
    })
    response = twitter.post(url, data=data, headers=headers)
    # print(r)
    data = response.json()
    if not response.ok:
        print("Unable to create tweet: {}".format(data['errors']))
    else:
        print("Tweet sent successfully!")


def get_twitter_session():
    return OAuth1Session(API_KEY,
                         client_secret=API_SECRET,
                         resource_owner_key=CONSUMER_KEY,
                         resource_owner_secret=CONSUMER_SECRET)


if __name__ == '__main__':
    # noun verb preposition location [with object [in style of]]
    main()
