<?php

require_once dirname(__FILE__) . '/../Filter.php';

/**
 * The Text_Filter_emails:: class finds email addresses in a block of
 * text and turns them into links.
 *
 * $Horde: framework/Text/Text/Filter/emails.php,v 1.4 2004/01/01 15:14:34 jan Exp $
 *
 * Copyright 2003-2004 Tyler Colbert <tyler-hordeml@colberts.us>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Tyler Colbert <tyler-hordeml@colberts.us>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Text
 */
class Text_Filter_emails extends Text_Filter {

    /**
     * Add links to all email addresses, including those in mailto:
     * urls.
     *
     * @access public
     *
     * @param string $text    The text to filter.
     * @param array  $params  Any filtering parameters.
     *
     * @return string  The text with any email addresses linked.
     */
    function filter($text, $params = array())
    {
        return parent::filter($text, Text_Filter_emails::getPatterns($params));
    }

    function getPatterns($params = array())
    {
        /* If we have a mail/compose registry method, use it. */
        if ($GLOBALS['registry']->hasMethod('mail/compose') && empty($params['always_mailto'])) {
            return array('regexp' => array('/(?<=\s)(?:mailto:)?([A-Z0-9]+@[A-Z0-9.]+)/ie' =>
                                           '\'<a class="pagelink" href="\'' .
                                           ' . $GLOBALS[\'registry\']->call(\'mail/compose\', array(\'$1\')) . \'">' .
                                           '$0</a>\''));
        } else {
            /* Otherwise, generate a standard mailto: and let the
             * browser handle it. */
            return array('regexp' => array('/(?<=\s)(?:mailto:)?([A-Z0-9]+@[A-Z0-9.]+)/i' =>
                                           '<a class="pagelink" href="mailto:$1">$0</a>'));
        }
    }

}
