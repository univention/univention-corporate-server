<?php
/**
 * Horde_Form for creating notepads.
 *
 * $Horde: mnemo/lib/Forms/CreateNotepad.php,v 1.1.2.1 2007-12-20 14:17:46 jan Exp $
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @package Mnemo
 */

/** Variables */
require_once 'Horde/Variables.php';

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Renderer */
require_once 'Horde/Form/Renderer.php';

/**
 * The Mnemo_CreateNotepadForm class provides the form for
 * creating a notepad.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Mnemo 2.2
 * @package Mnemo
 */
class Mnemo_CreateNotepadForm extends Horde_Form {

    function Mnemo_CreateNotepadForm(&$vars)
    {
        parent::Horde_Form($vars, _("Create Notepad"));

        $this->addVariable(_("Name"), 'name', 'text', true);
        $this->addVariable(_("Description"), 'description', 'longtext', false, false, null, array(4, 60));

        $this->setButtons(array(_("Create")));
    }

    function execute()
    {
        // Create new share.
        $notepad = $GLOBALS['mnemo_shares']->newShare(md5(microtime()));
        if (is_a($notepad, 'PEAR_Error')) {
            return $notepad;
        }
        $notepad->set('name', $this->_vars->get('name'));
        $notepad->set('desc', $this->_vars->get('description'));
        return $GLOBALS['mnemo_shares']->addShare($notepad);
    }

}
