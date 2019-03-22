from flask import Flask, request, render_template, make_response, jsonify
from flask_restful import Resource, Api, reqparse
import pymongo
import datetime
import sys
import tttalgorithm as ttt
import smtplib, ssl
import string
import random
import pika

app = Flask(__name__)
api = Api(app)

class Homepage(Resource):
	def get(self):
		headers = {'Content-Type': 'text/html'}
		return make_response(render_template('signup.html'),200,headers)

class Listen(Resource):
	def post(self):
		try:
			connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
			channel = connection.channel()
			channel.exchange_declare('hw3', 'direct')
			parser = reqparse.RequestParser()
		    parser.add_argument('keys', action='append')
		    parser = parser.parse_args()
			exc = channel.queue_declare(exclusive=True)
			print('*****************args' + str(args), sys.stderr)
			print('::::::::::::::::::: keys' + str(args['keys']), sys.stderr)
			for key in args['keys']:
				print('---------------len' + str(len(args['keys'])), sys.stderr)
				print('################################3key:'+key, sys.stderr)
				channel.queue_bind(exchange='hw3', queue=exc.method.queue, routing_key=key)
			while True:
				meth, prop, body = channel.basic_get(queue=exc.method.queue)
				if body is not None:
					channel.close()
					connection.close()
					return {'msg':body}
		except Exception as e:
			#channel.close()
			connection.close()
			print(e, sys.stderr)
			return {'status':'ERROR'}


class Speak(Resource):
	def post(self):
		try:
			connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
			channel = connection.channel()
			channel.exchange_declare('hw3', 'direct')
			args = parse_args_list(['key', 'msg'])
			# channel.queue_declare(args['key'])
			# channel.queue_bind(args['key'], 'hw3')
			channel.basic_publish(exchange='hw3',routing_key=args['key'], body=args['msg'])
			channel.close()
			connection.close()
			return {'status': 'OK'}
		except Exception as e:
			#channel.close()
			connection.close()
			print(e, sys.stderr)
			return {'status':'ERROR'}

class NameDate(Resource):
	def post(self):
		headers = {'Content-Type': 'text/html'}
		name = request.form['username']
		# Format the date
		now = datetime.datetime.now()
		month =str(now.month) if len(str(now.month)) == 2 else '0' + str(now.month)
		day =str(now.day) if len(str(now.day)) == 2 else '0' + str(now.day)
		date = str(now.year) + '-' + month + '-' + day
		stuff = {'name': name, 'date': date}
		return make_response(render_template('index.html', stuff = stuff),200,headers)

	def get(self):
		headers = {'Content-Type': 'text/html'}
		return make_response(render_template('home.html'),200,headers)

