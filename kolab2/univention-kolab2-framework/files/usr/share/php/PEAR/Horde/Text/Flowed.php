<?php
/**
 * The Text_Flowed:: class provides common methods for manipulating text
 * using the encoding described in RFC 2646 ('flowed' text).
 *
 * $Horde: framework/Text/Text/Flowed.php,v 1.11 2004/02/12 08:28:50 slusarz Exp $
 *
 * This class is based on the Text::Flowed perl module (Version 0.14) found
 * in the CPAN perl repository.  This module is released under the Perl
 * license, which is compatilble with the LGPL.
 *
 * Copyright 2002-2003 Philip Mak
 * Copyright 2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Flowed {

    /**
     * The maximum length that a line is allowed to be (unless faced with
     * with a word that is unreasonably long. This class will re-wrap a
     * line if it exceeds this length.
     *
     * @var integer $_maxlength
     */
    var $_maxlength = 78;

    /**
     * When this class wraps a line, the newly created lines will be split
     * at this length.
     *
     * @var integer $_optlength
     */
    var $_optlength = 72;

    /**
     * The text to be formatted.
     *
     * @var string $_text
     */
    var $_text = '';

    /**
     * The cached output of the formatting.
     *
     * @var array $_output
     */
    var $_output = null;

    /**
     * Constructor.
     *
     * @access public
     *
     * @param string $text  The text to process.
     */
    function Text_Flowed($text)
    {
        $this->_text = $text;
    }

    /**
     * Set the maximum length of a line of text.
     *
     * @access public
     *
     * @param integer $max  A new value for $_maxlength.
     */
    function setMaxLength($max)
    {
        $this->_maxlength = $max;
    }

    /**
     * Set the optimal length of a line of text.
     *
     * @access public
     *
     * @param integer $max  A new value for $_optlength.
     */
    function setOptLength($opt)
    {
        $this->_optlength = $opt;
    }
        
    /**
     * Reformats the input string, where the string is 'format=flowed' plain
     * text as described in RFC 2646.
     *
     * @access public
     *
     * @param optional boolean $quote  Add level of quoting to each line?
     *
     * @return string  The reformatted string.
     */
    function toFixed($quote = false)
    {
        $this->_reformat(false, $quote);

        $txt = '';

        foreach ($this->_output as $val) {
            $txt .= $val['text'] . "\n";
        }

        return rtrim($txt);
    }

    /**
     * Reformats the input string, and returns the output in an array format
     * with quote level information.
     *
     * @access public
     *
     * @param optional boolean $quote  Add level of quoting to each line?
     *
     * @return array  An array of arrays with the following elements:
     * <pre>
     * 'level' - The quote level of the current line.
     * 'text'  - The text for the current line.
     * </pre>
     */
    function toFixedArray($quote = false)
    {
        $this->_reformat(false, $quote);
        return $this->_output;
    }

    /**
     * Convert the text to 'flowed' format.
     *
     * @access public
     *
     * @param optional boolean $quote  Add level of quoting to each line?
     *
     * @return string  The text converted to RFC 2646 'flowed' format.
     */
    function toFlowed($quote = false)
    {
        $this->_reformat(true, $quote);

        $txt = '';

        foreach ($this->_output as $val) {
            $txt .= $val['text'] . "\n";
        }

        return $txt;
    }

    /**
     * Reformats the input string, where the string is 'format=flowed' plain
     * text as described in RFC 2646.
     *
     * @access private
     *
     * @param boolean $toflowed  Convert to flowed?
     * @param boolean $quote     Add level of quoting to each line?
     *
     * @return array  A list of arrays.
     */
    function _reformat($toflowed, $quote)
    {
        if (!is_null($this->_output)) {
            return;
        }

        $this->_output = array();
        $text = explode("\n", $this->_text);

        /* Process message line by line. */
        do {
            $line = array_shift($text);

            /* Per RFC 2646 [4.3], the 'Usenet Signature Convention' line
             * (DASH DASH SP) is not considered flowed. If converting to
             * fixed, we ignore it. */
            if (!$toflowed && ($line == '-- ')) {
                $this->_output[] = array('text' => $line, 'level' => 0);
                continue;
            }

            /* The next three steps come from RFC 2646 [4.2]. */
            /* STEP 1: Determine quote level for line. */
            if (($num_quotes = $this->_numquotes($line))) {
                $line = ltrim($line, '>');
            } 

            if (!$toflowed || $num_quotes) {
                /* STEP 2: Remove space stuffing from line. */
                $line = $this->_unstuff($line);

                /* STEP 3: Should we interpret this line as flowed?
                 * While line is flowed (not empty and there is a space
                 * at the end of the line), and there is a next line, and the
                 * next line has the same quote depth, add to the current
                 * line. */
                while (!empty($line) &&
                       preg_match('/ $/', $line) &&
                       !empty($text) &&
                       ($this->_numquotes($text[0]) == $num_quotes)) {
                    /* Join the next line. */
                    $newline = array_shift($text);
                    if ($num_quotes) {
                        $newline = ltrim($newline, '>');
                    }
                    $line .= $this->_unstuff($newline);
                }
            }

            /* Ensure line is fixed, since we already joined all flowed
             * lines. Remove all trailing ' ' from the line. */
            $line = rtrim($line);

            /* Increment quote depth if we're quoting. */
            if ($quote) {
                $num_quotes++;
            }

            /* The quote prefix for the line. */
            $quotestr = str_repeat('>', $num_quotes);

            if (empty($line)) {
                /* Line is empty. */
                $this->_output[] = array('text' => $quotestr, 'level' => $num_quotes);
            } elseif (empty($this->_maxlength) || ((String::length($line) + $num_quotes) <= $this->_maxlength)) {
                /* Line does not require rewrapping. */
                $this->_output[] = array('text' => $quotestr . $this->_stuff($line, $num_quotes, $toflowed), 'level' => $num_quotes);
            } else {
                /* Rewrap this paragraph. */
                while ($line) {
                    /* Set variables used in regexps. */
                    $max = $this->_maxlength;
                    $min = $num_quotes + 1;
                    $opt = $this->_optlength - 1;

                    /* Stuff and re-quote the line. */
                    $line = $quotestr . $this->_stuff($line, $num_quotes, $toflowed);

                    if (String::length($line) <= $this->_optlength) {
                        /* Remaining section of line is short enough. */
                        $this->_output[] = array('text' => $line, 'level' => $num_quotes);
                        break;
                    } elseif (preg_match('/^(.{' . $min . ',' . $opt . '}) (.*)/', $line, $m) ||
                              preg_match('/^(.{' . $min . ',' . $max . '}) (.*)/', $line, $m) ||
                              preg_match('/^(.{' . $min . ',})? (.*)/', $line, $m)) {
                        /* 1. Try to find a string as long as _optlength.
                         * 2. Try to find a string as long as _maxlength.
                         * 3. Take the first word. */
                        $this->_output[] = array('text' => $m[1] . ' ', 'level' => $num_quotes);
                        $line = $m[2];
                    } else {
                        /* One excessively long word left on line. */
                        $this->_output[] = array('text' => $line, 'level' => $num_quotes);
                        break;
                    }
                }
            }
        } while (!empty($text));
    }

    /**
     * Returns the number of leading '>' characters in the text input.
     * '>' characters are defined by RFC 2646 to indicate a quoted line.
     *
     * @access private
     *
     * @param string $text  The text to analyze.
     *
     * @return integer  The number of leading quote characters.
     */
    function _numquotes($text)
    {
        return (preg_match('/^(>+)/', $text, $matches)) ? strlen($matches[1]) : 0;
    }


    /**
     * Space-stuffs if it starts with ' ' or '>' or 'From ', or if
     * quote depth is non-zero (for aesthetic reasons so that there is a
     * space after the '>').
     *
     * @access private
     *
     * @param string $text        The text to stuff.
     * @param string $num_quotes  The quote-level of this line.
     * @param boolean $toflowed   Converting to flowed format?
     *
     * @return string  The stuffed text.
     */
    function _stuff($text, $num_quotes, $toflowed)
    {
        if ($num_quotes ||
            ($toflowed && preg_match('/^(?: |>|From )/', $text))) {
            return ' ' . $text;
        } else {
            return $text;
        }
    }

    /**
     * Unstuffs a space stuffed line.
     *
     * @access private
     *
     * @param string $text  The text to unstuff.
     *
     * @return string  The unstuffed text.
     */
    function _unstuff($text)
    {
        if (strpos($text, ' ') === 0) {
            $text = substr($text, 1);
        }

        return $text;
    }

}
