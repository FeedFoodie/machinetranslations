function navbarDropdown(id) {
  // On desktop, do nothing – hover handles it
  if (window.innerWidth >= 601) {
    return;
  }
  // Mobile: toggle dropdown
  var dropdown = document.getElementById(id);
  dropdown.classList.toggle("show");
  document.querySelectorAll('.dropdown-content.show').forEach(function(el) {
    if (el.id !== id) el.classList.remove('show');
  });
}
// Close the dropdown menu if the user clicks outside of it
window.onclick = function(e) {
	if (!e.target.matches('.dropbtn')) {
	var novelDropdown = document.getElementById("novelDropdown");
		if (novelDropdown.classList.contains('show')) {
			novelDropdown.classList.remove('show');
		}
	}
}