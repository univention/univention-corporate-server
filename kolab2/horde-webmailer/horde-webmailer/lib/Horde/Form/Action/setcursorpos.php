<?php
/**
 * Horde_Form_Action_setcursorpos is a Horde_Form_Action that places
 * the cursor in a text field.
 *
 * The params array contains the desired cursor position.
 *
 * $Horde: framework/Form/Form/Action/setcursorpos.php,v 1.3.2.3 2009-01-06 15:23:07 jan Exp $
 *
 * Copyright 2006-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since Horde 3.2
 * @package Horde_Form
 */
class Horde_Form_Action_setcursorpos extends Horde_Form_Action {

    var $_trigger = array('onload');

    function getActionScript(&$form, $renderer, $varname)
    {
        Horde::addScriptFile('form_helpers.js', 'horde', true);

        $pos = implode(',', $this->_params);
        return 'form_setCursorPosition(document.forms[\'' .
            htmlspecialchars($form->getName()) . '\'].elements[\'' .
            htmlspecialchars($varname) . '\'].id, ' . $pos . ');';
    }

}
