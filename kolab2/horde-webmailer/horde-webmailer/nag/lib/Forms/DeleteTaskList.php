<?php
/**
 * Horde_Form for deleting task lists.
 *
 * $Horde: nag/lib/Forms/DeleteTaskList.php,v 1.1.2.1 2007-12-20 14:23:08 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Nag
 */

/** Variables */
require_once 'Horde/Variables.php';

/** Horde_Form */
require_once 'Horde/Form.php';

/** Horde_Form_Renderer */
require_once 'Horde/Form/Renderer.php';

/**
 * The Nag_DeleteTaskListForm class provides the form for
 * deleting a task list.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Nag_DeleteTaskListForm extends Horde_Form {

    /**
     * Task list being deleted
     */
    var $_tasklist;

    function Nag_DeleteTaskListForm(&$vars, &$tasklist)
    {
        $this->_tasklist = &$tasklist;
        parent::Horde_Form($vars, sprintf(_("Delete %s"), $tasklist->get('name')));

        $this->addHidden('', 't', 'text', true);
        $this->addVariable(sprintf(_("Really delete the task list \"%s\"? This cannot be undone and all data on this task list will be permanently removed."), $this->_tasklist->get('name')), 'desc', 'description', false);

        $this->setButtons(array(_("Delete"), _("Cancel")));
    }

    function execute()
    {
        // If cancel was clicked, return false.
        if ($this->_vars->get('submitbutton') == _("Cancel")) {
            return false;
        }

        if ($this->_tasklist->get('owner') != Auth::getAuth()) {
            return PEAR::raiseError(_("Permission denied"));
        }

        // Delete the task list.
        $storage = &Nag_Driver::singleton($this->_tasklist->getName());
        $result = $storage->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete \"%s\": %s"), $this->_tasklist->get('name'), $result->getMessage()));
        } else {
            // Remove share and all groups/permissions.
            $result = $GLOBALS['nag_shares']->removeShare($this->_tasklist);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        // Make sure we still own at least one task list.
        if (count(Nag::listTasklists(true)) == 0) {
            // If the default share doesn't exist then create it.
            if (!$GLOBALS['nag_shares']->exists(Auth::getAuth())) {
                require_once 'Horde/Identity.php';
                $identity = &Identity::singleton();
                $name = $identity->getValue('fullname');
                if (trim($name) == '') {
                    $name = Auth::removeHook(Auth::getAuth());
                }
                $tasklist = &$GLOBALS['nag_shares']->newShare(Auth::getAuth());
                if (is_a($tasklist, 'PEAR_Error')) {
                    return;
                }
                $tasklist->set('name', sprintf(_("%s's Task List"), $name));
                $GLOBALS['nag_shares']->addShare($tasklist);
            }
        }

        return true;
    }

}
