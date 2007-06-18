<?php
/**
 * Horde_Form_Action_reload is a Horde_Form Action that reloads the
 * form with the current (not the original) value after the form element
 * that the action is attached to is modified.
 *
 * $Horde: framework/Form/Form/Action/reload.php,v 1.6 2004/03/21 18:22:19 eraserhd Exp $
 *
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file LICENSE for license information (BSD). If you
 * did not receive this file, see http://www.horde.org/licenses/bsdl.php.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Form
 */
class Horde_Form_Action_reload extends Horde_Form_Action {

    var $_trigger = array('onchange');

    function getActionScript($form, $renderer, $varname)
    {
        return 'if (this.value) { document.' . $form->getName() . '.formname.value=\'\';' .
            'document.' . $form->getName() . '.submit() }';
    }

}
