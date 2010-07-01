<?php

require_once 'Horde.php';
require_once 'Horde/String.php';

/**
 * Turn text into HTML with varying levels of parsing.  For no html
 * whatsoever, use htmlspecialchars() instead.
 *
 * Parameters:
 * <pre>
 * parselevel -- The parselevel of the output. See the list of constants below.
 * charset    -- The charset to use for htmlspecialchars() calls.
 * class      -- The CSS class name for the links.
 * nofollow   -- Whether to set the 'rel="nofollow"' attribute on links.
 * callback   -- An optional callback function that the URL is passed through
 *               before being set as the href attribute.  Must be a string with
 *               the function name, the function must take the original as the
 *               first and only parameter.
 * </pre>
 *
 * <pre>
 * List of valid constants for the parse level:
 * --------------------------------------------
 * TEXT_HTML_PASSTHRU        =  No action. Pass-through. Included for
 *                              completeness.
 * TEXT_HTML_SYNTAX          =  Allow full html, also do line-breaks,
 *                              in-lining, syntax-parsing.
 * TEXT_HTML_MICRO           =  Micro html (only line-breaks, in-line linking).
 * TEXT_HTML_MICRO_LINKURL   =  Micro html (only line-breaks, in-line linking
 *                              of URLSs; no email addresses are linked).
 * TEXT_HTML_NOHTML          =  No html (all stripped, only line-breaks)
 * TEXT_HTML_NOHTML_NOBREAK  =  No html whatsoever, no line breaks added.
 *                              Included for completeness.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/text2html.php,v 1.4.2.15 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Text
 */
class Text_Filter_text2html extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('charset' => null,
                         'class' => 'fixed',
                         'nofollow' => false,
                         'callback' => 'Horde::externalUrl');

    /**
     * Constructor.
     *
     * @param array $params  Any parameters that the filter instance needs.
     */
    function Text_Filter_text2html($params = array())
    {
        parent::Text_Filter($params);

        // Use ISO-8859-1 instead of US-ASCII
        if (String::lower($this->_params['charset']) == 'us-ascii') {
            $this->_params['charset'] = 'iso-8859-1';
        }
    }

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        if (is_null($this->_params['charset'])) {
            $this->_params['charset'] = isset($GLOBALS['_HORDE_STRING_CHARSET'])
                ? $GLOBALS['_HORDE_STRING_CHARSET']
                : 'ISO-8859-1';
        }

        /* Abort out on simple cases. */
        if ($this->_params['parselevel'] == TEXT_HTML_PASSTHRU) {
            return $text;
        }
        if ($this->_params['parselevel'] == TEXT_HTML_NOHTML_NOBREAK) {
            return @htmlspecialchars($text, ENT_COMPAT, $this->_params['charset']);
        }

        if ($this->_params['parselevel'] < TEXT_HTML_NOHTML) {
            $filter_array = array('linkurls');
            $filter_params = array(
                array('callback' => $this->_params['callback'],
                      'nofollow' => $this->_params['nofollow'],
                      'encode' => true));
            if ($this->_params['parselevel'] < TEXT_HTML_MICRO_LINKURL) {
                $filter_array[] = 'emails';
                $filter_params[] = array('encode' => true);
            }
            $text = Text_Filter::filter($text, $filter_array, $filter_params);
        }

        /* For level TEXT_HTML_MICRO, TEXT_HTML_NOHTML, start with
         * htmlspecialchars(). */
        $old_error = error_reporting(0);
        $text2 = htmlspecialchars($text, ENT_COMPAT, $this->_params['charset']);
        /* Bad charset input in may result in an empty string. If so, try
         * using the default charset encoding instead. */
        if (!$text2) {
            $text2 = htmlspecialchars($text, ENT_COMPAT);
        }
        $text = $text2;
        error_reporting($old_error);

        /* Do in-lining of http://xxx.xxx to link, xxx@xxx.xxx to email. */
        if ($this->_params['parselevel'] < TEXT_HTML_NOHTML) {
            $text = Text_Filter_linkurls::decode($text);
            if ($this->_params['parselevel'] < TEXT_HTML_MICRO_LINKURL) {
                $text = Text_Filter_emails::decode($text);
            }

            $text = Text_Filter::filter($text, 'space2html');
        }

        /* Do the newline ---> <br /> substitution. Everybody gets this; if
         * you don't want even that, just use htmlspecialchars(). */
        return nl2br($text);
    }

}
