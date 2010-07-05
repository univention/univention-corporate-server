<?php
/**
 * The Horde_SpellChecker_aspell:: class provides a driver for the 'aspell'
 * program.
 *
 * $Horde: framework/SpellChecker/SpellChecker/aspell.php,v 1.11.2.8 2009-01-06 15:23:37 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_SpellChecker
 */
class Horde_SpellChecker_aspell extends Horde_SpellChecker {

    var $_path = 'aspell';

    /**
     *
     */
    function spellCheck($text)
    {
        if ($this->_html) {
            $input = strtr($text, "\n", ' ');
        } else {
            $words = $this->_getWords($text);
            if (!count($words)) {
                return array('bad' => array(), 'suggestions' => array());
            }
            $input = implode(' ', $words);
        }

        $charset = NLS::getCharset();

        // Descriptor array.
        $descspec = array(
            0 => array('pipe', 'r'),
            1 => array('pipe', 'w'),
            2 => array('pipe', 'w')
        );

        $process = proc_open($this->_cmd(), $descspec, $pipes);
        if (!is_resource($process)) {
            require_once 'PEAR.php';
            return PEAR::raiseError('spellcheck failed', null, null, null,
                                    $this->_cmd());
        }

        // Write to stdin.
        if ($this->_encoding) {
            $input = String::convertCharset($input, $charset, $this->_encoding);
        }
        // The '^' character tells aspell to spell check the entire line.
        fwrite($pipes[0], '^' . $input);
        fclose($pipes[0]);

        // Read stdout.
        $out = '';
        while (!feof($pipes[1])) {
            $out .= fread($pipes[1], 8192);
        }
        fclose($pipes[1]);

        // Read stderr.
        $err = '';
        while (!feof($pipes[2])) {
            $err .= fread($pipes[2], 8192);
        }
        fclose($pipes[2]);

        // We can't rely on the return value of proc_close:
        // http://bugs.php.net/bug.php?id=29123
        proc_close($process);

        if (strlen($out) === 0) {
            require_once 'PEAR.php';
            if ($this->_encoding) {
                $err = String::convertCharset($err, $this->_encoding, $charset);
            }
            return PEAR::raiseError('spellcheck failed: ' . $err);
        }

        if ($this->_encoding) {
            $out = String::convertCharset($out, $this->_encoding, $charset);
        }

        // Parse output.
        $bad = array();
        $suggestions = array();
        $lines = explode("\n", $out);
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) {
                continue;
            }

            @list(,$word,) = explode(' ', $line, 3);

            if ($this->_inLocalDictionary($word) || in_array($word, $bad)) {
                continue;
            }

            switch ($line[0]) {
            case '#':
                // Misspelling with no suggestions.
                $bad[] = $word;
                $suggestions[] = array();
                break;

            case '&':
                // Suggestions.
                $bad[] = $word;
                $suggestions[] = array_slice(explode(', ', substr($line, strpos($line, ':') + 2)), 0, $this->_maxSuggestions);
                break;
            }
        }

        return array('bad' => $bad, 'suggestions' => $suggestions);
    }

    function _cmd()
    {
        $args = '';

        switch ($this->_suggestMode) {
        case SPELLCHECKER_SUGGEST_FAST:
            $args .= ' --sug-mode=fast';
            break;

        case SPELLCHECKER_SUGGEST_SLOW:
            $args .= ' --sug-mode=bad-spellers';
            break;

        default:
            $args .= ' --sug-mode=normal';
        }

        if ($this->_encoding) {
            $args .= ' --encoding=' . escapeshellarg($this->_encoding);
        }

        $args .= ' --lang=' . escapeshellarg($this->_locale);

        if ($this->_html) {
            $args .= ' -H';
        }

        return sprintf('%s -a %s', $this->_path, $args);
    }

}
