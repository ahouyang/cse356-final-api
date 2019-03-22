var board = {'grid':[' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']};
// var boardModel = [0,0,0,0,0,0,0,0,0];
const sleep = (milliseconds) => {
  return new Promise(resolve => setTimeout(resolve, milliseconds))
};
var gameover = false;



$(function(){
	console.log(board);

	// Load the board from the cookie
	var cookie = Cookies.get();
	console.log(cookie.grid.replace(/'/g, "\"").replace(/\\054/g,",").replace(/u/g,""));
	var correctGrid = cookie.grid.replace(/'/g, "\"").replace(/\\054/g,",").replace(/u/g,"");
	var initBoard = JSON.parse(correctGrid);

	for(let i = 0; i < initBoard.length; i++){
		$('#' + i).text(initBoard[i]);
		board.grid[i] = initBoard[i];
	}

	// Whenever a user makes a move
	$('.box-item').click((e)=>{
		console.log('in click handler');
		if(gameover){
			console.log('gameover');
			return;
		}
		if($('#' + e.target.id).text() == ' '){
			console.log('in if statement');
			$('#' + e.target.id).text('X');
			board.grid[e.target.id] = 'X';
			var grid = JSON.stringify(board['grid']);
			console.log(grid);
			console.log('run 4');
			// $.post('http://localhost:5000/ttt/play', $.param(board, true), (data) => {
			$.post('http://130.245.170.88/ttt/play', $.param({'move':e.target.id}, true), (data) => {
				sleep(500).then(() => {
					if(data.winner != ''){
						switch(data.winner){
							case 'X':
							case 'O':
								$('#winner').text(data.winner + ' is the winner!');
								gameover = true;
								break;
							case ' ':
								$('#winner').text('Tie!');
								gameover = true;
						}
					}
					for(let i = 0; i < data.grid.length; i++){
						$('#' + i).text(data.grid[i]);
						board.grid[i] = data.grid[i];
					}
				});
			});
		}
		console.log('outside if');
	});

	$('#listgames').click((e) => {
		$.post('http://130.245.170.88/listgames', (data, textStatus, xhr) => {
			$('#listgamesdiv').text(JSON.stringify(data));
		});
	});

	$('#getgame').click((e) => {
		$.post('http://130.245.170.88/getgame', $.param({'id': $('#gameID').val()}),(data) => {
			// Fill in getGame function here
			$('#getgamediv').text(JSON.stringify(data));
		});
	});

	$('#getscore').click((e) => {
		$.post('http://130.245.170.88/getscore', (data) => {
			// Fill in getGame function here
			$('#getscorediv').text(JSON.stringify(data));
		});
	});


	$('#submit').click((e)=>{
		$('.boxes').css('display', 'grid');
	});
});
