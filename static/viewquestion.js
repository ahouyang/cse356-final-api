$(function(){
	var questionID = $('meta[name=questionID]').attr("content");
	$.get('http://130.245.170.86/questions/' + questionID, (data, status, xhr) => {
		$('#title').text(data.title);
		$('#body').text(data.body);
		var posterstamp = 'Submitted by ' + data.user.username + ' on ' + data.timestamp;
		$('#posterstamp').text(posterstamp);
		var views = 'View Count: ' + data.view_count;
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
			$('#' + answer.id + 'body').text(answer.body);
			var stamp = "Submitted on " + data.timestamp;
			$('#' + answer.id + 'stamp').text(stamp);
		}
	});
});
