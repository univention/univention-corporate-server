<?php

require_once IMP_BASE . '/lib/Imple/SpellChecker.php';

/**
 * $Horde: dimp/lib/Dimple/SpellChecker.php,v 1.29.2.4 2009-01-06 15:22:39 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Dimple
 */
class Dimple_SpellChecker extends Imple_SpellChecker {

    /**
     */
    function attach()
    {
        Horde::addScriptFile('KeyNavList.js', 'imp', true);
        Horde::addScriptFile('SpellChecker.js', 'imp', true);
        $url = Horde::url($GLOBALS['registry']->get('webroot', 'dimp') . '/dimple.php/SpellChecker/input=' . rawurlencode($this->_params['targetId']));
        IMP::addInlineScript($this->_params['id'] . ' = new SpellChecker("' . $url . '", "' . $this->_params['targetId'] . '", "' . $this->_params['triggerId'] . '", ' . $this->_params['states'] . ', ' . $this->_params['locales'] . ');', 'dom');
    }

    /**
     */
    function handle($args)
    {
        $GLOBALS['registry']->pushApp('imp');
        $ret = parent::handle($args);
        $GLOBALS['registry']->popApp('imp');
        return $ret;
    }

}
