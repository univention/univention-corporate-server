<?php
/**
 * This file contains all Horde_Form extensions required for editing tasks.
 *
 * $Horde: nag/lib/Forms/task.php,v 1.11.2.10 2009-03-31 14:51:04 chuck Exp $
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

/** Horde_Form_Action */
require_once 'Horde/Form/Action.php';

/**
 * The Nag_TaskForm class provides the form for adding and editing a task.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Nag 1.2
 * @package Nag
 */
class Nag_TaskForm extends Horde_Form {

    var $delete;

    function Nag_TaskForm(&$vars, $title = '', $delete = false)
    {
        parent::Horde_Form($vars, $title);
        $this->delete = $delete;

        $tasklists = Nag::listTasklists(false, PERMS_EDIT);
        $tasklist_enums = array();
        foreach ($tasklists as $tl_id => $tl) {
            $tasklist_enums[$tl_id] = $tl->get('name');
        }

        $tasklist = $vars->get('tasklist_id');
        if (empty($tasklist)) {
            reset($tasklists);
            $tasklist = key($tasklists);
        }
        $tasks = Nag::listTasks(null, null, null, array($tasklist), 4);
        $task_enums = array('' => _("No parent task"));
        $tasks->reset();
        while ($task = $tasks->each()) {
            if ($vars->get('task_id') == $task->id) {
                continue;
            }
            $task_enums[htmlspecialchars($task->id)] = str_repeat('&nbsp;', $task->indent * 4) . htmlentities($task->name, ENT_COMPAT, NLS::getCharset());
        }
        $users = array();
        $share = &$GLOBALS['nag_shares']->getShare($tasklist);
        if (!is_a($share, 'PEAR_Error')) {
            $users = $share->listUsers(PERMS_READ);
            $groups = $share->listGroups(PERMS_READ);
            if (count($groups)) {
                require_once 'Horde/Group.php';
                $horde_group = &Group::singleton();
                foreach ($groups as $group) {
                    $users = array_merge($users,
                                         $horde_group->listAllUsers($group));
                }
            }
            $users = array_flip($users);
        }
        if (count($users)) {
            require_once 'Horde/Identity.php';
            foreach (array_keys($users) as $user) {
                $identity = &Identity::singleton('none', $user);
                $fullname = $identity->getValue('fullname');
                $users[$user] = strlen($fullname) ? $fullname : $user;
            }
        }
        $priorities = array(1 => '1 ' . _("(highest)"), 2 => 2, 3 => 3,
                            4 => 4, 5 => '5 ' . _("(lowest)"));

        $this->addHidden('', 'actionID', 'text', true);
        $this->addHidden('', 'task_id', 'text', false);
        $this->addHidden('', 'old_tasklist', 'text', false);

        $this->addVariable(_("Name"), 'name', 'text', true);
        if (!$GLOBALS['prefs']->isLocked('default_tasklist') &&
            count($tasklists) > 1) {
            $v = &$this->addVariable(_("Task List"), 'tasklist_id', 'enum', true, false, false, array($tasklist_enums));
            $v->setAction(Horde_Form_Action::factory('reload'));
        }

        $v = &$this->addVariable(_("Parent task"), 'parent', 'enum', false, false, false, array($task_enums));
        $v->setOption('htmlchars', true);

        if (class_exists('Horde_Form_Type_category')) {
            $this->addVariable(_("Category"), 'category', 'category', false);
        } else {
            require_once 'Horde/Prefs/CategoryManager.php';
            require_once 'Horde/Array.php';
            $values = Horde_Array::valuesToKeys(Prefs_CategoryManager::get());
            $this->addVariable(_("Category"), 'category', 'enum', false, false, false, array($values, _("Unfiled")));
        }

        $this->addVariable(_("Assignee"), 'assignee', 'enum', false, false,
                           null, array($users, _("None")));
        $this->addVariable(_("Private?"), 'private', 'boolean', false);
        $this->addVariable(_("Due By"), 'due', 'nag_due', false);
        $this->addVariable(_("Delay Start Until"), 'start', 'nag_start', false);
        $this->addVariable(_("Alarm"), 'alarm', 'nag_alarm', false);

        $v = &$this->addVariable(_("Priority"), 'priority', 'enum', false, false, false, array($priorities));
        $v->setDefault(3);

        $this->addVariable(_("Estimated Time"), 'estimate', 'number', false);
        $this->addVariable(_("Completed?"), 'completed', 'boolean', false);
        $this->addVariable(_("Description"), 'desc', 'longtext', false, false,
                           Horde::callHook('_nag_hook_description_help', array(), 'nag', ''));

        $buttons = array(_("Save"));
        if ($delete) {
            $buttons[] = _("Delete this task");
        }
        $this->setButtons($buttons);
    }

