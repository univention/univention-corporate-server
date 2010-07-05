<?php
/**
 * Horde_Form for creating task lists.
 *
 * $Horde: nag/lib/Forms/CreateTaskList.php,v 1.1.2.2 2008-07-31 10:10:03 jan Exp $
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
 * The Nag_CreateTaskListForm class provides the form for
 * creating a task list.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Nag_CreateTaskListForm extends Horde_Form {

    function Nag_CreateTaskListForm(&$vars)
    {
        parent::Horde_Form($vars, _("Create Task List"));

        $this->addVariable(_("Task List Name"), 'name', 'text', true);
        $this->addVariable(_("Task List Description"), 'description', 'longtext', false, false, null, array(4, 60));

        $this->setButtons(array(_("Create")));
    }

    function execute()
    {
        // Create new share.
        $tasklist = $GLOBALS['nag_shares']->newShare(md5(microtime()));
        if (is_a($tasklist, 'PEAR_Error')) {
            return $tasklist;
        }
        $tasklist->set('name', $this->_vars->get('name'));
        $tasklist->set('desc', $this->_vars->get('description'));
        return $GLOBALS['nag_shares']->addShare($tasklist);
    }

}
