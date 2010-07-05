<?php

require_once 'Horde.php';

/**
 * The Text_Filter_bbcode:: class finds bbcode-style markup (see below) in a
 * block of text and turns it into HTML.
 *
 * Parameters:
 * <pre>
 * entities -- If true before replacing bbcode with HTML tags, any HTML
 *             entities will be replaced.
 * </pre>
 *
 * Supported bbcode:
 * <pre>
 *     [b]Bold Text[/b]
 *     [i]Italics Text[/i]
 *     [u]Underlined Text[/u]
 *     [quote]Quoted Text[/quote]
 *     [center]Centered Text[/center]
 *
 *     List of items
 *     [list]
 *     [*] Item one
 *     [*] Item two
 *     [/list]
 *
 *     Numbered list
 *     [numlist]
 *     [*] Item one
 *     [*] Item two
 *     [/numlist]
 *
 *     [url]http://www.horde.org[/url] -> Link to the address using the
 *         address itself for the text.  You can specify the protocol: http or
 *         https and the port.
 *     [url]www.horde.org[/url] -> Link to the address using the address
 *         itself for the text.  You can specify the port.  The protocol is by
 *         default http.
 *     [url=http://www.horde.org]Link to Horde[/url] -> Link to the address
 *         using "Link to Horde" for the text.  You can specify the protocol:
 *         http or https and the port.
 *     [url=www.horde.org]Link to Horde[/url] -> Link to the address using
 *         "Link to Horde" for the text.  You can specify the port.  The
 *         protocol is by default http
 *     [email]cpedrinaci@yahoo.es[/email] -> sets a mailto link.
 *     [email=cpedrinaci@yahoo.es]Mail to Carlos[/email] -> Sets a mailto link
 *         and the text is "Mail to Carlos".
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/bbcode.php,v 1.8.10.9 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * Email validation based on Chuck Hagenbuch's
 * Mail_RFC822::isValidInetAddress.
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Carlos Pedrinaci <cpedrinaci@yahoo.es>
 * @package Horde_Text
 */
class Text_Filter_bbcode extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('entities' => false);

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        if ($this->_params['entities']) {
            $text = @htmlspecialchars($text);
        }

        return $text;
    }

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $replace = array(
            '[i]' => '<em>', '[/i]' => '</em>',
            '[u]' => '<u>', '[/u]' => '</u>',
            '[b]' => '<strong>', '[/b]' => '</strong>',
            '[s]' => '<strike>', '[/s]' => '</strike>',
            '[sub]' => '<sub>', '[/sub]' => '</sub>',
            '[sup]' => '<sup>', '[/sup]' => '</sup>',
            '[center]' => '<center>', '[/center]' => '</center>',
            '[quote]' => '<blockquote>', '[/quote]' => '</blockquote>',
            '[list]' => '<ul>', '[/list]' => '</ul>',
            '[numlist]' => '<ol>', '[/numlist]' => '</ol>',
            '[*]' => '<li>');

        /* When checking URLs we validate part of them, but it is up
         * to the user to write them correctly (in particular the
         * query string). Concerning mails we use the regular
         * expression in Mail_RFC822's isValidInetAddress() function,
         * slightly modified. */
        $regexp = array(
            "#\[url\]((http|https)://([a-zA-Z\d][\w-]*)(\.[a-zA-Z\d][\w-]*)+(:(\d+))?(/([^<>]+))*)\[/url\]#U" =>
            Horde::link("$1", "$1") . "$1</a>",

            "#\[url\=((http|https)://([a-zA-Z\d][\w-]*)(\.[a-zA-Z\d][\w-]*)+(:(\d+))?(/([^<>]+))*)\]([^<>]+)\[/url\]#U" =>
            Horde::link("$1", "$1") . "$9</a>",

            "#\[url\](([a-zA-Z\d][\w-]*)(\.[a-zA-Z\d][\w-]*)+(:(\d+))?(/([^<>]+))*)\[/url\]#U" =>
            Horde::link("http://$1", "http://$1") . "$1</a>",

            "#\[url\=(([a-zA-Z\d][\w-]*)(\.[a-zA-Z\d][\w-]*)+(:(\d+))?(/([^<>]+))*)\]([^<>]+)\[/url\]#U" =>
            Horde::link("http://$1", "http://$1") . "$8</a>",

            "#\[email\](([*+!.&\#$|\'\\%\/0-9a-zA-Z^_`{}=?~:-]+)@(([0-9a-zA-Z-]+\.)+[0-9a-zA-Z]{2,4}))\[/email\]#U" =>
            Horde::link("mailto:$1", "mailto:$1") . "$1</a>",

            "#\[email\=(([*+!.&\#$|\'\\%\/0-9a-zA-Z^_`{}=?~:-]+)@(([0-9a-zA-Z-]+\.)+[0-9a-zA-Z]{2,4}))\]([^<>]+)\[/email\]#U" =>
            Horde::link("mailto:$1", "mailto:$1") . "$5</a>",

            "#\[img\](.*)\[/img\]#U" =>
            "<img src=\"$1\" alt=\"$1\" />",

            "#\[img\=(.*)\](.*)\[/img\]#U" =>
            "<img src=\"$1\" alt=\"$2\" title=\"$2\" />",

            "#\[color\=(.*)\](.*)\[/color\]#U" =>
            "<span style=\"color: $1;\">$2</span>"

        );

        return array('replace' => $replace, 'regexp' => $regexp);
    }

}
