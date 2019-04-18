import requests

def _url(path):
	return 'http://130.245.170.48' + path

def authenticate(username, password):
	return requests.post(_url('/authenticate'), json={
		'username': username,
		'password': password
		})

def verify(email, key):
	return requests.post(_url('/verify'), json={
		'email': email,
		'key': key
		})

def validate_new(username, email):
	return requests.post(_url('/validatenew'), json={
		'username': username,
		'email': email
		})

def adduser(username, password, email):
	return requests.post(_url('/adduser'), json={
		'username': username,
		'password': password,
		'email': email
		})

def getuser(username):
	return requests.get(_url('/getuser/' + username))

def getuserQ(username):
	return requests.get(_url('/getuserquestions/' + username))

def getuserA(username):
	return requests.get(_url('/getuseranswers/' + username))
