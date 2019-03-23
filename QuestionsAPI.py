import requests

def _url(path):
	return 'http://130.245.168.91' + path

def add_question(title, body, tags, username):
	return requests.post(_url('/add'), json={
		'username': username,
		'title':title,
		'body':body,
		'tags':tags
		})