    function renderActive()
    {
        return parent::renderActive(new Nag_TaskForm_Renderer(array('varrenderer_driver' => array('nag', 'nag')), $this->delete), $this->_vars, 'task.php', 'post');
    }

}

class Nag_TaskForm_Renderer extends Horde_Form_Renderer {

    var $delete;

    function Nag_TaskForm_Renderer($params = array(), $delete = false)
    {
        parent::Horde_Form_Renderer($params);
        $this->delete = $delete;
    }

    function _renderSubmit($submit, $reset)
    {
?><div class="control" style="padding:1em;">
    <input class="button leftFloat" name="submitbutton" type="submit" value="<?php echo _("Save") ?>" />
<?php if ($this->delete): ?>
    <input class="button rightFloat" name="submitbutton" type="submit" value="<?php echo _("Delete this task") ?>" />
<?php endif; ?>
    <div class="clear"></div>
</div>
<?php
    }

}

/**
 * The Horde_Form_Type_nag_alarm class provides a form field for editing task
 * alarms.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Horde_Form_Type_nag_alarm extends Horde_Form_Type {

    function getInfo(&$vars, &$var, &$info)
    {
        $info = $var->getValue($vars);
        if (!$info['on']) {
            $info = 0;
        }
        $info = $info['value'] * $info['unit'];
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        if ($value['on']) {
            if ($vars->get('due_type') == 'none') {
                $message = _("A due date must be set to enable alarms.");
                return false;
            }
            if (empty($value['value'])) {
                $message = _("The alarm value must not be empty.");
                return false;
            }
        }

        return true;
    }

}

/**
 * The Horde_Form_Type_nag_due class provides a form field for editing
 * task due dates.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Horde_Form_Type_nag_due extends Horde_Form_Type {

    function getInfo(&$vars, &$var, &$info)
    {
        $due_type = $vars->get('due_type');
        $due = $vars->get('due');
        if (is_array($due)) {
            $due_day = !empty($due['day']) ? $due['day'] : null;
            $due_month = !empty($due['month']) ? $due['month'] : null;
            $due_year = !empty($due['year']) ? $due['year'] : null;
            $due_hour = Util::getFormData('due_hour');
            $due_minute = Util::getFormData('due_minute');
            if (!$GLOBALS['prefs']->getValue('twentyFour')) {
                $due_am_pm = Util::getFormData('due_am_pm');
                if ($due_am_pm == 'pm') {
                    if ($due_hour < 12) {
                        $due_hour = $due_hour + 12;
                    }
                } else {
                    // Adjust 12:xx AM times.
                    if ($due_hour == 12) {
                        $due_hour = 0;
                    }
                }
            }

            $due = (int)strtotime("$due_month/$due_day/$due_year $due_hour:$due_minute");
        }

        $info = strcasecmp($due_type, 'none') ? $due : 0;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

}

/**
 * The Horde_Form_Type_nag_start class provides a form field for editing
 * task delayed start dates.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Nag 2.2
 * @package Nag
 */
class Horde_Form_Type_nag_start extends Horde_Form_Type {

    function getInfo(&$vars, &$var, &$info)
    {
        $start_type = $vars->get('start_date');
        $start = $vars->get('start');
        if (is_array($start)) {
            $start_day = !empty($start['day']) ? $start['day'] : null;
            $start_month = !empty($start['month']) ? $start['month'] : null;
            $start_year = !empty($start['year']) ? $start['year'] : null;
            $start = (int)strtotime("$start_month/$start_day/$start_year");
        }

        $info = strcasecmp($start_type, 'none') ? $start : 0;
    }

    function isValid(&$var, &$vars, $value, &$message)
    {
        return true;
    }

}
