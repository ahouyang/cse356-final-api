import requests
import sys

def _url(path):
	return 'http://130.245.168.91' + path

def add_question(title, body, tags, username):
	return requests.post(_url('/add'), json={
		'username': username,
		'title':title,
		'body':body,
		'tags':tags
		})

def get_question(id, user):
	return requests.post(_url('/getquestion'), json={
		'id': id,
		'user':user
		})

def delete_question(id, user):
	return requests.delete(_url('/deletequestion'), json={
		'id': id,
		'user':user
		})

def add_answer(body, username, id, media=None):
	req = {}
	req['body'] = body
	req['username'] = username
	req['id'] = id
	if media is not None:
		req['media'] = media
	return requests.post(_url('/addanswer'), json=req)

def get_answers(id):
	return requests.get(_url('/getanswers/' + id))

def search(timestamp, limit):
	json = {
	'timestamp': timestamp,
	'limit': limit
	}
	print('-----------------------------' + str(json), sys.stderr)
	return requests.post(_url('/search'), json=json)

def get_topten():
	return requests.get(_url('/topten'))
