<?php

define('TEXT_HTML_PASSTHRU', 0);
define('TEXT_HTML_SYNTAX', 1);
define('TEXT_HTML_REDUCED', 2);
define('TEXT_HTML_MICRO', 3);
define('TEXT_HTML_NOHTML', 4);
define('TEXT_HTML_NOHTML_NOBREAK', 5);

/**
 * The Text:: class provides common methods for manipulating text.
 *
 * $Horde: framework/Text/Text.php,v 1.107 2004/05/25 02:05:52 chuck Exp $
 *
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Text
 */
class Text {

    /**
     * Filter the given text based on the words found in $words.
     *
     * @access public
     *
     * @param string $text         The text to filter.
     * @param string $words_file   Filename containing the words to replace.
     * @param string $replacement  The replacement string.
     *
     * @return string  The filtered version of $text.
     */
    function filter($text, $words_file, $replacement)
    {
        if (@is_readable($words_file)) {
            /* Read the file and iterate through the lines. */
            $lines = file($words_file);
            foreach ($lines as $line) {
                /* Strip whitespace and comments. */
                $line = trim($line);
                $line = preg_replace('|#.*$|', '', $line);

                /* Filter the text. */
                if (!empty($line)) {
                    $text = preg_replace("/(\b(\w*)$line\b|\b$line(\w*)\b)/i",
                                         $replacement, $text);
                }
            }
        }

        return $text;
    }

    /**
     * Fixes incorrect wrappings which split double-byte gb2312
     * characters.
     *
     * @since Horde 2.2
     *
     * @access public
     *
     * @param string $text  String containing wrapped gb2312 characters
     * @param $break_char   Character used to break lines.
     *
     * @return string  String containing fixed text.
     */
    function trim_gb2312($str, $break_char = "\n")
    {
        $lines = explode($break_char, $str);

        $iMax = count($lines) - 1;
        for ($i = 0; $i < $iMax; $i++) {
                $line = $lines[$i];
                $len = strlen($line);

                /* parse double-byte gb2312 characters */
                for ($c = 0; $c < $len - 1; $c++) {
                        if (ord($line{$c}) & 128) {
                                if (ord($line{$c + 1}) & 128) $c++;
                        }
                }

                /* If the last character of the current line is the first byte
                   of a double-byte character, move it to the start of the
                   next line. */
                if (($c == $len - 1) && (ord($line[$c]) & 128)) {
                        $lines[$i] = substr($line, 0, -1);
                        $lines[$i + 1] = $line[$c] . $lines[$i + 1];
                }
        }
        return implode($break_char, $lines);
    }

    /**
     * Wraps the text of a message.
     *
     * @access public
     *
     * @param string $text                 String containing the text to wrap.
     * @param optional integer $length     Wrap $text at this number of
     *                                     characters.
     * @param optional string $break_char  Character(s) to use when breaking
     *                                     lines.
     * @param optional string $charset     Character set to use when breaking
     *                                     lines.
     * @param optional boolean $quote      Ignore lines that are wrapped with
     *                                     the '>' character (RFC 2646)? If
     *                                     true, we don't remove any padding
     *                                     whitespace at the end of the
     *                                     string.
     *
     * @return string  String containing the wrapped text.
     */
    function wrap($text, $length = 80, $break_char = "\n", $charset = null,
                  $quote = false)
    {
        $paragraphs = array();

        $gb2312 = 0;
        if (!is_null($charset) && (strtolower($charset) == 'gb2312')) {
            $gb2312 = 1;
        }

        foreach (explode("\n", $text) as $input) {
            if ($quote && (strpos($input, '>') === 0)) {
                $line = $input;
            } else {
                /* We need to handle the Usenet-style signature line
                 * separately; since the space after the two dashes is
                 * REQUIRED, we don't want to trim the line. */
                if ($input != '-- ') {
                    $input = rtrim($input);
                }
                $line = wordwrap($input, $length, $break_char, $gb2312);
            }

            if ($gb2312) {
                $paragraphs[] = Text::trim_gb2312($line, $break_char);
            } else {
                $paragraphs[] = $line;
            }
        }

        return implode($break_char, $paragraphs);
    }

