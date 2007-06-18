<?php
/**
 * Text_Filter:: is a parent class for defining stackable text
 * filters.
 *
 * $Horde: framework/Text/Text/Filter.php,v 1.6 2004/01/01 15:14:33 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Filter {

    /**
     * Apply a set of patterns to a block of text.
     *
     * @access public
     *
     * @param string $text      The text to filter.
     * @param array  $patterns  The array of patterns to filter with.
     *
     * @return string  The transformed text.
     */
    function filter($text, $patterns)
    {
        /* str_replace() simple patterns. */
        if (isset($patterns['replace'])) {
            $from = array_keys($patterns['replace']);
            $to = array_values($patterns['replace']);
            $text = str_replace($from, $to, $text);
        }

        /* preg_replace complex patterns. */
        if (isset($patterns['regexp'])) {
            $from = array_keys($patterns['regexp']);
            $to = array_values($patterns['regexp']);
            $text = preg_replace($from, $to, $text);
        }

        return $text;
    }

}
