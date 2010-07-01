<?php
/**
 * The Text_Filter_tabs2spaces:: converts tabs into spaces.
 *
 * $Horde: framework/Text_Filter/Filter/tabs2spaces.php,v 1.3.10.10 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Text
 */
class Text_Filter_tabs2spaces extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('tabstop' => 8, 'breakchar' => "\n");

    /**
     * Executes any code necessary before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        $lines = explode($this->_params['breakchar'], $text);
        for ($i = 0; $i < count($lines); $i++) {
            while (($pos = strpos($lines[$i], "\t")) !== false) {
                $n_space = $this->_params['tabstop'] - ($pos % $this->_params['tabstop']);
                $new_str = str_repeat(' ', $n_space);
                $lines[$i] = substr_replace($lines[$i], $new_str, $pos, 1);
            }
        }
        return implode("\n", $lines);
    }

}