    /**
     * Turns all URLs in the text into hyperlinks.
     *
     * @access public
     *
     * @param string $text               The text to be transformed.
     * @param optional boolean $capital  Sometimes it's useful to generate <A>
     *                                   and </A> so you can know which tags
     *                                   you just generated.
     * @param optional string $class     The CSS class the links should be
     *                                   displayed with.
     *
     * @return string  The linked text.
     */
    function linkUrls($text, $capital = false, $class = '')
    {
        $a = 'a';

        if ($capital) {
            $a = 'A';
            /* Make sure that the original message doesn't contain any
             * capital </A> tags or open <A> tags , so we can assume
             * we generated them. */
            $text = str_replace(array('</A>', '<A'), array('</a>', '<a'), $text);
        }

        if (!empty($class)) {
            $class = ' class="' . $class . '"';
        }

        /* Prepend a space to make sure we can always catch links at
         * the very beginning of the first line. */
        $text = ' ' . $text;


        /* Get all possible URLs and store their position in the
         * text. */
        preg_match_all('|(\w+)://([^\s"<]*[\w+#?/&=])|', $text, $matches, PREG_SET_ORDER);

        /* Loop through the text replacing all the matched urls. */
        $offset = 0;
        foreach ($matches as $match) {
            $offset = strpos($text, $match[0], $offset);
            $url = Horde::externalUrl(trim($match[0]));
            $new = '<' . $a . ' href="' . $url . '" target="_blank"' . $class . '>' . $match[0] . '</' . $a . '>';
            /* Replace URL with link using match offset. */
            $text = substr_replace($text, $new, $offset, strlen($match[0]));

            /* Increase offset to compensate for more characters in link. */
            $offset += (strlen($new) - strlen($match[0]));
        }

        /* Take the leading space back off. */
        return substr($text, 1);
    }

    /**
     * Turn all mailto: strings in the text into Horde mail/compose
     * links.
     *
     * @access public
     *
     * @param string $text              The text to be transformed.
     * @param optional string $charset  The charset to use for
     *                                  htmlspecialchars() calls.
     *
     * @return string  The text with mailtos transformed into compose links.
     */
    function linkMailtos($text, $charset = null)
    {
        global $registry;

        /* Make sure we have a safe charset. */
        if (is_null($charset)) {
            $charset = NLS::getCharset();
        }
        if ((strtolower($charset) == 'us-ascii') ||
            !NLS::checkCharset($charset)) {
            $charset = 'iso-8859-1';
        }

        /**
         * @TODO: someone needs to document this.
         */
        $pattern = '|(\[\s+)*([Mm][Aa][Ii][Ll][Tt][Oo]):(\s?)([^\s\?(?(1)\])"<]*)(\??)([^\s"<]*[\w+#?/&=])?|e';

        return @preg_replace($pattern, "'\\2:\\3<A href=\"' . str_replace('&amp;', '&', \$registry->call('mail/compose', array(array('to' => '\\4')), '&\\6')) . '\" onmouseover=\"status=\'' . htmlspecialchars(addslashes(sprintf(_(\"Compose Message (%s)\"), '\\4')), ENT_QUOTES, $charset) . '\'; return true;\" onmouseout=\"status=\'\';\">\\4\\5\\6</A>'", $text);
    }

