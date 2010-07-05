<?php
/**
 * Filters the given text based on the words found in a word list
 * file.
 *
 * Parameters:
 * <pre>
 * words_file  -- Filename containing the words to replace.
 * replacement -- The replacement string.  Defaults to "*****".
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/words.php,v 1.2.10.9 2009-01-06 15:23:42 jan Exp $
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
class Text_Filter_words extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('replacement' => '*****');

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $regexp = array();

        if (is_readable($this->_params['words_file'])) {
            /* Read the file and iterate through the lines. */
            $lines = file($this->_params['words_file']);
            foreach ($lines as $line) {
                /* Strip whitespace and comments. */
                $line = trim($line);
                $line = preg_replace('|#.*$|', '', $line);

                /* Filter the text. */
                if (!empty($line)) {
                    $regexp["/(\b(\w*)$line\b|\b$line(\w*)\b)/i"] = $this->_getReplacement($line);
                }
            }
        }

        return array('regexp' => $regexp);
    }

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function _getReplacement($line)
    {
        if ($this->_params['replacement']) {
            return $this->_params['replacement'];
        } else {
            return substr($line, 0, 1) . str_repeat('*', strlen($line) - 1);
        }
    }

}
