
$(function(){
	$('#submit').click((e)=>{
		var user = $('#user').val();
		var pass = $('#pass').val();

		var validation = {'username':user, 'password':pass};
		// console.log(validation);
		// validation.username = user;
		// validation.password = pass;
		var stringJson = JSON.stringify(validation);

		$.post('http://130.245.170.86/login', $.param(validation, true), (data, status, xhr) => {
			var cookie = Cookies.get();
			// cookie.grid.replace(/'/g, "\"");
			// console.log(JSON.parse(cookie.grid.replace(/'/g, "\"").replace(/\\054/g,",")));
			console.log(cookie);
			if(data.status == "OK"){
				$('#error').text('');
				$('#playgame').css('visibility', 'visible');
			}
			else{
				$('#error').text(data.message);
			}

		});
	});
});
