<?php

require_once dirname(__FILE__) . '/../Filter.php';

/**
 * The Text_Filter_linkurls:: class.
 *
 * $Horde: framework/Text/Text/Filter/linkurls.php,v 1.6 2004/01/01 15:14:34 jan Exp $
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
class Text_Filter_linkurls extends Text_Filter {

    /**
     * Add links to all urls.
     *
     * @access public
     *
     * @param string $text  The text to filter.
     *
     * @return string  The text with any links inserted
     */
    function filter($text)
    {
        $validprotos = array(
            'http',
            'https',
            'ftp',
            'irc',
            'telnet',
            'news',
            'file');

        $protogroup = implode('|', $validprotos);

        $go = Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/go.php?1=1', false, -1);
        return preg_replace(
            '/(?<!href|src)(\s)+?((' . $protogroup . '):\/\/[-0-9a-z#%&+.\/:;?_\\~]+[-0-9a-z#%&+\/_\\~])/i',
            '<a target="_blank" class="externlink" href="' . $go . '&url=$2">$2</a>', $text); 
    }

}