    /**
     * Re-convert links generated by Text::linkUrls() to working
     * hrefs, after htmlspecialchars() has been called on the
     * text. This is an awkward chain, but necessary to filter out
     * other HTML.
     *
     * @since Horde 2.1
     *
     * @access public
     *
     * @param string $text             The text to convert.
     * @param optional string $target  The link target.
     * @param optional string $class   The css class name for the links
     *
     * @return string  The converted text.
     */
    function enableCapitalLinks($text, $target = '_blank', $class = 'fixed')
    {
        $syntax = array(
            '&lt;A href=&quot;' => '<a' . (empty($class) ? '' : ' class="' . $class) . '" href="',
            '&quot; target=&quot;_blank&quot;&gt;'  => '" target="' . $target . '">',
            '&quot; onmouseover=&quot;' => '" onmouseover="',
            '&quot; onmouseout=&quot;' => '" onmouseout="',
            '\');&quot;&gt;' => '\');">',
            '&quot;&gt;' =>  '">',
            /* Only reconvert capital /A tags - the ones we
             * generated. */
            '&lt;/A&gt;' => '</a>'
        );

        return str_replace(array_keys($syntax), $syntax, $text);
    }

    /**
     * Replace occurences of %VAR% with VAR, if VAR exists in the
     * webserver's environment. Ignores all text after a '#' character
     * (shell-style comments).
     *
     * @access public
     *
     * @param string $text  The text to expand.
     *
     * @return string  The expanded text.
     */
    function expandEnvironment($text)
    {
        if (preg_match("|([^#]*)#.*|", $text, $regs)) {
            $text = $regs[1];

            if (strlen($text) > 0) {
                $text = $text . "\n";
            }
        }

        while (preg_match("|%([A-Za-z_]+)%|", $text, $regs)) {
            $text = preg_replace("|%([A-Za-z_]+)%|", getenv($regs[1]), $text);
        }
        return $text;
    }

    /**
     * Convert a line of text to display properly in HTML.
     *
     * @param string $text  The string of text to convert.
     *
     * @return string  The HTML-compliant converted text.
     */
    function htmlSpaces($text = '')
    {
        $text = @htmlspecialchars($text, ENT_COMPAT, NLS::getCharset());
        $text = str_replace("\t", '&nbsp; &nbsp; &nbsp; &nbsp; ', $text);
        $text = str_replace('  ', '&nbsp; ', $text);
        $text = str_replace('  ', ' &nbsp;', $text);

        return $text;
    }

    /**
     * Same as htmlSpaces() but converts all spaces to &nbsp;
     * @see htmlSpaces()
     *
     * @param string $text  The string of text to convert.
     *
     * @return string  The HTML-compliant converted text.
     */
    function htmlAllSpaces($text = '')
    {
        $text = Text::htmlSpaces($text);
        $text = str_replace(' ', '&nbsp;', $text);

        return $text;
    }

    /**
     * Removes some common entities and high-ascii or otherwise
     * nonstandard characters common in text pasted from Microsoft
     * Word into a browser.
     *
     * This function should NOT be used on non-ASCII text; it may and
     * probably will butcher other character sets
     * indescriminately. Use it only to clean US-ASCII (7-bit) text
     * which you suspect (or know) may have invalid or non-printing
     * characters in it.
     *
     * @since Horde 2.1
     *
     * @access public
     *
     * @param string $text  The text to be cleaned.
     *
     * @return string  The cleaned text.
     */
    function cleanASCII($text)
    {
        // Remove control characters.
        $text = preg_replace('/[\x00-\x1f]+/', '', $text);

        /* The 'Â' entry may look wrong, depending on your editor,
           but it's not - that's not really a single quote. */
        $from = array('Â', 'Â', 'Â', 'Â', 'Â', 'Â', 'Â', 'Â', 'Â', 'Â·', chr(167), '&#61479;', '&#61572;', '&#61594;', '&#61640;', '&#61623;', '&#61607;', '&#61553;', '&#61558;', '&#8226;', '&#9658;');
        $to   = array('...',     "'", "'",    '"',    '"',    '*',    '-',    '-',    '*', '*',      '*',        '.',        '*',        '*',        '-',        '-',        '*',        '*',        '*',       '*',       '>');

        return str_replace($from, $to, $text);
    }

