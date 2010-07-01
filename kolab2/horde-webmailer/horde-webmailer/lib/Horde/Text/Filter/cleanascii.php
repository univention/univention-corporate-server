<?php
/**
 * Removes some common entities and high-ascii or otherwise nonstandard
 * characters common in text pasted from Microsoft Word into a browser.
 *
 * This function should NOT be used on non-ASCII text; it may and probably
 * will butcher other character sets indescriminately.  Use it only to clean
 * US-ASCII (7-bit) text which you suspect (or know) may have invalid or
 * non-printing characters in it.
 *
 * $Horde: framework/Text_Filter/Filter/cleanascii.php,v 1.3.2.8 2009-01-06 15:23:42 jan Exp $
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
class Text_Filter_cleanascii extends Text_Filter {

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        if (preg_match('/|([^#]*)#.*/', $text, $regs)) {
            $text = $regs[1];

            if (!empty($text)) {
                $text = $text . "\n";
            }
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
        /* Remove control characters. */
        $regexp = array('/[\x00-\x1f]+/' => '');

        /* The '’' entry may look wrong, depending on your editor,
         * but it's not - that's not really a single quote. */
        $replace = array(chr(150) => '-',
                         chr(167) => '*',
                         '·' => '*',
                         '…' => '...',
                         '‘' => "'",
                         '’' => "'",
                         '“' => '"',
                         '”' => '"',
                         '•' => '*',
                         '–' => '-',
                         '—' => '-',
                         'Ÿ' => '*',
                         '&#61479;' => '.',
                         '&#61572;' => '*',
                         '&#61594;' => '*',
                         '&#61640;' => '-',
                         '&#61623;' => '-',
                         '&#61607;' => '*',
                         '&#61553;' => '*',
                         '&#61558;' => '*',
                         '&#8226;' => '*',
                         '&#9658;' => '>',
                         );

        return array('regexp' => $regexp, 'replace' => $replace);
    }

}
