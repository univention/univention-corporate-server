<?php
// The function print_help() expects the following functions to be callable:
//     print_help_title($lang): prints out the title of the module in the specific language
//     print_help_text($lang): prints out the html code of the help text in the specific language
function print_help($lang) {
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="<?php echo $lang; ?>">
<head>
<title>Univention <?php print_help_title(); ?></title>
<link rel="SHORTCUT ICON" href="/icon/about.png" />
<link rel="stylesheet" href="/style/stylesheet.css" type="text/css" media="screen" title="style.css" charset="utf-8" />
<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
<style type="text/css">
/* necessary to make the background image in help_container repeat correctly;
   this is also in 'stylesheet.css', but just in case... */
body {
	height: 100%;
}

/* this element is centered on the page and contains all other elements;
   it also contains a repeating background image */
div#help_container {
	background-image: url("/style/help_text_background.png");
	background-repeat:repeat-y;
	width: 506px;
	min-height: 100%;
	text-align: left;
	margin-left:auto;
	margin-right:auto;
}

/* modifications for the inherited header from 'stylesheet.css' */
div#header {
	background-image: url("/style/help_header_background.png");
	background-repeat: no-repeat;
	width: 506px;
	height: 110px;
	position: relative;
	left: 0px;
}

/* modifications for the inherited header-title from 'stylesheet.css' */
div#header .header-title {
	top: 54px;
}

/* some padding information to make the text fit nicely to the log */
div#help_textcontainer {
	padding: 0px 15px 5px 15px;
}

/* padding information for paragraphs */
div#help_textcontainer p {
	margin: 10px;
	text-align: justify;
}

/* the red triangles for HTML lists */
div#help_textcontainer ul li {
	background-image: url("/style/bullet.gif");
	background-repeat: no-repeat;
	background-position: 0px 2px;
	list-style-type: none;
	margin-bottom:7px;
	padding-left:13px;
	margin: 10px;
}
div#help_textcontainer ul {
	margin-bottom: 16px;
}

</style>
</head>
<body>
<div id="help_container">
<div id="header">
<h1 class="header-title">
	<span class="hide">univention</span> <a href="#" title="Start"><?php print_help_title($lang); ?></a>
</h1>
</div>
<div id="help_textcontainer">
<?php print_help_text($lang); ?>
</div>
</div>
</body>

</html>
<?php
}
?>
