<?php

require_once dirname(__FILE__) . '/../Filter.php';

/**
 * The Text_Filter_bbcode:: class finds bbcode-style markup (see
 * below) in a block of text and turns it into HTML.
 *
 * Supported bbcode:
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
 *     [url]http://www.horde.org[/url] -> Link to the address using the address itself for the text
 *                                        You can specify the protocol: http or https and the port
 *     [url]www.horde.org[/url] -> Link to the address using the address itself for the text 
 *                                 You can specify the port. The protocol is by default http
 *     [url=http://www.horde.org]Link to Horde[/url] -> Link to the address using "Link to Horde" for the text
 *                                                      You can specify the protocol: http or https and the port
 *     [url=www.horde.org]Link to Horde[/url] -> Link to the address using "Link to Horde" for the text 
 *                                               You can specify the port. The protocol is by default http
 *     [email]cpedrinaci@yahoo.es[/email] -> sets a mailto link
 *     [email=cpedrinaci@yahoo.es]Mail to Carlos[/email] -> Sets a mailto link and the text is "Mail to Carlos"
 *
 * $Horde: framework/Text/Text/Filter/bbcode.php,v 1.3 2004/01/01 15:14:34 jan Exp $
 *
 * Copyright 2003-2004 Carlos Pedrinaci <cpedrinaci@yahoo.es>
 *
 * Email validation based on Chuck Hagenbuch's
 * Mail_RFC822::isValidInetAddress.
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Carlos Pedrinaci <cpedrinaci@yahoo.es>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Text
 */
class Text_Filter_bbcode extends Text_Filter {

    /**
     * Convert bbcode into HTML.
     *
     * @access public
     *
     * @param string  $text      The text to filter.
     * @param boolean $entities  If true before replacing bbcode with HTML tags,
     *                           any HTML entities will be replaced. Useful for chaining filters.
     *
     * @return string  The transformed text.
     */
    function filter($text, $entities = false)
    {
    	if ($entities) {
    		$text = @htmlspecialchars($text);
    	}

        return parent::filter($text, Text_Filter_bbcode::getPatterns());
    }

    /**
     * Returns an array with the patterns to be replaced.  For
     * performance reasons the array is split in str_replace
     * (result['replace']) and regexps patterns result['regexp'] =>
     * array(link, name) for correct formatting of the links.
     *
     * @access protected
     */
    function getPatterns()
    {
    	$replace = array(
    	    '[i]' => '<i>', '[/i]' => '</i>', '[u]' => '<u>', '[/u]' => '</u>', '[b]' => '<b>', '[/b]' => '</b>',
            '[center]' => '<center>', '[/center]' => '</center>', '[quote]' => '<blockquote>', 
            '[/quote]' => '</blockquote>', '[list]' => '<ul>', '[/list]' => '</ul>', '[numlist]' => '<ol>',
            '[/numlist]' => '</ol>', '[*]' => '<li>');

        // When checking URLs we validate part of them, but it is up
        // to the user to write them correctly (in particular the
        // query string). Concerning mails we use the regular
        // expression in Mail_RFC822::isValidInetAddress but slightly
        // modified.
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
            Horde::link("mailto:$1", "mailto:$1") . "$5</a>"
        );

        return array('replace' => $replace, 'regexp' => $regexp);
    }

}
