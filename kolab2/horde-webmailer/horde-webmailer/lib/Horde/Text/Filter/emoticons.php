<?php

require_once 'Horde.php';

/**
 * The Text_Filter_emoticons:: class finds emoticon strings ( :), etc.) in a
 * block of text and turns them into image links.
 *
 * Parameters:
 * <pre>
 * entities -- If true the html entity versions of the patterns will be used.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/emoticons.php,v 1.17.10.15 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @package Horde_Text
 */
class Text_Filter_emoticons extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('entities' => false);

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        /* Build the patterns. */
        $patterns = array_keys($this->getIcons());
        $beg_pattern = '(^|\s)(';
        $end_pattern = ')(?=\s)';
        if ($this->_params['entities']) {
            $patterns = array_map('htmlspecialchars', $patterns);
            $beg_pattern = '(^|\s|<br />|&nbsp;)(';
            $end_pattern = ')(?=\s|<br />|&nbsp;)';
        }
        $patterns = array_map('preg_quote', $patterns);

        /* Check for a smiley either immediately at the start of a line or
         * following a space. Use {} as the preg delimiters as this is not
         * found in any smiley. */
        $regexp['{' . $beg_pattern . implode('|', $patterns) . $end_pattern . '}e'] = 'Text_Filter_emoticons::getImage(\'$2\', \'$1\', \'' . ($this->_params['entities'] ? '$3' : '') . '\')';

        return array('regexp' => $regexp);
    }

    /**
     * Returns the img tag for an emoticon.
     *
     * @see Text_Filter_emoticons::getPatterns()
     * @since Horde 3.1.4
     *
     * @param string $icon  The emoticon.
     * @param string $prefix  A html prefix.
     * @param string $postfix  A html postfix.
     *
     * @return string  HTML code with the image tag and any additional prefix
     *                 or postfix.
     */
    function getImage($icon, $prefix, $postfix)
    {
        static $iconpath;
        if (empty($iconpath)) {
            $iconpath = $GLOBALS['registry']->getImageDir('horde') . '/emoticons';;
        }

        return $prefix . Horde::img(Text_Filter_emoticons::getIcons($icon) . '.png', $icon, array('align' => 'middle', 'title' => $icon), $iconpath) . $postfix;
    }

    /**
     * Returns a hash with all emoticons and names or the name of a single
     * emoticon.
     *
     * @param string $icon  If set, return the name for that emoticon only.
     *                      @since Horde 3.1.4
     *
     * @return array|string  Patterns hash or icon name.
     */
    function getIcons($icon = null)
    {
        /* List complex strings before simpler ones, otherwise for example :((
         * would be matched against :( before :(( is found. */
        static $icons = array(
            ':/' => 'frustrated', ':-/' => 'frustrated',
            // ':*>' => 'blush',
            ':e' => 'disappointed',
            '=:)$' => 'mrt',
            '#|' => 'hangover', '#-|' => 'hangover',
            ':-@' => 'shout', ':@' => 'shout',
            ':((' => 'bigfrown', ':C' => 'bigfrown',
            ':S' => 'dazed', ':-S' => 'dazed',
            'X@' => 'angry',
            'X(' => 'mad',
            // '>:)' => 'devil', '>:-)' => 'devil',
            // '>:p' => 'deviltongue', '>:-p' => 'deviltongue',
            // '>:p' => 'raspberry', '>:P' => 'raspberry',
            // '&)' => 'punk',
            // '&p' => 'punktongue',
            // '=&)' => 'punkmohawk',
            ':]' => 'grin',
            '#[' => 'hurt', '#(' => 'hurt', '#-[' => 'hurt', '#-(' => 'hurt',
            ':O' => 'embarrassed', ':-O' => 'embarrassed',
            ':[' => 'sad',
            // '>:@' => 'enraged',
            // ':&' => 'annoyed',
            '=(' => 'worried', '=-(' => 'worried',
            ':|=' => 'vampire',
            ':-(' => 'frown', ':(' => 'frown',
            ':D' => 'biggrin', ':-D' => 'biggrin', ':d' => 'biggrin', ':-d' => 'biggrin',
            '8)' => 'cool',
            // In English, 8PM occurs sufficiently often to specifically
            // search for and exclude
            '8p(?<![Mm]\s+)' => 'cooltongue', // '8Þ' => 'cooltongue',
            '8D' => 'coolgrin',
            ':p' => 'tongueout', ':P' => 'tongueout', // ':Þ' => 'tongueout',
            '?:(' => 'confused', '%-(' => 'confused',
            // ':)&' => 'love',
            'O;-)' => 'angelwink',
            ';]' => 'winkgrin',
            ';p' => 'winktongue', ';P' => 'winktongue', // ';Þ' => 'winktongue',
            ':|' => 'indifferent', ':-|' => 'indifferent',
            '!|' => 'tired', '!-I' => 'tired',
            '|I' => 'asleep', '|-I' => 'asleep',
            'O:)' => 'angel', 'O:-)' => 'angel',
            'O;)' => 'angelwink',
            ';-)' => 'wink', ';)' => 'wink',
            ':#)' => 'clown', ':o)' => 'clown',
            ':)' => 'smile', ':-)' => 'smile',
        );

        if ($icon) {
            return isset($icons[$icon]) ? $icons[$icon] : null;
        } else {
            return $icons;
        }
    }

}
