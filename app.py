# -*- coding: utf-8 -*-

import os
import sys
import json

import requests
from flask import Flask, request
import pickle
import random
import apiai



app = Flask(__name__)

quotes=pickle.load(open('quoteobj'))

def chunkstring(string, length):
	return (string[0+i:length+i] for i in range(0, len(string), length))

def apiai_call(message):
    ai = apiai.ApiAI(os.environ["APIAI_CLIENT_ACCESS_TOKEN"])
    request = ai.text_request()
    request.query = message 
    response = request.getresponse()
    response_json = json.loads(response.read().decode('utf-8'))
    return response_json['result']['fulfillment']['speech']


@app.route('/', methods=['GET'])
def verify():
	# when the endpoint is registered as a webhook, it must echo back
	# the 'hub.challenge' value it receives in the query arguments
	if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
		if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
			return "Verification token mismatch", 403
		return request.args["hub.challenge"], 200

	return "Welcome to Sheldonisms", 200


@app.route('/', methods=['POST'])
def webhook():

	# endpoint for processing incoming messaging events

	data = request.get_json()
	log(data)  # you may not want to log every incoming message in production, but it's good for testing

	if data["object"] == "page":

		for entry in data["entry"]:
			for messaging_event in entry["messaging"]:

				if messaging_event.get("message"):  # someone sent us a message

					sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
					recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
					message_text=""
					try:
						message_text = messaging_event["message"]["text"]  # the message text
					except:
						message_text = "Sticker!"

					# if message_text.lower()=="hi" or message_text.lower()=="hi!" or message_text.lower()=="hello!" or message_text.lower()=="hello" or message_text.lower()=="hey!" or message_text.lower()=="hey":
					# 	send_message(sender_id, u'Hello from Sheldon! 🖖 \nSend Bazinga! for a new quote.'.encode('utf-8'))
					# 	quickreply(sender_id)


					# elif message_text.lower()=="lol" or message_text.lower()=="haha" or message_text.lower()=="hehe":
					# 	send_message(sender_id, "You think I'm funny, but I'm serious. Well, mostly. Send Bazinga for the next one!")
					# 	quickreply(sender_id)


					if message_text.lower()=="i'm done":
						send_message(sender_id, "Goodbye, human. If you require more of my humour, type Bazinga to wake me up.")

					elif message_text.lower()=="bazinga" or message_text.lower()=="bazinga!":
						while True:
							show=random.choice(quotes)
							if len(show)>0:
								if len(show)<320:
									send_message(sender_id, show)
									quickreply(sender_id)
									break
								else:
									for chunk in chunkstring(show, 300):
										send_message(sender_id, chunk)
									quickreply(sender_id)
									break

					else:
						send_message(sender_id, apiai_call(message_text))
						quickreply(sender_id)


				if messaging_event.get("delivery"):  # delivery confirmation
					pass

				if messaging_event.get("optin"):  # optin confirmation
					pass

				if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
					pass

	return "ok", 200


def send_message(recipient_id, message_text):

	log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

	params = {
		"access_token": os.environ["PAGE_ACCESS_TOKEN"]
	}
	headers = {
		"Content-Type": "application/json"
	}
	data = json.dumps({
		"recipient": {
			"id": recipient_id
		},
		"message": {
			"text": message_text
		}
	})
	r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
	if r.status_code != 200:
		log(r.status_code)
		log(r.text)


def quickreply(recipient_id):

	params = {
		"access_token": os.environ["PAGE_ACCESS_TOKEN"]
	}
	headers = {
		"Content-Type": "application/json"
	}
	data = json.dumps({
		"recipient": {
			"id": recipient_id
		},
		"message": {
			"text": u'🖖'.encode('utf-8'),
			"quick_replies":[
			  {
				"content_type":"text",
				"title":"Bazinga!",
				"payload":"NEW_JOKE"
			  },
			  {
				"content_type":"text",
				"title":"I'm done",
				"payload":"DONE"
			  }
			]
		}
	})
	r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
	if r.status_code != 200:
		log(r.status_code)
		log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
	print str(message)
	sys.stdout.flush()


if __name__ == '__main__':
	app.run(debug=True)
