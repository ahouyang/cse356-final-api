$(()=>{
	$.post('http://130.245.170.86/topten', function(data, textStatus, xhr) {
		var questions = data.questions;
		for(var question in questions){
			$('#questions').append('<a href="http://" id="' + question.id + '" class="question"></div>');
			$('#' + question.id).append('<h2>' + question.title + '</h2><h4>' + question.body + '</h4>');
		}
	});
});