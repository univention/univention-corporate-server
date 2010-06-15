<?php

require_once dirname(__FILE__) . '/../Filter.php';
require_once 'Text/reST.php';
require_once 'Text/reST/Formatter.php';

/**
 * The Text_Filter_rst:: class.  Filter to convert reStructuredText to
 * HTML.
 *
 * $Horde: framework/Text/Text/Filter/rst.php,v 1.5 2004/04/07 14:43:13 chuck Exp $
 *
 * Copyright 2003-2004 Jason M. Felice <jfelice@cronosys.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jason M. Felice <jfelice@cronosys.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Text
 */
class Text_Filter_rst extends Text_Filter {

    /**
     * Add links to all urls.
     *
     * @access public
     *
     * @param string $text  The text to filter.
     *
     * @return string  The text reformatted to HTML.
     */
    function filter($text)
    {
        $document = &Text_reST::parse($text);
        $formatter = &Text_reST_Formatter::factory('html');
        return $formatter->format($document, NLS::getCharset());
    }

}

