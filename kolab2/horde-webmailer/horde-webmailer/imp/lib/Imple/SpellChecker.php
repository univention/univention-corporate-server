<?php
/**
 * $Horde: imp/lib/Imple/SpellChecker.php,v 1.25.2.7 2009-01-06 15:24:08 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package IMP
 */
class Imple_SpellChecker extends Imple {

    /**
     * Constructor.
     *
     * @param array $params  Configuration parameters.
     * <pre>
     * 'id' => TODO (optional)
     * 'locales' => TODO (optional)
     * 'states' => TODO (optional)
     * 'targetId' => TODO (optional)
     * 'triggerId' => TODO (optional)
     * </pre>
     */
    function Imple_SpellChecker($params = array())
    {
        require_once IMP_BASE . '/lib/JSON.php';
        if (empty($params['id'])) {
            $params['id'] = $this->_randomid();
        }
        if (empty($params['targetId'])) {
            $params['targetId'] = $this->_randomid();
        }
        if (empty($params['triggerId'])) {
            $params['triggerId'] = $params['targetId'] . '_trigger';
        }
        if (empty($params['states'])) {
            $params['states'] = '""';
        } else {
            $params['states'] = IMP_Serialize_JSON::encode(String::convertCharset($params['states'], NLS::getCharset(), 'utf-8'));
        }
        if (empty($params['locales'])) {
            $params['locales'] = array();
            foreach (array_keys($GLOBALS['nls']['spelling']) as $lcode) {
                $params['locales'][$lcode] = $GLOBALS['nls']['languages'][$lcode];
            }
        }
        // TODO: SORT_LOCALE_STRING requires PHP 4.4.0 or 5.0.2
        asort($params['locales'], defined('SORT_LOCALE_STRING') ? SORT_LOCALE_STRING : SORT_STRING);
        $params['locales'] = IMP_Serialize_JSON::encode(String::convertCharset($params['locales'], NLS::getCharset()), 'utf-8');

        parent::Imple($params);
    }

    /**
     */
    function attach()
    {
        parent::attach();
        Horde::addScriptFile('KeyNavList.js', 'imp', true);
        Horde::addScriptFile('SpellChecker.js', 'imp', true);
        $url = Horde::url($GLOBALS['registry']->get('webroot', 'imp') . '/imple.php?imple=SpellChecker/input=' . rawurlencode($this->_params['targetId']), true);
        IMP::addInlineScript($this->_params['id'] . ' = new SpellChecker("' . $url . '", "' . $this->_params['targetId'] . '", "' . $this->_params['triggerId'] . '", ' . $this->_params['states'] . ', ' . $this->_params['locales'] . ', \'widget\');', 'dom');
    }

    /**
     */
    function handle($args)
    {
        $spellArgs = array();

        if (!empty($GLOBALS['conf']['spell']['params'])) {
            $spellArgs = $GLOBALS['conf']['spell']['params'];
        }

        if (isset($args['locale'])) {
            $spellArgs['locale'] = $args['locale'];
        } elseif (isset($GLOBALS['language'])) {
            $spellArgs['locale'] = $GLOBALS['language'];
        }

        /* Add local dictionary words. */
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('spelling.php',
                                               array('ignore_list'));
            if (!is_a($result, 'PEAR_Error')) {
                $spellArgs['localDict'] = $result['ignore_list'];
            }
        } else {
            require IMP_BASE . '/config/spelling.php';
            $spellArgs['localDict'] = $ignore_list;
        }

        if (!empty($args['html'])) {
            $spellArgs['html'] = true;
        }

        require_once IMP_BASE . '/lib/SpellChecker.php';
        $speller = IMP_SpellChecker::factory(
            $GLOBALS['conf']['spell']['driver'], $spellArgs);
        if ($speller === false) {
            return array();
        }

        $result = $speller->spellCheck(Util::getPost($args['input']));
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            return array('bad' => array(), 'suggestions' => array());
        } else {
            return $result;
        }
    }

}
