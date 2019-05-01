$(function(){
	var username = $('meta[name=username]').attr("content");
	var logged_in_meta = $('meta[name=logged_in]').attr("content");
	var logged_in = logged_in_meta === 'yes' ? true : false;
	console.log('logged_in_meta:' + logged_in_meta + ' logged_in:' + logged_in);
	$.get('http://130.245.170.86/user/' + username, (data) => {
		if(data.status == 'OK'){
			$('#email').text('Email: ' + data.user.email);
			$('#reputation').text('Reputation: ' + data.user.reputation);
		}
	});


	$.get('http://130.245.170.86/user/' + username + '/questions', (data) => {
		if(data.status == 'OK'){
			var questions = data.questions;
			for(var i = 0; i < questions.length; i++){
				var id = questions[i];
				$.get('http://130.245.170.86/questions/' + id, (data) => {
					var question = data.question;
					$('#questions').append('<div id="' + question.id + '"></div>');
					$('#' + question.id).append('<h3 id="' + question.id + 'title"></h3>');
					$('#' + question.id).append('<div id="' + question.id + 'score"></div>');
					$('#' + question.id).append('<div id="' + question.id + 'body"></div>');
					$('#' + question.id).append('<div id="' + question.id + 'stamp"></div>');
					$('#' + question.id + 'title').text(question.title);
					$('#' + question.id + 'score').text('Score: ' + question.score);
					$('#' + question.id + 'body').html(question.body);
					var date = new Date(question.timestamp*1000);
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
					var posterstamp = 'Submitted by ' + question.user.username + ' on ' + formattedTime;
					// var stamp = "Submitted on " + question.timestamp;
					$('#' + question.id + 'stamp').text(posterstamp);
					if(logged_in){
						//add delete question button
						$('#' + question.id).append('<input type="button" id="delete_' + question.id + '" value="Delete" class="delete>');

					}
				});
			}
		}
	});

	$('.delete').click((event) => {
		var id = event.target.id;
		$.ajax({
		    url: 'http://130.245.170.86/questions/' + id,
		    type: 'DELETE',
		    success: function(result) {
		        if(result.status == 'OK'){
		        	$('#' + id).remove();
		        }
		    }
		});
	});



});
