from flask import Flask, request, render_template, make_response, jsonify 
from flask_restful import Resource, Api, reqparse, inputs 
import pymongo 
import datetime 
import sys
# import tttalgorithm as ttt
import smtplib, ssl
import string
import random
import pika
import AccountAPI as account
import QuestionsAPI as questions
import time
from cassandra.cluster import Cluster
import base64
import json

app = Flask(__name__)
api = Api(app)

cluster = Cluster(['192.168.122.21'])
session = cluster.connect(keyspace='stackoverflow')
myclient = pymongo.MongoClient('mongodb://130.245.170.88:27017/')
mydb = myclient['finalproject']
users = mydb['users']
media = mydb['media']

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
			return resp.json(), 400

	def get(self):
		headers = {'Content-Type': 'text/html'}
		return make_response(render_template('signup.html'), 200, {'Content-Type': 'text/html'})


class Verify(Resource):
	def post(self):
		try:
			self.handleRequest(parse_args_list(['email', 'key']))
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "error", "error":str(e)}, 400
	def get(self):
		# TODO, have this return html saying "your account is verified" instead of this json
		# OK or ERROR JSON should only be returned by POST, not GET
		try:
			self.handleRequest(request.args)
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "error", "error":str(e)}, 400
	def handleRequest(self, args):
		# args = parse_args_list(['email', 'key'])
		resp = account.verify(args['email'], args['key'])
		if resp.json()['status'] == 'OK':
			return
		raise Exception(resp.json()['error'])

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
			return make_response(render_template('index.html', username=username),200,headers)

		return make_response(render_template('login.html'),200,headers)
	def post(self):
		# validate user and password
		args = parse_args_list(['username', 'password'])
		resp = {}
		micro_resp = account.authenticate(args['username'], args['password'])
		users = get_users_coll()
		currUser = users.find_one({'username': args['username']})
		if micro_resp.json()['status'] == 'OK':
			#print('####################### verification' + currUser['verification'], sys.stderr)
			headers = {'Content-Type': 'application/json'}
			response = make_response(jsonify({"status": "OK"}), 200, headers)
			response.set_cookie('username', currUser['username'])
			response.set_cookie('password', currUser['password'])
			return response
		elif micro_resp.json()['error'] == 'not verified':
			resp['status'] = "error"
			resp['error'] = "User has not been validated. Check your email."
			# print('#######################not validated', file=sys.stderr)
			return resp, 400
		elif micro_resp.json()['error'] == 'incorrect password':
			resp['status'] = "error"
			resp['error'] = "The entered password is incorrect."
			# print('#######################wrong password', file=sys.stderr)
			return resp, 400
		else:
			resp['status'] = "error"
			resp['error'] = "The entered username doesn't exist."
			# print('#######################bad username:' + str(args['username']), file=sys.stderr)
			return resp, 400

class Logout(Resource):
	def post(self):
		# Update cookie to invalid one; no access to database bc cookie just serves to initialize the board upon login
		try:
			headers = {'Content-Type': 'application/json'}
			response = make_response(jsonify({"status": "OK"}), 200, headers)
			response.set_cookie('username', '', expires = 0)
			response.set_cookie('password', '', expires = 0)
			return response
		except Exception as e:
			print(e, sys.stderr)
			return {'status': "error"}, 400

class AddQuestion(Resource):
	def post(self):
		# authenticate cookie, 
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		print('add question, username: {}, password: {}'.format(username, password), sys.stderr)
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'error':
			return resp.json(), 400
		parser = reqparse.RequestParser()
		parser.add_argument('title')
		parser.add_argument('body')
		parser.add_argument('tags', action='append')
		parser.add_argument('media', action='append')
		args = parser.parse_args()
		if args.get('title') is None:
			return _error('title required')
		elif args.get('body') is None:
			return _error('body required')
		elif args.get('tags') is None:
			return _error('tags required')
		resp = questions.add_question(args['title'], args['body'], args['tags'], username, args['media'])
		if resp.json()['status'] == 'error':
			return _error(resp.json().get('error') if resp.json().get('error') is not None else 'failed to add question')
		return resp.json()

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
		if resp2.json()['status'] == 'error':
			return {"status": "error"}, 400
		#print("#######################" + str(resp2), sys.stderr)
		return resp2.json()
	
	def delete(self, id):
		# check if user is logged in
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		user = None
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'OK':
			user = username
		else:
			user = request.remote_addr
			return {'status': 'error', 'error': 'not logged in'}, 400
		resp2 = questions.delete_question(id=id, user=user)
		if resp2.json()['status'] == 'error':
			return {'status': 'error', 'error': 'wrong user'}, 400
		#print("#######################" + str(resp2), sys.stderr)
		return resp2.json()


