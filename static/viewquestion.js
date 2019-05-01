$(function(){
	var questionID = $('meta[name=questionID]').attr("content");
	var upvoted = false;
	var downvoted = false;
	// var score = null;
	$.get('http://130.245.170.86/questions/' + questionID, (data, status, xhr) => {
		console.log(data);
		$('#title').text(data.question.title);
		$('#body').html(data.question.body);
		$('#score').text('Score: ' + data.question.score);
		score = data.question.score;
		var date = new Date(data.question.timestamp*1000);
		var year = date.getFullYear();
		var day = date.getDate();
		var month = date.getMonth() + 1;
		// Hours part from the timestamp
		var hours = date.getHours();
		// Minutes part from the timestamp
		var minutes = "0" + date.getMinutes();
		// Seconds part from the timestamp
		var seconds = "0" + date.getSeconds();
		// Will display time in 10:30:23 format
		var formattedTime = year + '-' + month + '-' + day + ', ' + hours + ':' 
		 + minutes.substr(-2) + ':' + seconds.substr(-2);
		var poster = '<a href="http://130.245.170.86/userinfo/' + data.question.user.username + '">' + 
				data.question.user.username + '</a>';
		var posterstamp = 'Submitted by ' + poster + ' on ' + formattedTime;
		$('#posterstamp').html(posterstamp);
		var views = 'View Count: ' + data.question.view_count;
		$('#view_count').text(views);
	});

	$.get('http://130.245.170.86/questions/' + questionID + '/answers', (data, status, xhr) => {
		var answers = data.answers;
		for(var i = 0; i < answers.length; i++){
			var answer = answers[i];
			$('#answers').append('<div id="' + answer.id + '"></div>');
			$('#' + answer.id).append('<h4 id="' + answer.id + 'user"></h4>');
			$('#' + answer.id).append('<div id="' + answer.id + 'score"></div>');
			$('#' + answer.id).append('<input type="button" id="upvote_' + answer.id + '" value="Upvote" class="upvote">');
			$('#' + answer.id).append('<input type="button" id="downvote_' + answer.id + '" value="Downvote" class="downvote">');
			$('#' + answer.id).append('<div id="' + answer.id + 'body"></div>');
			$('#' + answer.id).append('<div id="' + answer.id + 'stamp"></div>');
			$('#' + answer.id + 'user').text(answer.user);
			$('#' + answer.id + 'score').text('Score: ' + answer.score);
			$('#' + answer.id + 'body').html(answer.body);
			var date = new Date(answer.timestamp*1000);
			var year = date.getFullYear();
			var day = date.getDate();
			var month = date.getMonth() + 1;
			// Hours part from the timestamp
			var hours = date.getHours();
			// Minutes part from the timestamp
			var minutes = "0" + date.getMinutes();
			// Seconds part from the timestamp
			var seconds = "0" + date.getSeconds();
			// Will display time in 10:30:23 format
			var formattedTime = year + '-' + month + '-' + day + ', ' + hours + ':' 
			 + minutes.substr(-2) + ':' + seconds.substr(-2);
			var poster = '<a href="http://130.245.170.86/userinfo/' + answer.user + '">' + 
				answer.user + '</a>';
			var posterstamp = 'Submitted by ' + poster + ' on ' + formattedTime;
			// var stamp = "Submitted on " + answer.timestamp;
			$('#' + answer.id + 'stamp').html(posterstamp);



		}
	});

	$('#postanswer').click((event) => {
		var body = {};
		body.body = $('#postanswerbody').val();
		$.post('http://130.245.170.86/questions/' + questionID + '/answers/add', $.param(body), (data, textStatus, xhr) => {
			if(data.status == 'OK'){
				$('#success').text('Answer Posted!');
				$('#postanswer').attr("disabled", 'true');
			}
		});
	});
	function upvote(up){
		$.post('http://130.245.170.86/questions/' + questionID + '/upvote', $.param({'upvote':up}), (data, textStatus, xhr) => {
			if(data.status == 'OK'){
				console.log('up:' + up + 'upvoted:'+upvoted+'downvoted'+downvoted+'score'+score);
				$('#score').text('Score:' + data.score);
			}
		});
	}

	$('#upvotequestion').click((event) => {
		upvote(true);
	});
	$('#downvotequestion').click((event) => {
		upvote(false);
	});

	$(document).on('click', '.upvote', (event) => {
		var idtag = event.target.id;
		var answerid = idtag.substring(7, idtag.length);
		upvote_answer(true, answerid);
	});

	$(document).on('click', '.downvote', (event) => {
		var idtag = event.target.id;
		var answerid = idtag.substring(9, idtag.length);
		upvote_answer(9, answerid);
	});

	function upvote_answer(up, id){
		$.post('http://130.245.170.86/answers/' + answer + '/upvote', $.param({'upvote':up}), (data, textStatus, xhr) => {
			if(data.status == 'OK'){
				// console.log('up:' + up + 'upvoted:'+upvoted+'downvoted'+downvoted+'score'+score);
				$('#' + id + 'score').text('Score:' + data.score);
			}
		});
	}



});
