/*global XMLHttpRequest,document*/
function expand(path) {
	"use strict";
	var request, lines, i, item;

	request = new XMLHttpRequest();
	request.open("GET", path, false);
	request.send(null);

	lines = request.responseText.split("\n");
	for (i = 0; i < lines.length - 1; i += 1) {
		item = lines[i].split('; ');
		document.write("<tr>");
		document.write("<td>" + item[0] + "</td>");
		document.write("<td>");
		document.write("<a href=\"" + item[1] + "\" class=\"htmlLink\">HTML</a>");
		document.write("<a href=\"" + item[2] + "\" class=\"pdfLink\">PDF</a>");
		document.write("</td>");
		document.write("</tr>");
	}
}