class AddAnswer(Resource):
	def post(self, id):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		if resp.json()['status'] == 'error':
			return resp.json(), 400
		parser = reqparse.RequestParser()
		parser.add_argument('body')
		parser.add_argument('media', action='append')
		args = parser.parse_args()
		if args.get('body') is None:
			return {'status': 'error', 'error':'body is required'}, 400
		resp2 = questions.add_answer(body=args['body'], username=username, id=id, media=args.get('media'))
		return resp2.json()

class Search(Resource):
	def post(self):
		parser = reqparse.RequestParser()
		parser.add_argument('timestamp', type=float)
		parser.add_argument('limit', type=int)
		parser.add_argument('q')
		parser.add_argument('sort_by')
		parser.add_argument('tags', action='append')
		parser.add_argument('has_media', type=inputs.boolean)
		parser.add_argument('accepted', type=inputs.boolean)
		args = parser.parse_args()
		#print('$$$$$$$$$$$$$$$$$$$$$$$$$$args:' + str(args), sys.stderr)
		timestamp = args['timestamp'] if args['timestamp'] is not None else time.time()
		limit = args.get('limit')
		if args['limit'] is not None:
			if args['limit'] > 100:
				limit = 100
		else:
			limit = 25
		if args['q'] == '':
			args['q'] = None
		# accepted = args['accepted'] if args['accepted'] is not None else False
		resp = questions.search(timestamp, limit, args['q'], args['sort_by'], 
									args['tags'], args['has_media'], args['accepted'])
		return resp.json()

class GetAnswers(Resource):
	def get(self, id):
		return questions.get_answers(id).json()

class TopTen(Resource):
	def get(self):
		return questions.get_topten().json()

class PostQuestion(Resource):
	def get(self):
		return make_response(render_template('addquestion.html'), 200, {'Content-Type': 'text/html'})

class GetUser(Resource):
	def get(self, username):
		#cookieuser = request.cookies.get('username')
		#password = request.cookies.get('password')
		#if cookieuser != username:
		#	return {'status': 'error'}
		#resp = account.authenticate(cookieuser, password)
		#if resp.json()['status'] == 'error':
		#	return resp.json()
		resp = account.getuser(username).json()
		if resp['status'] == 'error':
			return _error("Error in getting user for username {}".format(username))
		return resp

class GetUserQuestions(Resource):
	def get(self, username):
		#cookieuser = request.cookies.get('username')
		#password = request.cookies.get('password')
		#if cookieuser != username:
		#	return {'status': 'error'}
		#resp = account.authenticate(cookieuser, password)
		#if resp.json()['status'] == 'error':
		#	return resp.json()
		resp = account.getuserQ(username).json()
		if resp['status'] == 'error':
			return _error("Error in getting questions for user {}".format(username))
		return resp

class GetUserAnswers(Resource):
	def get(self, username):
		#cookieuser = request.cookies.get('username')
		#password = request.cookies.get('password')
		#if cookieuser != username:
	#		return {'status': 'error'}
		#resp = account.authenticate(cookieuser, password)
		#if resp.json()['status'] == 'error':
		#	return resp.json()
		resp = account.getuserA(username).json()
		if resp['status'] == 'error':
			return _error("Error in getting answers for user {}".format(username))
		return resp

class GetQuestionPage(Resource):
	def get(self, id):
		cookieuser = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(cookieuser, password)
		if resp.json()['status'] == 'error':
			cookieuser = None
		headers = {'Content-Type': 'text/html'}
		if cookieuser is None:
			return make_response(render_template('viewquestion.html', id=id))
		return make_response(render_template('viewquestion.html', id=id, username=cookieuser))

class UpvoteQuestion(Resource):
	def post(self, id):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		#print('---------------------' + str(resp.json()), sys.stderr)
		if resp.json()['status'] == 'error':
			#print('---------------------' + str('hellooo'), sys.stderr)
			return resp.json(), 400
		parser = reqparse.RequestParser()
		#print('******************************' + str('1st'), sys.stderr)
		parser.add_argument('upvote', type=inputs.boolean)
		#print('******************************' + str('2nd'), sys.stderr)
		args = parser.parse_args()
		#print('******************************' + str(args['upvote']), sys.stderr)
		action = None
		if args.get('upvote') is None:
			action = True
		else:
			action = args['upvote']
		#print(str(action) + '<- action', sys.stderr)
		return questions.upvote(action, id, username).json()
