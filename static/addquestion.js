$(function(){
	$('#postquestion').click(function(event) {
		var request = {};
		request.title = $('#title').val();
		request.body = $('#body').val();
		var tagstring = $('#tags').val();
		var tags = tagstring.split(' ');
		request.tags = tags;
		console.log(request);
		$.post('http://130.245.170.86/questions/add', $.param(request, true), (data, status, xhr) => {
				if(data.status == "OK"){
					$('#submitted').text('Question Posted!');
					$('#postquestion').attr("disabled", 'true');
				}
				else{
					$('#submitted').text(data.message);
				}
			});
	});
});
