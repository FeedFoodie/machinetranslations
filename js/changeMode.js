window.onload = function() {
  if(localStorage.getItem('fontSize')) {
		var storedSize = localStorage.getItem('fontSize');
		setFontSize(storedSize);
	}
	if(localStorage.getItem('colorScheme')) {
		var storedColor = localStorage.getItem('colorScheme');
		setMode(storedColor);
	}
}

// Set Font Size Automatically
function setFontSize(value) {
	document.getElementById("content").style.fontSize = value;
	var quote = document.getElementsByClassName("night-mode-quotes");
		for (var i = 0; i < quote.length; i++) {
			quote[i].style.fontSize = value;
		}
}

// Set Day/Night Mode Automatically
function setMode(value) {
	if (value == "day") {
		document.getElementById("wrappertext").classList.toggle("day-mode");
		document.getElementById("chapterTitle").classList.toggle("day-mode-heading");
		var quotes = document.getElementsByClassName("night-mode-quotes");
		for (var i = 0; i < quotes.length; i++) {
			quotes[i].classList.toggle("day-mode-quotes")
		}
	}
}

// Change Font Size
var currentSize = 0;
var selectedSize = 0;
function changeFontSize(change) {	
	if (change == '0') {
		selectedSize = "16px";
		localStorage.setItem('fontSize', selectedSize);
		document.getElementById("content").style.fontSize = selectedSize;
		var quote = document.getElementsByClassName("night-mode-quotes");
		for (var i = 0; i < quote.length; i++) {
			quote[i].style.fontSize = selectedSize;
		}
	}
	else {
		currentSize = parseInt(document.getElementById("content").style.fontSize);
		selectedSize = currentSize + change + 'px';
		localStorage.setItem('fontSize', selectedSize);
		document.getElementById("content").style.fontSize = selectedSize;
		var quote = document.getElementsByClassName("night-mode-quotes");
		for (var i = 0; i < quote.length; i++) {
			quote[i].style.fontSize = selectedSize;
		}
	}
}

//Change Color
function changeWrapColor() {
	document.getElementById("wrappertext").classList.toggle("day-mode");
	document.getElementById("chapterTitle").classList.toggle("day-mode-heading");
	var quotes = document.getElementsByClassName("night-mode-quotes");
	for (var i = 0; i < quotes.length; i++) {
		quotes[i].classList.toggle("day-mode-quotes")
	}
	if (document.getElementById("wrappertext").classList.contains("day-mode")) {
		localStorage.setItem('colorScheme', "day");
	}
	else {
		localStorage.setItem('colorScheme', "night");
	}
}

document.addEventListener('DOMContentLoaded', function() { var coll = document.getElementsByClassName('collapsible'); for (var i = 0; i < coll.length; i++) { coll[i].addEventListener('click', function() {  this.classList.toggle('active');  var content = this.nextElementSibling;   if (content.style.maxHeight) {  content.style.maxHeight = null;  } else {  content.style.maxHeight = content.scrollHeight + 'px'; }});}});