    /**
     * Turn text into HTML with varying levels of parsing.
     * For no html whatsoever, use htmlspecialchars() instead.
     *
     * @since Horde 2.2
     *
     * @access public
     *
     * @param string $input             An url-decoded string, \n-separated
     *                                  for lines.
     * @param integer $parselevel       The parselevel of the output. See the
     *                                  list of constants below.
     * @param optional string $charset  The charset to use for
     *                                  htmlspecialchars() calls.
     * @param optional string $class    The css class name for the links.
     *
     * <pre>
     * List of valid constants for $parselevel:
     * ----------------------------------------
     * TEXT_HTML_PASSTHRU        =  No action. Pass-through. Included for
     *                              completeness.
     * TEXT_HTML_SYNTAX          =  Allow full html, also do line-breaks,
     *                              in-lining, syntax-parsing.
     * TEXT_HTML_REDUCED         =  Reduced html (bold, links, etc. by syntax
     *                              array).
     * TEXT_HTML_MICRO           =  Micro html (only line-breaks, in-line
     *                              linking).
     * TEXT_HTML_NOHTML          =  No html (all stripped, only line-breaks)
     * TEXT_HTML_NOHTML_NOBREAK  =  No html whatsoever, no line breaks added.
     *                              Included for completeness.
     * </pre>
     *
     * @return string  The converted HTML.
     */
    function toHTML($text, $parselevel, $charset = null, $class = 'fixed')
    {
        $syntax = array(
            'B' => '<b>',
            '/B' => '</b>',
            'I' => '<i>',
            '/I' => '</i>',
            'U' => '<u>',
            '/U' => '</u>',
            'Q'   => '<blockquote>',
            '/Q' => '</blockquote>',
            'LIST' => '<ul>',
            '/LIST' => '</ul>',
            '*' => '<li>'
        );

        if (is_null($charset)) {
            $charset = NLS::getCharset();
        }
        if ((strtolower($charset) == 'us-ascii') ||
            !NLS::checkCharset($charset)) {
            $charset = 'iso-8859-1';
        }

        /* Abort out on simple cases. */
        if ($parselevel == TEXT_HTML_PASSTHRU) {
            return $text;
        }
        if ($parselevel == TEXT_HTML_NOHTML_NOBREAK) {
            return htmlspecialchars($text, ENT_QUOTES, $charset);
        }

        /* Find tags we recognize with this parselevel and translate them to
           <tag> ==> [tag]
           and then translate the rest < --> &lt; > --> &gt; */
        if ($parselevel == TEXT_HTML_REDUCED) {
            foreach ($syntax as $k => $val) {
                $text = str_replace('<' . $k . '>', '[' . $k . ']', $text);
                $k = strtolower($k);
                $text = str_replace('<' . $k . '>', '[' . $k . ']', $text);
            }
        }

        /* Interpret tags for parse levels TEXT_HTML_SYNTAX and
           TEXT_HTML_REDUCED. */
        if ($parselevel <= TEXT_HTML_REDUCED) {
            foreach ($syntax as $k => $v) {
                $text = str_replace('[' . $k . ']', $v, $text);
                $text = str_replace('<' . $k . '>', $v, $text);
                $k = strtolower($k);
                $text = str_replace('[' . $k . ']', $v, $text);
                $text = str_replace('<' . $k . '>', $v, $text);
            }
        }

        /* Do in-lining of http://xxx.xxx to link, xxx@xxx.xxx to email,
           part one. */
        if ($parselevel < TEXT_HTML_NOHTML) {
            /* Make sure that the original message doesn't contain any
               capital </A> tags or open <A> tags , so we can assume we
               generated them. */
            $text = str_replace(array('</A>', '<A'), array('</a>', '<a'), $text);

            $text = Text::linkUrls($text, true);
            $text = Text::linkMailtos($text, $charset);
        }

        /* For level TEXT_HTML_MICRO, TEXT_HTML_NOHTML, start with
           htmlspecialchars(). */
        $text = htmlspecialchars($text, ENT_QUOTES, $charset);

        /* Do in-lining of http://xxx.xxx to link, xxx@xxx.xxx to email,
           part two. */
        if ($parselevel < TEXT_HTML_NOHTML) {
            $text = Text::enableCapitalLinks($text, '_blank', $class);
        }

        /* Do the blank-line ---> <br /> substitution.
           Everybody gets this; if you don't want even that, just save
           the htmlspecialchars() version of the input. */
        $text = nl2br($text);

        return $text;
    }

