<?php
/**
 * Highlights simple markup as used in emails or usenet postings.
 *
 * $Horde: framework/Text_Filter/Filter/simplemarkup.php,v 1.1.10.9 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Filter_simplemarkup extends Text_Filter {

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $regexp = array(
            // Bold.
            '/(^|\s|&nbsp;|<br \/>)(\*[^*\s]+\*)(\s|&nbsp;|<br|\.)/i' => '\1<strong>\2</strong>\3',

            // Underline.
            '/(^|\s|&nbsp;|<br \/>)(_[^_\s]+_)(\s|&nbsp;|<br|\.)/i' => '\1<u>\2</u>\3',

            // Italic.
            ';(^|\s|&nbsp\;|<br />)(/[^/\s]+/)(\s|&nbsp\;|<br|\.);i' => '\1<em>\2</em>\3');

        return array('regexp' => $regexp);
    }

}
