<?php

require_once dirname(__FILE__) . '/../Filter.php';

/**
 * The Text_Filter_emoticons:: class finds emoticon strings ( :),
 * etc.) in a block of text and turns them into image links.
 *
 * $Horde: framework/Text/Text/Filter/emoticons.php,v 1.9 2004/01/30 23:56:23 mdjukic Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Text
 */
class Text_Filter_emoticons extends Text_Filter {

    /**
     * Convert textual emoticons into graphical ones.
     *
     * @access public
     *
     * @param string $text       The text to filter.
     * @param boolean $entities  (optional) If true the html entity versions of
     *                           the patterns will be used. Useful for
     *                           combinations with Text::toHTML().
     *
     * @return string  The text with any graphical emoticons inserted.
     */
    function filter($text, $entities = false)
    {
        $patterns = &Text_Filter_emoticons::getPatterns();

        /* Loop through possible string emoticons and convert to
         * graphics. */
        foreach ($patterns['replace'] as $string => $icon) {
            if ($entities) {
                $string = htmlspecialchars($string);
            }
            /* Check for a smiley either immediately at the start of a line
             * or following a space. Use {} as the preg delimiters as this is
             * not found in any smiley. */
            $text = preg_replace('{(^|\s)' . preg_quote($string) . '}', ' ' . Horde::img($icon . '.gif', $string, 'align="middle"', $GLOBALS['registry']->getParam('graphics', 'horde') . '/emoticons'), $text);
        }

        return $text;
    }

    function getPatterns()
    {
        /* List complex strings before simpler ones, otherwise for
         * example :(( would be matched against :( before :(( is
         * found. */
        return array('replace' => array(
            ':/' => 'frustrated', ':-/' => 'frustrated', ':*>' => 'blush',
            ':e' => 'disappointed', '=:)$' => 'mrt', '#|' => 'hangover',
            '#-|' => 'hangover', ':-@' => 'shout', ':((' => 'bigfrown',
            ':C' => 'bigfrown', ':S' => 'dazed', ':-S' => 'dazed',
            'X@' => 'angry', 'X(' => 'mad', '>:)' => 'devil', '>:-)' => 'devil',
            '>:p' => 'deviltongue', '>:-p' => 'deviltongue',
            '>:p' => 'raspberry', '>:P' => 'raspberry', '&)' => 'punk',
            '&p' => 'punktongue', '=&)' => 'punkmohawk', ':]' => 'grin',
            '#[' => 'hurt', '#(' => 'hurt', '#-[' => 'hurt', '#-(' => 'hurt',
            ':O' => 'embarrassed', ':-O' => 'embarrassed', ':[' => 'sad',
            '>:@' => 'enraged', ':&' => 'annoyed', '=(' => 'worried',
            '=-(' => 'worried', ':|=' => 'vampire', ':-(' => 'frown',
            ':D' => 'biggrin', '8)' => 'cool', '8p' => 'cooltongue',
            '8Þ' => 'cooltongue', '8D' => 'coolgrin', ':p' => 'tongueout',
            ':P' => 'tongueout', ':Þ' => 'tongueout', '?:(' => 'confused',
            '%-(' => 'confused', ':)&' => 'love', 'O;-)' => 'angelwink',
            ';]' => 'winkgrin', ';p' => 'winktongue', ';P' => 'winktongue',
            ';Þ' => 'winktongue', ':|' => 'indifferent', ':-|' => 'indifferent',
            '!|' => 'tired', '!-I' => 'tired', '|I' => 'asleep',
            '|-I' => 'asleep', 'O:)' => 'angel', 'O:-)' => 'angel',
            'O;)' => 'angelwink', ';-)' => 'wink', ':#)' => 'clown',
            ':o)' => 'clown', ':)' => 'smile', ';)' => 'wink', ':-)' => 'smile',
            ':@' => 'shout', ':(' => 'frown'));
    }

}