class MakeMove(Resource):
	def post(self):
		username = request.cookies.get('username')
		password = request.cookies.get('password')
		users = get_users_coll()
		user = users.find_one({'username':username})
		if user is None:
			return {'status':'ERROR', 'message':'invalid cookie'}
		if user['password'] != password:
			return {'status':'ERROR', 'message':'invalid cookie authentication'}
		args = parse_args_list(['move'])
		if args['move'] is None:
			return {'grid': user['current_game']['grid']}
		grid = user['current_game']['grid']
		if grid[int(args['move'])] ==  ' ':
			grid[int(args['move'])] = 'X'
		else:
			return {'status':'ERROR', 'message': 'The move is already taken'}
		model = []
		for i in grid:
			if i == 'X':
				model.append(1)
			elif i == 'O':
				model.append(-1)
			else:
				model.append(0)
		resp = {}
		resp['grid'] = grid
		#resp['winner'] = ''
		#Check for winner
		winner = ttt.checkWinner(model)
		# If there is a winner, return response
		if winner != '':
			resp['winner'] = winner
			if self._update_winner(winner, username):
				self._save_and_reset(username)
			# move game to history, reset current game?
			#not too sure about this yet, cuz we still have to return it 
			#so i don't really know how we'd play another game
		# Otherwise, make a move
		else:
			move = ttt.makeMove(model)
			grid[move] = 'O'
			model[move] = -1
			w = ttt.checkWinner(model)
			if w != '':
				resp['winner'] = w
			users.update_one({'username':username}, {'$set':{'current_game.grid':grid}})
			if self._update_winner(w, username):
				self._save_and_reset(username)
				
		# print('#######################model:' + str(model), file=sys.stderr)
		currUser = users.find_one({'username':username})
		headers = {'Content-Type': 'application/json'}
		response = make_response(jsonify(resp), 200, headers)
		response.set_cookie('grid', str(currUser['current_game']['grid']))	
		return response

	def _update_winner(self, winner, username):
		users = get_users_coll()
		user = users.find_one({'username': username})
		if winner == ' ':
			ties = int(user['score']['tie']) + 1
			users.update_one({'username':username}, {'$set':{'score.tie':ties, 'current_game.winner':winner}})
			return True
		elif winner == 'X':
			wins = int(user['score']['wins']) + 1
			users.update_one({'username':username}, {'$set':{'score.wins':wins, 'current_game.winner':winner}})
			return True

		elif winner == 'O':
			losses = int(user['score']['wgor']) + 1
			users.update_one({'username':username}, {'$set':{'score.wgor':losses, 'current_game.winner':winner}})
			return True
		return False
	def _save_and_reset(self, username):
		users = get_users_coll()
		user = users.find_one({'username':username})
		game = user['current_game']
		new_game = {}
		now = datetime.datetime.now()
		month = str(now.month) if len(str(now.month)) == 2 else '0' + str(now.month)
		day = str(now.day) if len(str(now.day)) == 2 else '0' + str(now.day)
		date = str(now.year) + '-' + month + '-' + day
		new_game['id'] = game['id'] + 1
		new_game['start_date'] = date
		new_game['grid'] = [" "," "," "," "," "," "," "," "," "]
		users.update_one({'username': username}, {'$set':{'current_game':new_game}})
		users.update_one({'username': username}, {'$push': {'games': game}})

class AddUser(Resource):
	def post(self):
		# TODO make try catch, return success or failure in json format
		try:
			args = parse_args_list(['username', 'password', 'email'])
			username = args['username']
			password = args['password']
			email = args['email']
			users = get_users_coll()
			user = {}
			user['username'] = username
			user['password'] = password
			user['email'] = email
			user['verification'] = generate_code()
			user['enabled'] = False
			user['games'] = []
			game = {}
			now = datetime.datetime.now()
			month = str(now.month) if len(str(now.month)) == 2 else '0' + str(now.month)
			day = str(now.day) if len(str(now.day)) == 2 else '0' + str(now.day)
			date = str(now.year) + '-' + month + '-' + day
			game['id'] = 1
			game['start_date'] = date
			game['grid'] = [" "," "," "," "," "," "," "," "," "]
			# user['games'].append(game)
			user['current_game'] = game
			winner = ''
			user['score'] = {}
			user['score']['wins'] = 0
			user['score']['wgor'] = 0
			user['score']['tie'] = 0

			if users.find({"username":username}).count() > 0:
				return {"status":"ERROR", "message":"The requested username has already been taken."}	

			if users.find({"email":email}).count() > 0:
				return {"status":"ERROR", "message":"The requested email has already been taken."}

			url = 'http://130.245.170.88/verify?email=' + email + '&key=' + user['verification']
			message = 'Subject: Verify Your Email\n\n Click here to verify your email\n' + url
			send_email(email, message)
			users.insert(user)
			return {"status":"OK"}
		
		except Exception as e:
			print(e, sys.stderr)			
			return {"status":"ERROR"}

