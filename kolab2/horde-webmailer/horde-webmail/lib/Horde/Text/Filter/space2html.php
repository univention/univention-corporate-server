<?php
/**
 * The space2html filter converts horizontal whitespace to HTML code.
 *
 * Parameters:
 * <pre>
 * encode     -- HTML encode the text?  Defaults to false.
 * charset    -- Charset of the text.  Defaults to ISO-8859-1.
 * encode_all -- Replace all spaces with &nbsp;?  Defaults to false.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/space2html.php,v 1.1.10.9 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Mathieu Arnold <mat@mat.cc>
 * @package Horde_Text
 */
class Text_Filter_space2html extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('encode' => false,
                         'charset' => 'ISO-8859-1',
                         'encode_all' => false);

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        if ($this->_params['encode']) {
            $text = @htmlspecialchars($text, ENT_COMPAT, $this->_params['charset']);
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
        $replace = array("\t" => '&nbsp; &nbsp; &nbsp; &nbsp; ',
                         '  ' => '&nbsp; ');
        return array('replace' => $replace);
    }

    /**
     * Executes any code necessaray after applying the filter patterns.
     *
     * @param string $text  The text after the filtering.
     *
     * @return string  The modified text.
     */
    function postProcess($text)
    {
        $text = str_replace('  ', ' &nbsp;', $text);
        if ($this->_params['encode_all']) {
            $text = str_replace(' ', '&nbsp;', $text);
        }
        return $text;
    }

}
