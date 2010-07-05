<?php
/**
 * Horde_Form_Action_reload is a Horde_Form Action that reloads the
 * form with the current (not the original) value after the form element
 * that the action is attached to is modified.
 *
 * $Horde: framework/Form/Form/Action/reload.php,v 1.7.10.8 2009-01-06 15:23:07 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Form
 */
class Horde_Form_Action_reload extends Horde_Form_Action {

    var $_trigger = array('onchange');

    function getActionScript($form, $renderer, $varname)
    {
        Horde::addScriptFile('prototype.js', 'horde', true);
        Horde::addScriptFile('effects.js', 'horde', true);
        Horde::addScriptFile('redbox.js', 'horde', true);
        return 'if (this.value) { document.' . $form->getName() . '.formname.value=\'\'; RedBox.loading(); document.' . $form->getName() . '.submit() }';
    }

}