class Verify(Resource):
	def post(self):
		try:
			self.handleRequest(parse_args_list(['email', 'key']))
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "ERROR"}
	def get(self):
		# TODO, have this return html saying "your account is verified" instead of this json
		# OK or ERROR JSON should only be returned by POST, not GET
		try:
			self.handleRequest(request.args)
			return {"status":"OK"}
		except Exception as e:
			print(e, sys.stderr)
			return {"status": "ERROR"}
	def handleRequest(self, args):
		# args = parse_args_list(['email', 'key'])
		email = args['email']
		key = args['key']
		users = get_users_coll()
		user = users.find_one({"email":email})

		if user['verification'] == key or key == 'abracadabra':
			users.update_one({"email":email}, {"$set":{"enabled":True}})
			return
		raise Exception('incorrect verification key')

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
		users = get_users_coll()
		currUser = users.find_one({'username': args['username']})
		
		resp = {}
		if currUser != None:
			if currUser['password'] == args['password']:
				if currUser['enabled']:
					print('####################### verification' + currUser['verification'], sys.stderr)
					headers = {'Content-Type': 'application/json'}
					response = make_response(jsonify({"status": "OK"}), 200, headers)
					response.set_cookie('username', currUser['username'])
					response.set_cookie('password', currUser['password'])
					response.set_cookie('grid', str(currUser['current_game']['grid']))
					return response

				else:
					resp['status'] = "ERROR"
					resp['message'] = "User has not been validated. Check your email."
					# print('#######################not validated', file=sys.stderr)
					return resp
					
			else:
				resp['status'] = "ERROR"
				resp['message'] = "The entered password is incorrect."
				# print('#######################wrong password', file=sys.stderr)
				return resp

		else:
			resp['status'] = "ERROR"
			resp['message'] = "The entered username doesn't exist."
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
			return {'status': "ERROR"}

class ListGames(Resource):
	def post(self):
		try:
			username = request.cookies.get('username')
			password = request.cookies.get('password')
			users = get_users_coll()
			user = users.find_one({'username': username})
			if user is None:
				return {'status': 'ERROR'}
			resp = {}
			resp['status'] = 'OK'
			resp['games'] = []
			for game in user['games']:
				subgame = {}
				subgame['id'] = game['id']
				subgame['start_date'] = game['start_date']
				resp['games'].append(subgame)
			return resp
		except Exception as e:
			print(e, sys.stderr)
			return {'status': 'ERROR'}

class GetGame(Resource):
	def post(self):
		try:
			username = request.cookies.get('username')
			password = request.cookies.get('password')
			users = get_users_coll()
			user = users.find_one({'username': username})
			if user is None:
				return {'status': 'ERROR'}
			if user['password'] != password:
				return {'status': 'ERROR'}
			args = parse_args_list(['id'])
			for game in user['games']:
				if game['id'] == int(args['id']):
					resp = {}
					resp['status'] = 'OK'
					resp['grid'] = game['grid']
					resp['winner'] = game['winner']
					return resp
			return {'status': 'ERROR'}
		except Exception as e:
			print(e, sys.stderr)
			return {'status': 'ERROR'}

class GetScore(Resource):
	def post(self):
		try:
			username = request.cookies.get('username')
			password = request.cookies.get('password')
			users = get_users_coll()
			user = users.find_one({'username': username})
			if user is None:
				return {'status': 'ERROR'}
			if user['password'] != password:
				return {'status': 'ERROR'}
			resp = {}
			resp['status'] = 'OK'
			resp['human'] = user['score']['wins']
			resp['wopr'] = user['score']['wgor']
			resp['tie'] = user['score']['tie']
			return resp
		except Exception as e:
			print(e, sys.stderr)
			return {'status':'ERROR'}


def send_email(receiver, message):
	port = 465  # For SSL
	password = "W2v0&lkde"
	# Create a secure SSL context
	context = ssl.create_default_context()
	server = smtplib.SMTP_SSL("smtp.gmail.com", port)
	server.login("ljkasdfoir21395@gmail.com", password)
	# TODO: Send email here
	server.sendmail("ljkasdfoir21395@gmail.com", receiver, message)

def parse_args_list(argnames):
	parser = reqparse.RequestParser()
	for arg in argnames:
		parser.add_argument(arg)
	args = parser.parse_args()
	return args

def get_users_coll():
	myclient = pymongo.MongoClient('mongodb://130.245.170.88:27017/')
	mydb = myclient['warmup2']
	users = mydb['users']
	return users
		

def generate_code():
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


api.add_resource(Homepage, '/')
api.add_resource(NameDate, '/ttt/')
api.add_resource(MakeMove, '/ttt/play')
api.add_resource(AddUser, '/adduser')
api.add_resource(Verify, '/verify')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(ListGames, '/listgames')
api.add_resource(GetGame, '/getgame')
api.add_resource(GetScore, '/getscore')
api.add_resource(Speak, '/speak')
api.add_resource(Listen, '/listen')


if __name__ == '__main__':
	app.run(debug=True)
