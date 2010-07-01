<?php
/**
 * Horde_Form for editing task lists.
 *
 * $Horde: nag/lib/Forms/EditTaskList.php,v 1.1.2.2 2008-07-31 10:10:03 jan Exp $
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
 * The Nag_EditTaskListForm class provides the form for
 * editing a task list.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Nag_EditTaskListForm extends Horde_Form {

    /**
     * Task list being edited
     */
    var $_tasklist;

    function Nag_EditTaskListForm(&$vars, &$tasklist)
    {
        $this->_tasklist = &$tasklist;
        parent::Horde_Form($vars, sprintf(_("Edit %s"), $tasklist->get('name')));

        $this->addHidden('', 't', 'text', true);
        if ($this->_tasklist->get('owner') != Auth::getAuth()) {
            $this->addVariable(_("Task List Name"), 'name', 'text', false, true);
            $this->addVariable(_("Task List Description"), 'description', 'longtext', false, true);
        } else {
            $this->addVariable(_("Task List Name"), 'name', 'text', true);
            $this->addVariable(_("Task List Description"), 'description', 'longtext', false, false, null, array(4, 60));
        }

        $this->setButtons(array(_("Save")));
    }

    function activeSyncSegment($devices)
    {
        $this->addHidden('', 'activesync_devices', 'text');
        $this->addVariable('', '', 'spacer');
        $this->addVariable(_("Synchronize this calendar with the following ActiveSync devices"), '', 'header');
        foreach ($devices as $id => $config) {
            $this->addVariable(sprintf("Device \"%s\"", $id), 'activesync_' . $id, 'radio', false, false, null, 
                           array(array(_("does not synchronize with this tasklist"), _("synchronizes with this tasklist but ignores alarms"), _("synchronizes with this tasklist including alarms"))));
        }
    }

    function execute()
    {
        if ($this->_tasklist->get('owner') == Auth::getAuth()) {
            $this->_tasklist->set('name', $this->_vars->get('name'));
        }
        $this->_tasklist->set('desc', $this->_vars->get('description'));

        if ($this->_vars->get('activesync_devices', '')) {
            $params = array();
            $ids = explode('|', $this->_vars->get('activesync_devices', ''));
            foreach ($ids as $id) {
                $sync = (int) $this->_vars->get('activesync_' . $id, 0);
                if ($sync === 0 || $sync === 1 || $sync === 2) {
                    $params['activesync']['FOLDER'][$id]['S'] = $sync;
                }
            }
            $this->_tasklist->set('params', serialize($params));
        }

        $result = $this->_tasklist->save();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to save task list \"%s\": %s"), $id, $result->getMessage()));
        }
        return true;
    }

}
