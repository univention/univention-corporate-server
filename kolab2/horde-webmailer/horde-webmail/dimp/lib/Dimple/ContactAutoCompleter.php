<?php

require_once IMP_BASE . '/lib/Imple/ContactAutoCompleter.php';

/**
 * $Horde: dimp/lib/Dimple/ContactAutoCompleter.php,v 1.17.2.8 2009-01-06 15:22:39 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Dimple
 */
class Dimple_ContactAutoCompleter extends Imple_ContactAutoCompleter {

    /**
     */
    function attach()
    {
        Horde::addScriptFile('prototype.js', 'imp', true);
        Horde::addScriptFile('effects.js', 'imp', true);
        Horde::addScriptFile('autocomplete.js', 'dimp', true);
        IMP::addInlineScript('new Ajax.Autocompleter("' . $this->_params['triggerId'] . '", "' . $this->_params['resultsId'] . '", "' . Horde::url($GLOBALS['registry']->get('webroot', 'dimp') . '/dimple.php/ContactAutoCompleter/input=' . rawurlencode($this->_params['triggerId'])) . '", { tokens: [",", ";"], indicator: "' . $this->_params['triggerId'] . '_loading_img", afterUpdateElement: function(f, t) { if (!f.value.endsWith(";")) { f.value += ","; } f.value += " "; } });', 'dom');
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