    /**
     * Highlights quoted messages with different colors for the
     * different quoting levels. CSS class names called "quoted1"
     * .. "quoted$level" must be present.
     *
     * @since Horde 2.2
     *
     * @access public
     *
     * @param string $text             The text to be highlighted.
     * @param optional integer $level  The maximum numbers of different
     *                                 colors.
     *
     * @return string  The highlighted text.
     */
    function highlightQuotes($text, $level = 5)
    {
        // Use a global var since the class is called statically.
        $GLOBALS['_tmp_maxQuoteChars'] = 0;

        // Tack a newline onto the beginning of the string so that we
        // correctly highlight when the first character in the string
        // is a quote character.
        $text = "\n$text";

        preg_replace_callback("/^\s*((&gt;\s?)+)/m", array('Text', '_countQuoteChars'), $text);

        // Go through each level of quote block and put the
        // appropriate style around it. Important to work downwards so
        // blocks with fewer quote chars aren't matched until their
        // turn.
        for ($i = $GLOBALS['_tmp_maxQuoteChars']; $i > 0; $i--) {
            $text = preg_replace(
                // Finds a quote block across multiple newlines.
                "/(\n)( *(&gt;\s?)\{$i}(?! ?&gt;).*?)(\n|$)(?! *(&gt; ?)\{$i})/s",
                '\1<span class="quoted' . ((($i - 1) % $level) + 1) . '">\2</span>\4',
                $text
            );
        }

        /* Unset the global variable. */
        unset($GLOBALS['_tmp_maxQuoteChars']);

        /* Remove the leading newline we added above. */
        return substr($text, 1);
    }

    /**
     * Called by the preg_replace_callback function in
     * highlightQuotes(). This method finds the maximum number of
     * quote characters in all of the quote blocks.
     *
     * @access private
     *
     * @param array $matches  The matches from the regexp.
     */
    function _countQuoteChars($matches)
    {
        $num = count(preg_split('/&gt;\s?/', $matches[1])) - 1;
        if ($num > $GLOBALS['_tmp_maxQuoteChars']) {
            $GLOBALS['_tmp_maxQuoteChars'] = $num;
        }
    }

    /**
     * Highlights simple markup as used in emails or usenet postings.
     *
     * @param string $text  The text to highlight
     *
     * @return  The text with markups being highlighted by html tags.
     */
    function simpleMarkup($text)
    {
        // bold
        $text = preg_replace('/(\s|\n)(\*[^*\s]+\*)(\s|\r|\n|<br)/i', '\1<b>\2</b>\3', $text);
        // underline
        $text = preg_replace('/(\s|\n)(_[^_\s]+_)(\s|\r|\n|<br)/i', '\1<u>\2</u>\3', $text);
        // italic
        $text = preg_replace(';(\s|\n)(/[^/\s]+/)(\s|\r|\n|<br);i', '\1<i>\2</i>\3', $text);

        return $text;
    }

    /**
     * Displays message signatures marked by a '-- ' in the style of
     * the CSS class "signature". Class names inside the signature are
     * prefixed with "signature-".
     *
     * @since Horde 2.2
     *
     * @access public
     *
     * @param string $text  The text to be changed.
     *
     * @return string  The changed text.
     */
    function dimSignature($text)
    {
        $parts = preg_split('|(\n--\s*(<br />)?\r?\n)|', $text, 2, PREG_SPLIT_DELIM_CAPTURE);
        $text = array_shift($parts);
        if (count($parts)) {
            $text .= '<span class="signature">' . $parts[0];
            $text .= preg_replace('|class="([^"]+)"|', 'class="signature-\1"', $parts[2]);
            $text .= '</span>';
        }

        return $text;
    }

