<?php
/**
 * Horde_Form for deleting notepads.
 *
 * $Horde: mnemo/lib/Forms/DeleteNotepad.php,v 1.4.2.1 2007-12-20 14:17:46 jan Exp $
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
 * The Mnemo_DeleteNotepadForm class provides the form for
 * deleting a notepad.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Mnemo 2.2
 * @package Mnemo
 */
class Mnemo_DeleteNotepadForm extends Horde_Form {

    /**
     * Notepad being deleted
     */
    var $_notepad;

    function Mnemo_DeleteNotepadForm(&$vars, &$notepad)
    {
        $this->_notepad = &$notepad;
        parent::Horde_Form($vars, sprintf(_("Delete %s"), $notepad->get('name')));

        $this->addHidden('', 'n', 'text', true);
        $this->addVariable(sprintf(_("Really delete the notepad \"%s\"? This cannot be undone and all data on this notepad will be permanently removed."), $this->_notepad->get('name')), 'desc', 'description', false);

        $this->setButtons(array(_("Delete"), _("Cancel")));
    }

    function execute()
    {
        // If cancel was clicked, return false.
        if ($this->_vars->get('submitbutton') == _("Cancel")) {
            return false;
        }

        if ($this->_notepad->get('owner') != Auth::getAuth()) {
            return PEAR::raiseError(_("Permission denied"));
        }

        // Delete the notepad.
        $storage = &Mnemo_Driver::singleton($this->_notepad->getName());
        $result = $storage->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete \"%s\": %s"), $this->_notepad->get('name'), $result->getMessage()));
        } else {
            // Remove share and all groups/permissions.
            $result = $GLOBALS['mnemo_shares']->removeShare($this->_notepad);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        // Make sure we still own at least one notepad.
        if (count(Mnemo::listNotepads(true)) == 0) {
            // If the default share doesn't exist then create it.
            if (!$GLOBALS['mnemo_shares']->exists(Auth::getAuth())) {
                require_once 'Horde/Identity.php';
                $identity = &Identity::singleton();
                $name = $identity->getValue('fullname');
                if (trim($name) == '') {
                    $name = Auth::removeHook(Auth::getAuth());
                }
                $notepad = &$GLOBALS['mnemo_shares']->newShare(Auth::getAuth());
                if (is_a($notepad, 'PEAR_Error')) {
                    return;
                }
                $notepad->set('name', sprintf(_("%s's Notepad"), $name));
                $GLOBALS['mnemo_shares']->addShare($notepad);
            }
        }

        return true;
    }

}
