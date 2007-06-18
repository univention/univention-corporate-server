<?php
/**
 * Horde_Form_Action_submit is a Horde_Form Action that submits the
 * form after the form element that the action is attached to is
 * modified.
 *
 * $Horde: framework/Form/Form/Action/submit.php,v 1.10 2004/03/21 18:22:19 eraserhd Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @package Horde_Form
 */
class Horde_Form_Action_submit extends Horde_Form_Action {

    var $_trigger = array('onchange');

    function getActionScript($form, $renderer, $varname)
    {
        return 'document.' . $form->getName() . '.submit()';
    }

}
