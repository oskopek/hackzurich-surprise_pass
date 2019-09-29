


//jQuery time
var current_fs, next_fs, previous_fs; //fieldsets
var left, opacity, scale; //fieldset properties which we will animate
var animating; //flag to prevent quick multi-click glitches
var stage = 0;

var today = new Date();
var h = today.getHours() + 2;
if (h >= 24)
	h = 24 - h;

if (h < 10)
	h = '0' + h;
var time = h + ":" + today.getMinutes();


var dd = today.getDate();
var mm = today.getMonth()+1; //January is 0!
var yyyy = today.getFullYear();
max_mm = mm + 2;
if (max_mm > 12)
	max_mm -= 12;

if (max_mm < 10)
	max_mm = '0' + max_mm;

if (mm < 10)
	mm = '0' + mm;

if (dd < 10)
	dd = '0' + dd;

date = yyyy + '-' + mm + '-' + dd;
max_date = yyyy + '-' + max_mm + '-' + dd;

document.getElementById("date").setAttribute("max", max_date);
document.getElementById("date").setAttribute("value", date);
document.getElementById("date").setAttribute("min", date);

document.getElementById("departure").setAttribute("value", "00:00");
document.getElementById("departure").setAttribute("min", "00:00");

$(".next").click(function(){
	stage++;

	if(animating) return false;
	animating = true;
	
	current_fs = $(this).parent();
	next_fs = $(this).parent().next();
	
	//activate next step on progressbar using the index of next_fs
	$("#progressbar li").eq($("fieldset").index(next_fs)).addClass("active");
	
	//show the next fieldset
	next_fs.show();
	//hide the current fieldset with style
	current_fs.animate({opacity: 0}, {
		step: function(now, mx) {
			//as the opacity of current_fs reduces to 0 - stored in "now"
			//1. scale current_fs down to 80%
			scale = 1 - (1 - now) * 0.2;
			//2. bring next_fs from the right(50%)
			left = (now * 50)+"%";
			//3. increase opacity of next_fs to 1 as it moves in
			opacity = 1 - now;
			current_fs.css({
        'transform': 'scale('+scale+')',
        'position': 'absolute' });

			next_fs.css({'left': left, 'opacity': opacity});
		},
		duration: 800, 
		complete: function(){
			current_fs.hide();
			animating = false;
		}, 
		//this comes from the custom easing plugin
		easing: 'easeInOutBack'
	});

	var delayInMilliseconds = 800; //1 second
	if (stage == 2) {
		var x = document.getElementById("wait");
    	x.removeAttribute("hidden");
		setTimeout(function() {
			document.getElementById("msform").submit();
			}, delayInMilliseconds);
	}
});

$(".previous").click(function(){
	if(animating) return false;
	animating = true;
	
	current_fs = $(this).parent();
	previous_fs = $(this).parent().prev();
	
	//de-activate current step on progressbar
	$("#progressbar li").eq($("fieldset").index(current_fs)).removeClass("active");
	
	//show the previous fieldset
	previous_fs.show(); 
	//hide the current fieldset with style
	current_fs.animate({opacity: 0}, {
		step: function(now, mx) {
			//as the opacity of current_fs reduces to 0 - stored in "now"
			//1. scale previous_fs from 80% to 100%
			scale = 0.8 + (1 - now) * 0.2;
			//2. take current_fs to the right(50%) - from 0%
			left = ((1-now) * 50)+"%";
			//3. increase opacity of previous_fs to 1 as it moves in
			opacity = 1 - now;
			current_fs.css({'left': left});
			previous_fs.css({'transform': 'scale('+scale+')', 'opacity': opacity});
		}, 
		duration: 800, 
		complete: function(){
			current_fs.hide();
			animating = false;
		}, 
		//this comes from the custom easing plugin
		easing: 'easeInOutBack'
	});
});

$(".submit").click(function(){
	return false;
})