class UpvoteAnswer(Resource):
	def post(self, id):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		#print('---------------------' + str(resp.json()), sys.stderr)
		if resp.json()['status'] == 'error':
			#print('---------------------' + str('hellooo'), sys.stderr)
			return resp.json(), 400
		parser = reqparse.RequestParser()
		#print('******************************' + str('1st'), sys.stderr)
		parser.add_argument('upvote', type=inputs.boolean)
		#print('******************************' + str('2nd'), sys.stderr)
		args = parser.parse_args()
		#print('******************************' + str(args['upvote']), sys.stderr)
		action = None
		if args.get('upvote') is None:
			action = True
		else:
			action = args['upvote']
		print(str(action) + '<- action', sys.stderr)
		return questions.upvoteanswer(action, id, username).json()

class AcceptAnswer(Resource):
	def post(self, id):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		#print('---------------------' + str(resp.json()), sys.stderr)
		if resp.json()['status'] == 'error':
			#print('---------------------' + str('hellooo'), sys.stderr)
			return resp.json(), 400
		return questions.acceptanswer(id, username).json()


class AddMedia(Resource):
	def post(self):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(username, password)
		#print('---------------------' + str(resp.json()), sys.stderr)
		if resp.json()['status'] == 'error':
			#print('---------------------' + str('hellooo'), sys.stderr)
			return resp.json(), 400
		file = request.files.get('content')
		filetype = file.content_type
		#print('-------------------------' + str(file.content_type), sys.stderr)
		b = bytearray(file.read())
		b = base64.b64encode(b)
		# cluster = Cluster(['130.245.171.50'])
		# session = cluster.connect(keyspace='stackoverflow')
		media_id = self._generate_code()
		# cqlinsert = 'insert into media (id, content, type, added, poster) values (%s, %s, %s, %s, %s);'
		# session.execute(cqlinsert, (media_id, b, filetype, False, username))
		cols = '{},{}'.format(media_id, str(b))
		connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.122.23'))
		channel = connection.channel()
		channel.queue_declare(queue='cassandra', durable=True)
		channel.basic_publish(exchange='',routing_key='cassandra', body=cols)
		mongo = {}
		mongo['id'] = media_id
		mongo['type'] = filetype
		mongo['added'] = False
		mongo['poster'] = username
		mongo['collection'] = 'media'
		mongo['action'] = 'insert'
		dump = json.dumps(mongo)
		channel.queue_declare(queue='mongo', durable=True)
		channel.basic_publish(exchange='',routing_key='mongo', body=dump)
		resp = {}
		resp['status'] = 'OK'
		resp['id'] = media_id
		return resp
	def _generate_code(self):
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


class GetMedia(Resource):
	def get(self, id):
		# cluster = Cluster(['130.245.171.50'])
		# session = cluster.connect(keyspace='stackoverflow')
		cqlselect = "select id, content from media where id = '" + id + "';"
		rows = session.execute(cqlselect)
		if not rows:
			return {'status':'error'}, 400
		row = rows[0]
		file = row[1]
		#filetype = row[2]
		response = make_response(file)
		metadata = media.find_one({'id':id})
		filetype = metadata['type']
		response.headers.set('Content-Type', filetype)
		return response

class UserInfo(Resource):
	def get(self, username):
		cookieuser = request.cookies.get('username')
		password = request.cookies.get('password')
		resp = account.authenticate(cookieuser, password)
		if resp.json()['status'] == 'error':
			cookieuser = None
		headers = {'Content-Type': 'text/html'}
		if cookieuser is None or cookieuser != username:
			return make_response(render_template('userinfo.html', username=username))
		return make_response(render_template('userinfo.html', logged_in='yes', username=username))

class Reset(Resource):
	def get(self):
		return questions.reset().json()


def parse_args_list(argnames):
	parser = reqparse.RequestParser()
	for arg in argnames:
		parser.add_argument(arg)
	args = parser.parse_args()
	return args

def get_users_coll():
	return users

def _error(message):
		return {'status': 'error', 'error': message}, 400


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
api.add_resource(PostQuestion, '/postquestion')
api.add_resource(GetUser, '/user/<username>')
api.add_resource(GetUserQuestions, '/user/<username>/questions')
api.add_resource(GetUserAnswers, '/user/<username>/answers')
api.add_resource(GetQuestionPage, '/questions/<id>/page')
api.add_resource(UpvoteQuestion, '/questions/<id>/upvote')
api.add_resource(UpvoteAnswer, '/answers/<id>/upvote')
api.add_resource(AcceptAnswer, '/answers/<id>/accept')
api.add_resource(AddMedia, '/addmedia')
api.add_resource(GetMedia, '/media/<id>')
api.add_resource(Reset, '/reset')
api.add_resource(UserInfo, '/userinfo')


if __name__ == '__main__':
	app.run(debug=True)
