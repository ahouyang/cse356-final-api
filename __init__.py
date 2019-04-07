from flask import Flask, request, render_template, make_response, jsonify
from flask_restful import Resource, Api, reqparse
import pymongo
import datetime
import sys
# import tttalgorithm as ttt
import smtplib, ssl
import string
import random
# import pika
import AccountAPI as account
import QuestionsAPI as questions
import time

app = Flask(__name__)
api = Api(app)

class Homepage(Resource):
	def get(self):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'OK':
			headers = {'Content-Type': 'text/html'}

			return make_response(render_template('index.html', username = username),200,headers)
		return make_response(render_template('index.html'), 200, {'Content-Type': 'text/html'})


class AddUser(Resource):
	def post(self):
		args = parse_args_list(['username', 'password', 'email'])
		resp = account.validate_new(args['username'], args['email'])
		if resp.json()['status'] == 'OK':
			createresp = account.adduser(args['username'], args['password'], args['email'])
			return createresp.json()
		else:
			return resp.json()

class Verify(Resource):
	def post(self):
		try:
			self.handleRequest(parse_args_list(['email', 'key']))
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "error"}
	def get(self):
		# TODO, have this return html saying "your account is verified" instead of this json
		# OK or ERROR JSON should only be returned by POST, not GET
		try:
			self.handleRequest(request.args)
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "error"}
	def handleRequest(self, args):
		# args = parse_args_list(['email', 'key'])
		resp = account.verify(args['email'], args['key'])
		if resp.json()['status'] == 'OK':
			return
		raise Exception(resp.json()['message'])

class Login(Resource):

	def get(self):
		headers = {'Content-Type': 'text/html'}
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		users = get_users_coll()
		currUser = users.find_one({'username': username})
		if(currUser is None):
			return make_response(render_template('login.html'),200,headers)
		if(currUser['password'] == password):
			now = datetime.datetime.now()
			month =str(now.month) if len(str(now.month)) == 2 else '0' + str(now.month)
			day =str(now.day) if len(str(now.day)) == 2 else '0' + str(now.day)
			date = str(now.year) + '-' + month + '-' + day
			stuff = {'name': username, 'date': date}
			return make_response(render_template('index.html', stuff = stuff),200,headers)

		return make_response(render_template('login.html'),200,headers)
	def post(self):
		# validate user and password
		args = parse_args_list(['username', 'password'])
		resp = {}
		micro_resp = account.authenticate(args['username'], args['password'])
		users = get_users_coll()
		currUser = users.find_one({'username': args['username']})
		if micro_resp.json()['status'] == 'OK':
			print('####################### verification' + currUser['verification'], sys.stderr)
			headers = {'Content-Type': 'application/json'}
			response = make_response(jsonify({"status": "OK"}), 200, headers)
			response.set_cookie('username', currUser['username'])
			response.set_cookie('password', currUser['password'])
			return response
		elif micro_resp.json()['error'] == 'not verified':
			resp['status'] = "error"
			resp['error'] = "User has not been validated. Check your email."
			# print('#######################not validated', file=sys.stderr)
			return resp
		elif micro_resp.json()['error'] == 'incorrect password':
			resp['status'] = "error"
			resp['error'] = "The entered password is incorrect."
			# print('#######################wrong password', file=sys.stderr)
			return resp
		else:
			resp['status'] = "error"
			resp['error'] = "The entered username doesn't exist."
			# print('#######################bad username:' + str(args['username']), file=sys.stderr)
			return resp

class Logout(Resource):
	def post(self):
		# Update cookie to invalid one; no access to database bc cookie just serves to initialize the board upon login
		try:
			headers = {'Content-Type': 'application/json'}
			response = make_response(jsonify({"status": "OK"}), 200, headers)
			response.set_cookie('username', '', expires = 0)
			response.set_cookie('password', '', expires = 0)
			response.set_cookie('grid', '', expires = 0)
			return response
		except Exception as e:
			print(e, sys.stderr)
			return {'status': "error"}

class AddQuestion(Resource):
	def post(self):
		# authenticate cookie, 
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'error':
			return resp.json()
		parser = reqparse.RequestParser()
		parser.add_argument('title')
		parser.add_argument('body')
		parser.add_argument('tags', action='append')
		args = parser.parse_args()
		if args.get('title') is None:
			return self._error('title required')
		elif args.get('body') is None:
			return self._error('body required')
		elif args.get('tags') is None:
			return self._error('tags required')
		resp = questions.add_question(args['title'], args['body'], args['tags'], username)
		return resp.json()
	def _error(self, message):
		return {'status': 'error', 'error': message}

class GetQuestion(Resource):
	def get(self, id):
		# check if user is logged in
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		user = None
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'OK':
			user = username
		else:
			user = request.remote_addr
		resp2 = questions.get_question(id=id, user=user)
		print("#######################" + str(resp2), sys.stderr)
		return resp2.json()

class AddAnswer(Resource):
	def post(self, id):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'error':
			return resp.json()
		parser = reqparse.RequestParser()
		parser.add_argument('body')
		parser.add_argument('media', action='append')
		args = parser.parse_args()
		if args.get('body') is None:
			return {'status': 'error', 'error':'body is required'}
		resp2 = questions.add_answer(body=args['body'], username=username, id=id, media=args.get('media'))
		return resp2.json()

class Search(Resource):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('timestamp', type=float)
		parser.add_argument('limit', type=int)
		args = parser.parse_args()
		print('$$$$$$$$$$$$$$$$$$$$$$$$$$args:' + str(args), sys.stderr)
		timestamp = args['timestamp'] if args['timestamp'] is not None else time.time()
		limit = args.get('limit')
		if args['limit'] is not None:
			if args['limit'] > 100:
				limit = 100
		else:
			limit = 25
		# accepted = args['accepted'] if args['accepted'] is not None else False
		resp = questions.search(timestamp, limit)
		return resp.json()

class GetAnswers(Resource):
	def get(self, id):
		return questions.get_answers(id).json()

class TopTen(Resource):
	def post(self):
		return questions.get_topten().json()

def parse_args_list(argnames):
	parser = reqparse.RequestParser()
	for arg in argnames:
		parser.add_argument(arg)
	args = parser.parse_args()
	return args

def get_users_coll():
	myclient = pymongo.MongoClient('mongodb://130.245.170.88:27017/')
	mydb = myclient['finalproject']
	users = mydb['users']
	return users


api.add_resource(Homepage, '/')
api.add_resource(AddUser, '/adduser')
api.add_resource(Verify, '/verify')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(AddQuestion, '/questions/add')
api.add_resource(GetQuestion, '/questions/<id>')
api.add_resource(AddAnswer, '/questions/<id>/answers/add')
api.add_resource(GetAnswers, '/questions/<id>/answers')
api.add_resource(Search, '/search')
api.add_resource(TopTen, '/topten')

if __name__ == '__main__':
	app.run(debug=True)
