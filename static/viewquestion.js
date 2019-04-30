$(function(){
	var questionID = $('meta[name=questionID]').attr("content");
	var upvoted = false;
	var downvoted = false;
	var score = null;
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
		var posterstamp = 'Submitted by ' + data.question.user.username + ' on ' + formattedTime;
		$('#posterstamp').text(posterstamp);
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
			var posterstamp = 'Submitted by ' + answer.user + ' on ' + formattedTime;
			// var stamp = "Submitted on " + answer.timestamp;
			$('#' + answer.id + 'stamp').text(posterstamp);
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
				if(up && upvoted){
					$('#score').text('Score:' + (score - 1));
					upvoted = false;
				}
				else if(up && downvoted){
					$('#score').text('Score:' + (score + 2));
					upvoted = true;
					downvoted = false;
				}
				else if(up){
					$('#score').text('Score:' + (score + 1));
					upvoted = true;
				}
				else if(!up && upvoted){
					$('#score').text('Score:' + (score - 2));
					upvoted = false;
					downvoted = true;
				}
				else if(!up && downvoted){
					$('#score').text('Score:' + (score + 1));
					downvoted = false;
				}
				else if(!up){
					$('#score').text('Score:' + (score - 1));
					downvoted = false;
				}
			}
		});
	}

	$('#upvotequestion').click((event) => {
		upvote(true);
	});
	$('#downvotequestion').click((event) => {
		upvote(false);
	});

});
