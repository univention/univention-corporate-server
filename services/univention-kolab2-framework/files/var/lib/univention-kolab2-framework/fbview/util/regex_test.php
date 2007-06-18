<?php
/**
 * Simple script to help with regex construction/debugging. Put it somewhere
 * on your webserver and point your browser to it.
 *
 * Based on: http://myfluffydog.com/programming/php/scripts/regexp.php
 */

require 'Horde/Util.php';
$regexp = Util::getFormData('regexp');
$subject = Util::getFormData('subject');
$submit = Util::getFormData('submit');

set_time_limit (2);

function unhtmlentities($string)
{
    $trans_tbl = get_html_translation_table(HTML_ENTITIES);
    $trans_tbl = array_flip($trans_tbl);
    return strtr($string, $trans_tbl);
}

if ($submit == "Test") { // doing a reg expression search -- get variables
    $unescapedRegexp = unhtmlentities($regexp); // for search
    $escapedRegexp = htmlentities($regexp); // for showing on page and in textarea
    $text = $subject;
    $text = stripslashes($text);
    $text = unhtmlentities($text); // for search
    $escapedText = htmlentities($text);// for textarea

    // Do preg_replace on source, substituting matched_text with [b]matched_text[/b]
    $highlightedText = preg_replace($unescapedRegexp, '[b]\\0[/b]', $text);
    // convert htmlentities
    $highlightedText = htmlentities($highlightedText);
    // replace [b] with <b> and [/b] with </b>
    $highlightedText = str_replace('[b]', '<span class="highlight">', $highlightedText);
    $highlightedText = str_replace('[/b]', '</span>', $highlightedText);
}
?>
<html>
<head>
<title>Test regular expressions</title>
<style type="text/css">
<!--
h1 {
    font-size: large;
}
.fixed {
    font-size: 10px;
    font-family: monospace,fixed;
    color: #000099;
    background-color: #cccccc;
}
.notes {
    font-size: small;
    color: #000099;
    background-color: #cccccc;
}
.highlight {
    color: #000066;
    background-color: #ffff00;
}
.empty {
    background-color: #ff9933
}
-->
</style>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<body bgcolor="#FFFFFF">
<h1>Test <a href="http://www.php.net/manual/en/ref.pcre.php">PHP Regular Expression Functions (Perl-Compatible)</a></h1>
<div class="fixed">preg_match_all($pattern, $subject, $matches, PREG_SET_ORDER)</div>
<form name="form1" method="post" action="<?php echo $PHP_SELF?>">
<p><strong>Enter your regular expression ($pattern):</strong><br />
<textarea name="regexp" cols="80" rows="6" id="regexp"><?php if($submit){echo $escapedRegexp;}?></textarea>
<br />
<strong>Enter text to search against in the textarea below ($subject):</strong><br />
<textarea name="subject" cols="80" rows="3"><?php if($subject){echo $escapedText;}?></textarea>
<br />
<input type="submit" name="submit" value="Test">
<input type="reset" name="Reset" value="Reset">
<a href='<?php echo $PHP_SELF?>'>Home</a><br />
</p>
</form>
<hr>
<?php
if ($submit){ // only shows up on results page
    if (preg_match_all($unescapedRegexp, $text, $results, PREG_SET_ORDER)) { // found match
        echo "The regexp <strong> $escapedRegexp </strong> matched!\n<p>";
        echo "<h1>Here's what was matched searching the text you entered:</h1>\n";
        $y = 0;
        echo '<div class="fixed">';
        foreach ($results as $loop_result) {
            $x = 0;
            foreach ($loop_result as $loop_result2){
                if ($x != 0) {
                    /* Indent subpatterns. */
                    echo "<blockquote>";
                }
                printf('$matches[%s][%s]:&nbsp;&nbsp;', $y, $x);// show variable name
                if (!$loop_result2){
                    echo '<span class="empty">Empty</span>';
                } else {
                    echo '<span class="highlight">' . htmlentities($loop_result2) . '</span>';
                }
                if ($x != 0) {
                    echo "</blockquote>";
                } else {
                    echo "<p />";
                }
                $x++;
            }
            $y++;
        }
        echo '</div>';
    } else { // no match
        echo "regexp <strong> $escapedRegexp </strong> doesn't return any results\n<p>";
    }
    ?>
    <h1>Searched text with matches <span class='highlight'>highlighted</span></h1>
    <?php // Show searched text with matches highlighted
    echo '<pre>';
    echo $highlightedText;
    echo '</pre><hr>';
}
?>

<div class="notes">
<h1>Example regular expressions:</h1>
<p><strong>{&lt;!--(?:.|\s)*?--&gt;}</strong>&nbsp; --&nbsp; Shows comments in html&nbsp;</p>
<ul>
<li><strong>{</strong> open delimiter</li>
<li><strong>&lt;!--</strong> search for opening comment tag</li>
<li><strong>(?:.|\s)*</strong> any number of characters or white space</li>
<li><strong>?</strong> non-greedy</li>
<li><strong>--&gt;</strong> search for closing comment tag</li>
<li><strong>}</strong> close delimiter</li>
</ul>
<p><strong>{&lt;style type(?:.|\s)*?&lt;/style&gt;}</strong> -- Shows  styles</p>
<p>Notes:</p>
<ul>
<li>The results page shows the individual matches and subpattern matches, and the original text with the matches highlighted.</li>
<li>Might not be able to search for html entities like "&amp;amp;" because of the converting for display and textareas (the search pattern (regexp) and non-url subjects are processed by unhtmlentities)</li>
</ul></div>
</body>
</html>