    /**
     * Expand tabs into spaces
     *
     * @author Marc Jauvin <marc@register4less.com>
     *
     * @access public
     *
     * @param string $text                 The text to expand.
     * @param optional integer $tabstop    Expand Tabs into that many spaces.
     * @param optional string $break_char  Character(s) to use when breaking
     *                                     lines.
     *
     * @return string  The text after tab expansion.
     */
    function smartExpandTabs($text, $tabstop = 8, $break_char = "\n")
    {
        $lines = explode($break_char, $text);
        for ($i = 0; $i < count($lines); $i++) {
            while(($pos = strpos($lines[$i], "\t")) !== false) {
                $n_space = $tabstop - ($pos % $tabstop);
                $new_str = str_repeat(' ', $n_space);
                $lines[$i] = substr_replace($lines[$i], $new_str, $pos, 1);
            }
        }
        return implode("\n", $lines);
    }

}

/**
 * Takes HTML and converts it to formatted, plain text.
 *
 * Copyright 2003-2004 Jon Abernathy <jon@chuggnutt.com>
 * Original source: http://www.chuggnutt.com/html2text.php
 *
 * @author  Jon Abernathy <jon@chuggnutt.com>
 * @version $Horde: framework/Text/Text.php,v 1.107 2004/05/25 02:05:52 chuck Exp $
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_HTMLConverter {

    /**
     * Contains the HTML content to convert.
     *
     * @var string $_html
     */
    var $_html = '';

    /**
     * Maximum width of the formatted text, in columns.
     *
     * @var integer $_width
     */
    var $_width = 70;

    /**
     * List of preg* regular expression patterns to search for,
     * used in conjunction with $replace.
     *
     * @see $replace
     *
     * @var array $_search
     */
    var $_search = array(
        "/\r/",                                  // Non-legal carriage return
        "/\n+/",                                 // Newlines
        "/\t+/",                                 // Tabs
        '/<script[^>]*>.*?<\/script>/i',         // <script>s -- which strip_tags() supposedly has problems with
        '/<style[^>]*>.*?<\/style>/i',           // <style>s -- which strip_tags() supposedly has problems with
        //'/<!-- .* -->/',                       // Comments -- which strip_tags() might have problem a with
        '/<h[123][^>]*>(.+?)<\/h[123]>/ie',      // H1 - H3
        '/<h[456][^>]*>(.+?)<\/h[456]>/ie',      // H4 - H6
        '/<p[^>]*>/i',                           // <P>
        '/<br[^>]*>/i',                          // <br>
        '/<b[^>]*>(.+?)<\/b>/ie',                // <b>
        '/<i[^>]*>(.+?)<\/i>/i',                 // <i>
        '/(<ul[^>]*>|<\/ul>)/i',                 // <ul> and </ul>
        '/<li[^>]*>/i',                          // <li>
        '/<a href="([^"]+)"[^>]*>(.+?)<\/a>/ie', // <a href="">
        '/<hr[^>]*>/i',                          // <hr>
        '/(<table[^>]*>|<\/table>)/i',           // <table> and </table>
        '/<tr[^>]*>/i',                          // <tr>
        '/<td[^>]*>(.+?)<\/td>/i',               // <td> and </td>
        '/&nbsp;/i',
        '/&quot;/i',
        '/&gt;/i',
        '/&lt;/i',
        '/&amp;/i',
        '/&copy;/i',
        '/&trade;/i'
    );

    /**
     * List of pattern replacements corresponding to patterns searched.
     *
     * @see $_search
     *
     * @var array $_replace
     */
    var $_replace = array(
        '',                                     // Non-legal carriage return
        '',                                     // Newlines
        ' ',                                    // Tabs
        '',                                     // <script>s -- which strip_tags() supposedly has problems with
        '',                                     // <style>s -- which strip_tags() supposedly has problems with
        //'',                                   // Comments -- which strip_tags() might have problem a with
        "strtoupper(\"\n\n\\1\n\n\")",          // H1 - H3
        "ucwords(\"\n\n\\1\n\n\")",             // H4 - H6
        "\n\n\t",                               // <P>
        "\n",                                   // <br>
        'strtoupper("\\1")',                    // <b>
        '_\\1_',                                // <i>
        "\n\n",                                 // <ul> and </ul>
        "\n\t* ",                               // <li>
        '$this->_buildLinkList($link_count++, "\\1", "\\2")',
                                                // <a href="">
        "\n-------------------------\n",        // <hr>
        "\n\n",                                 // <table> and </table>
        "\n\t",                                 // <tr> and </tr>
        "\\1\t\t",                              // <td> and </td>
        ' ',
        '"',
        '>',
        '<',
        '&',
        '(c)',
        '(tm)'
    );

    /**
     * Contains URL addresses from links to be rendered in plain text.
     *
     * @var string $_linkList
     */
    var $_linkList;

    /**
     * Constructor.
     *
     * If the HTML source string (or file) is supplied, the class
     * will instantiate with that source propagated, all that has
     * to be done it to call getText().
     *
     * @access public
     *
     * @param optional string $source      HTML content.
     * @param optional boolean $from_file  Indicates $source is a file to
     *                                     pull content from.
     */
    function Text_HTMLConverter($source = null, $from_file = false)
    {
        if (!is_null($source)) {
            $this->setHtml($source, $from_file);
        }
    }

    /**
     * Loads source HTML into memory, either from $source string or a
     * file.
     *
     * @access public
     *
     * @param string $source               HTML content.
     * @param optional boolean $from_file  Indicates $source is a file to
     *                                     pull content from.
     */
    function setHtml($source, $from_file = false)
    {
        $this->_html = $source;

        if ($from_file && file_exists($source)) {
            $fp = fopen($source, 'r');
            $this->_html = fread($fp, filesize($fp));
            fclose($fp);
        }
    }

    /**
     * Returns the text, converted from HTML.
     *
     * First performs custom tag replacement specified by $search and
     * $replace arrays. Then strips any remaining HTML tags, reduces
     * whitespace and newlines to a readable format, and word wraps the
     * text to $width characters.
     *
     * @access public
     *
     * @return string  The converted text.
     */
    function getText()
    {
        /* Variables used for building the link list. */
        $link_count = 1;
        $this->_linkList = '';

        $text = trim($this->_html);

        /* Run our defined search-and-replace. */
        $text = preg_replace($this->_search, $this->_replace, $text);

        /* Strip any other HTML tags. */
        $text = strip_tags($text);

        /* Bring down number of empty lines to 2 max. */
        $text = preg_replace("/\n[[:space:]]+\n/", "\n\n", $text);
        $text = preg_replace("/[\n]{3,}/", "\n\n", $text);

        /* Add link list. */
        if (!empty($this->_linkList)) {
            $text .= "\n\n" . _("Links") . ":\n------\n" . $this->_linkList;
        }

        /* Wrap the text to a readable format. */
        $text = wordwrap($text, $this->_width);

        return $text;
    }

    /**
     *  Helper function called by preg_replace() on link replacement.
     *
     *  Maintains an internal list of links to be displayed at the end of the
     *  text, with numeric indices to the original point in the text they
     *  appeared.
     *
     *  @access private
     *
     *  @param integer $link_count  Counter tracking current link number.
     *  @param string $link         URL of the link.
     *  @param string $display      Part of the text to associate number with.
     *
     *  @return string  The regex used by preg_replace().
     */
    function _buildLinkList($link_count, $link, $display)
    {
        $this->_linkList .= "[$link_count] $link\n";
        return $display . '[' . $link_count . ']';
    }

}
