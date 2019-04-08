$(function(){
	console.log('hello');
	$.get('http://130.245.170.86/topten', function(data, textStatus, xhr) {
		console.log(data);
		var questions = data.questions;
		for(var i = 0; i < questions.length; i++){
			var question = questions[i];
			console.log(question);
			$('#questions').append('<a href="http://" id="' + question.id + '" class="question"></a>');
			$('#' + question.id).append('<h2>' + question.title + '</h2><h4>' + question.body + '</h4>');
		}
	});
});
