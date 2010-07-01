<?php
/**
 * The Text_Flowed:: class provides common methods for manipulating text
 * using the encoding described in RFC 3676 ('flowed' text).
 *
 * $Horde: framework/Text_Flowed/Flowed.php,v 1.14.10.21 2009-01-06 15:23:43 jan Exp $
 *
 * This class is based on the Text::Flowed perl module (Version 0.14) found
 * in the CPAN perl repository.  This module is released under the Perl
 * license, which is compatible with the LGPL.
 *
 * Copyright 2002-2003 Philip Mak
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Flowed {

    /**
     * The maximum length that a line is allowed to be (unless faced with
     * with a word that is unreasonably long). This class will re-wrap a
     * line if it exceeds this length.
     *
     * @var integer
     */
    var $_maxlength = 78;

    /**
     * When this class wraps a line, the newly created lines will be split
     * at this length.
     *
     * @var integer
     */
    var $_optlength = 72;

    /**
     * The text to be formatted.
     *
     * @var string
     */
    var $_text;

    /**
     * The cached output of the formatting.
     *
     * @var array
     */
    var $_output = array();

    /**
     * The format of the data in $_output.
     *
     * @var string
     */
    var $_formattype = null;

    /**
     * The character set of the text.
     *
     * @var string
     */
    var $_charset;

    /**
     * Convert text using DelSp?
     *
     * @var boolean
     */
    var $_delsp = false;

    /**
     * Constructor.
     *
     * @param string $text     The text to process.
     * @param string $charset  The character set of $text.
     */
    function Text_Flowed($text, $charset = null)
    {
        $this->_text = $text;
        $this->_charset = $charset;
    }

    /**
     * Set the maximum length of a line of text.
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
     * @param integer $max  A new value for $_optlength.
     */
    function setOptLength($opt)
    {
        $this->_optlength = $opt;
    }

    /**
     * Set whether to format test using DelSp.
     *
     * @since Horde 3.1
     *
     * @param boolean $delsp  Use DelSp?
     */
    function setDelSp($delsp)
    {
        $this->_delsp = (bool) $delsp;
    }

    /**
     * Reformats the input string, where the string is 'format=flowed' plain
     * text as described in RFC 2646.
     *
     * @param boolean $quote  Add level of quoting to each line?
     *
     * @return string  The text converted to RFC 2646 'fixed' format.
     */
    function toFixed($quote = false)
    {
        $txt = '';

        $this->_reformat(false, $quote);
        reset($this->_output);
        $lines = count($this->_output) - 1;
        while (list($no, $line) = each($this->_output)) {
            $txt .= $line['text'] . (($lines == $no) ? '' : "\n");
        }
        return $txt;
    }

    /**
     * Reformats the input string, and returns the output in an array format
     * with quote level information.
     *
     * @param boolean $quote  Add level of quoting to each line?
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
     * Reformats the input string, where the string is 'format=fixed' plain
     * text as described in RFC 2646.
     *
     * @param boolean $quote  Add level of quoting to each line?
     *
     * @return string  The text converted to RFC 2646 'flowed' format.
     */
    function toFlowed($quote = false)
    {
        $txt = '';

        $this->_reformat(true, $quote);
        reset($this->_output);
        while (list(,$line) = each($this->_output)) {
            $txt .= $line['text'] . "\n";
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
     */
    function _reformat($toflowed, $quote)
    {
        $format_type = implode('|', array($toflowed, $quote));
        if ($format_type == $this->_formattype) {
            return;
        }

        $this->_output = array();
        $this->_formattype = $format_type;

        /* Set variables used in regexps. */
        $delsp = ($toflowed && $this->_delsp) ? 1 : 0;
        $opt = $this->_optlength - 1 - $delsp;

        /* Process message line by line. */
        $text = explode("\n", $this->_text);
        $text_count = count($text) - 1;
        $skip = 0;
        reset($text);

        while (list($no, $line) = each($text)) {
            if ($skip) {
                --$skip;
                continue;
            }

            /* Per RFC 2646 [4.3], the 'Usenet Signature Convention' line
             * (DASH DASH SP) is not considered flowed.  Watch for this when
             * dealing with potentially flowed lines. */

            /* The next three steps come from RFC 2646 [4.2]. */
            /* STEP 1: Determine quote level for line. */
            if (($num_quotes = $this->_numquotes($line))) {
                $line = substr($line, $num_quotes);
            }

            /* Only combine lines if we are converting to flowed or if the
             * current line is quoted. */
            if (!$toflowed || $num_quotes) {
                /* STEP 2: Remove space stuffing from line. */
                $line = $this->_unstuff($line);

                /* STEP 3: Should we interpret this line as flowed?
                 * While line is flowed (not empty and there is a space
                 * at the end of the line), and there is a next line, and the
                 * next line has the same quote depth, add to the current
                 * line. A line is not flowed if it is a signature line. */
                if ($line != '-- ') {
                    while (!empty($line) && 
                           ($line[strlen($line) - 1] == ' ') &&
                           ($text_count != $no) &&
                           ($this->_numquotes($text[$no + 1]) == $num_quotes)) {
                        /* If DelSp is yes and this is flowed input, we need to
                         * remove the trailing space. */
                        if (!$toflowed && $this->_delsp) {
                            $line = substr($line, 0, -1);
                        }
                        $line .= $this->_unstuff(substr($text[++$no], $num_quotes));
                        ++$skip;
                    }
                }
            }

            /* Ensure line is fixed, since we already joined all flowed
             * lines. Remove all trailing ' ' from the line. */
            if ($line != '-- ') {
                $line = rtrim($line);
            }

            /* Increment quote depth if we're quoting. */
            if ($quote) {
                $num_quotes++;
            }

            /* The quote prefix for the line. */
            $quotestr = str_repeat('>', $num_quotes);

            if (empty($line)) {
                /* Line is empty. */
                $this->_output[] = array('text' => $quotestr, 'level' => $num_quotes);
            } elseif (empty($this->_maxlength) || ((String::length($line, $this->_charset) + $num_quotes) <= $this->_maxlength)) {
                /* Line does not require rewrapping. */
                $this->_output[] = array('text' => $quotestr . $this->_stuff($line, $num_quotes, $toflowed), 'level' => $num_quotes);
            } else {
                $min = $num_quotes + 1;

                /* Rewrap this paragraph. */
                while ($line) {
                    /* Stuff and re-quote the line. */
                    $line = $quotestr . $this->_stuff($line, $num_quotes, $toflowed);
                    $line_length = String::length($line, $this->_charset);
                    if ($line_length <= $this->_optlength) {
                        /* Remaining section of line is short enough. */
                        $this->_output[] = array('text' => $line, 'level' => $num_quotes);
                        break;
                    } elseif ($m = String::regexMatch($line, array('^(.{' . $min . ',' . $opt . '}) (.*)', '^(.{' . $min . ',' . $this->_maxlength . '}) (.*)', '^(.{' . $min . ',})? (.*)'), $this->_charset)) {
                        /* We need to wrap text at a certain number of
                         * *characters*, not a certain number of *bytes*;
                         * thus the need for a multibyte capable regex.
                         * If a multibyte regex isn't available, we are stuck
                         * with preg_match() (the function will still work -
                         * we will just be left with shorter rows than expected
                         * if multibyte characters exist in the row).
                         *
                         * Algorithim:
                         * 1. Try to find a string as long as _optlength.
                         * 2. Try to find a string as long as _maxlength.
                         * 3. Take the first word. */
                        if (empty($m[1])) {
                            $m[1] = $m[2];
                            $m[2] = '';
                        }
                        $this->_output[] = array('text' => $m[1] . ' ' . (($delsp) ? ' ' : ''), 'level' => $num_quotes);
                        $line = $m[2];
                    } else {
                        /* One excessively long word left on line.  Be
                         * absolutely sure it does not exceed 998 characters
                         * in length or else we must truncate. */
                        if ($line_length > 998) {
                            $this->_output[] = array('text' => String::substr($line, 0, 998, $this->_charset), 'level' => $num_quotes);
                            $line = String::substr($line, 998, null, $this->_charset);
                        } else {
                            $this->_output[] = array('text' => $line, 'level' => $num_quotes);
                            break;
                        }
                    }
                }
            }
        }
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
        return strspn($text, '>');
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
     * @param boolean $toflowed   Are we converting to flowed text?
     *
     * @return string  The stuffed text.
     */
    function _stuff($text, $num_quotes, $toflowed)
    {
        if ($toflowed &&
            ($num_quotes || preg_match("/^(?: |>|From |From$)/", $text))) {
            return ' ' . $text;
        }
        return $text;
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
        if (!empty($text) && ($text[0] == ' ')) {
            $text = substr($text, 1);
        }
        return $text;
    }

}
