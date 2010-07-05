<?php

define('SPELLCHECKER_SUGGEST_FAST', 1);
define('SPELLCHECKER_SUGGEST_NORMAL', 2);
define('SPELLCHECKER_SUGGEST_SLOW', 3);

/** NLS */
require_once 'Horde/NLS.php';

/** String */
require_once 'Horde/String.php';

/**
 * The Horde_SpellChecker:: class provides a unified spellchecker API.
 *
 * $Horde: framework/SpellChecker/SpellChecker.php,v 1.12.2.5 2009-01-06 15:23:37 jan Exp $
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
class Horde_SpellChecker {

    var $_maxSuggestions = 10;
    var $_minLength = 3;
    var $_locale = 'en';
    var $_encoding = 'utf-8';
    var $_html = false;
    var $_suggestMode = SPELLCHECKER_SUGGEST_FAST;
    var $_localDict = array();

    /**
     * Constructor.
     */
    function Horde_SpellChecker($params)
    {
        $this->__construct($params);
    }

    /**
     */
    function __construct($params)
    {
        $this->setParams($params);
    }

    /**
     * TODO
     *
     * @param array $params  TODO
     */
    function setParams($params)
    {
        foreach ($params as $key => $val) {
            $key = '_' . $key;
            $this->$key = $val;
        }
    }

    /**
     * TODO
     *
     * @param string $engine  TODO
     * @param array $params   TODO
     *
     * @return TODO
     */
    function factory($engine, $params = array())
    {
        $engine = strtolower(basename($engine));
        $class = 'Horde_SpellChecker_' . $engine;
        if (!class_exists($class)) {
            include 'Horde/SpellChecker/' . $engine . '.php';
        }
        if (!class_exists($class)) {
            return false;
        }
        return new $class($params);
    }

    /**
     * TODO
     *
     * @abstract
     *
     * @param string $text  TODO
     *
     * @return array  TODO
     */
    function spellCheck($text)
    {
    }

    /**
     * TODO
     *
     * @access private
     *
     * @param string $text  TODO
     *
     * @return array  TODO
     */
    function _getWords($text)
    {
        return array_keys(array_flip(preg_split('/[\s\[\]]+/s', $text, -1, PREG_SPLIT_NO_EMPTY)));
    }

    /**
     * Determine if a word exists in the local dictionary.
     *
     * @access private
     *
     * @param string $word  The word to check.
     *
     * @return boolean  True if the word appears in the local dictionary.
     */
    function _inLocalDictionary($word)
    {
        return (empty($this->_localDict)) ? false : in_array(String::lower($word, true), $this->_localDict);
    }

}
