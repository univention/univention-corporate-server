<?php
/**
 * Nag_Driver:: defines an API for implementing storage backends for Nag.
 *
 * $Horde: nag/lib/Driver.php,v 1.57.2.30 2009-10-15 16:23:26 jan Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Nag 0.1
 * @package Nag
 */
class Nag_Driver {

    /**
     * A Nag_Task instance holding the current task list.
     *
     * @var Nag_Task
     */
    var $tasks;

    /**
     * String containing the current tasklist.
     *
     * @var string
     */
    var $_tasklist = '';

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array();

    /**
     * An error message to throw when something is wrong.
     *
     * @var string
     */
    var $_errormsg;

    /**
     * Constructor - just store the $params in our newly-created
     * object. All other work is done by initialize().
     *
     * @param array $params  Any parameters needed for this driver.
     */
    function Nag_Driver($params = array(), $errormsg = null)
    {
        $this->tasks = new Nag_Task();
        $this->_params = $params;
        if (is_null($errormsg)) {
            $this->_errormsg = _("The Tasks backend is not currently available.");
        } else {
            $this->_errormsg = $errormsg;
        }
    }

    /**
     * List all alarms near $date.
     *
     * @param integer $date  The unix epoch time to check for alarms.
     *
     * @return array  An array of tasks that have alarms that match.
     */
    function listAlarms($date)
    {
        if (!$this->tasks->count()) {
            $result = $this->retrieve(0);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }
        $alarms = array();
        $this->tasks->reset();
        while ($task = &$this->tasks->each()) {
            if ($task->alarm &&
                ($task->due - ($task->alarm * 60)) <= $date) {
                $alarms[$task_id] = &$task;
            }
        }
        return $alarms;
    }

    /**
     * Generate a universal / unique identifier for a task. This is
     * NOT something that we expect to be able to parse into a
     * tasklist and a taskId.
     *
     * @return string  A nice unique string (should be 255 chars or less).
     */
    function generateUID()
    {
        return date('YmdHis') . '.'
            . substr(str_pad(base_convert(microtime(), 10, 36), 16, uniqid(mt_rand()), STR_PAD_LEFT), -16)
            . '@' . $GLOBALS['conf']['server']['name'];
    }

    /**
     * Attempts to return a concrete Nag_Driver instance based on $driver.
     *
     * @param string    $tasklist   The name of the tasklist to load.
     *
     * @param string    $driver     The type of concrete Nag_Driver subclass
     *                              to return.  The is based on the storage
     *                              driver ($driver).  The code is dynamically
     *                              included.
     *
     * @param array     $params     (optional) A hash containing any additional
     *                              configuration or connection parameters a
     *                              subclass might need.
     *
     * @return mixed    The newly created concrete Nag_Driver instance, or
     *                  false on an error.
     */
    function &factory($tasklist = '', $driver = null, $params = null)
    {
        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['storage']['driver'];
        }

        $driver = basename($driver);

        if (is_null($params)) {
            $params = Horde::getDriverConfig('storage', $driver);
        }

        require_once dirname(__FILE__) . '/Driver/' . $driver . '.php';
        $class = 'Nag_Driver_' . $driver;
        if (class_exists($class)) {
            $nag =& new $class($tasklist, $params);
            $result = $nag->initialize();
            if (is_a($result, 'PEAR_Error')) {
                $nag =& new Nag_Driver($params, sprintf(_("The Tasks backend is not currently available: %s"), $result->getMessage()));
            }
        } else {
            $nag =& new Nag_Driver($params, sprintf(_("Unable to load the definition of %s."), $class));
        }

        return $nag;
    }

    /**
     * Attempts to return a reference to a concrete Nag_Driver
     * instance based on $driver. It will only create a new instance
     * if no Nag_Driver instance with the same parameters currently
     * exists.
     *
     * This should be used if multiple storage sources are required.
     *
     * This method must be invoked as: $var =& Nag_Driver::singleton()
     *
     * @param string    $tasklist   The name of the tasklist to load.
     *
     * @param string    $driver     The type of concrete Nag_Driver subclass
     *                              to return.  The is based on the storage
     *                              driver ($driver).  The code is dynamically
     *                              included.
     *
     * @param array     $params     (optional) A hash containing any additional
     *                              configuration or connection parameters a
     *                              subclass might need.
     *
     * @return mixed    The created concrete Nag_Driver instance, or false
     *                  on error.
     */
    function &singleton($tasklist = '', $driver = null, $params = null)
    {
        static $instances = array();

        if (is_null($driver)) {
            $driver = $GLOBALS['conf']['storage']['driver'];
        }

        if (is_null($params)) {
            $params = Horde::getDriverConfig('storage', $driver);
        }

        $signature = serialize(array($tasklist, $driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] =& Nag_Driver::factory($tasklist, $driver, $params);
        }

        return $instances[$signature];
    }

    /**
     * Adds a task and handles notification.
     *
     * @param string $name        The name (short) of the task.
     * @param string $desc        The description (long) of the task.
     * @param integer $start      The start date of the task.
     * @param integer $due        The due date of the task.
     * @param integer $priority   The priority of the task.
     * @param float $estimate     The estimated time to complete the task.
     * @param integer $completed  The completion state of the task.
     * @param string $category    The category of the task.
     * @param integer $alarm      The alarm associated with the task.
     * @param string $uid         A Unique Identifier for the task.
     * @param string $parent      The parent task.
     * @param boolean $private    Whether the task is private.
     * @param string $owner       The owner of the event.
     * @param string $assignee    The assignee of the event.
     *
     * @return array              array(ID,UID) of new task
     */
    function add($name, $desc, $start = 0, $due = 0, $priority = 0,
                 $estimate = 0.0, $completed = 0, $category = '', $alarm = 0,
                 $uid = null, $parent = '', $private = false, $owner = null,
                 $assignee = null)
    {
        if (is_null($uid)) {
            $uid = $this->generateUID();
        }
        if (is_null($owner)) {
            $owner = Auth::getAuth();
        }

        $taskId = $this->_add($name, $desc, $start, $due, $priority, $estimate,
                              $completed, $category, $alarm, $uid, $parent,
                              $private, $owner, $assignee);
        if (is_a($taskId, 'PEAR_Error')) {
            return $taskId;
        }
        $task = $this->get($taskId);

        /* Log the creation of this item in the history log. */
        $history = &Horde_History::singleton();
        $history->log('nag:' . $this->_tasklist . ':' . $uid, array('action' => 'add'), true);

        /* Log completion status changes. */
        if ($completed) {
            $history->log('nag:' . $this->_tasklist . ':' . $uid, array('action' => 'complete'), true);
        }

        /* Notify users about the new event. */
        $result = Nag::sendNotification('add', $task);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        /* Add an alarm if necessary. */
        if (!empty($GLOBALS['conf']['alarms']['driver']) && !empty($alarm)) {
            $alarm = $task->toAlarm();
            if ($alarm) {
                $alarm['start'] = new Horde_Date($alarm['start']);
                require_once 'Horde/Alarm.php';
                $horde_alarm = Horde_Alarm::factory();
                $horde_alarm->set($alarm);
            }
        }

        return array($taskId, $uid);
    }

    /**
     * Modifies an existing task and handles notification.
     *
     * @param string $taskId           The task to modify.
     * @param string $name             The name (short) of the task.
     * @param string $desc             The description (long) of the task.
     * @param integer $start           The start date of the task.
     * @param integer $due             The due date of the task.
     * @param integer $priority        The priority of the task.
     * @param float $estimate          The estimated time to complete the task.
     * @param integer $completed       The completion state of the task.
     * @param string $category         The category of the task.
     * @param integer $alarm           The alarm associated with the task.
     * @param string $parent           The parent task.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     * @param string $tasklist         The new tasklist.
     */
    function modify($taskId, $name, $desc, $start = 0, $due = 0, $priority = 0,
                    $estimate = 0.0, $completed = 0, $category = '',
                    $alarm = 0, $parent = '', $private = false,
                    $owner = null, $assignee = null, $completed_date = null,
                    $tasklist = null)
    {
        /* Retrieve unmodified task. */
        $task = $this->get($taskId);
        if (is_a($task, 'PEAR_Error')) {
            return $task;
        }

        /* Avoid circular reference. */
        if ($parent == $taskId) {
            $parent = '';
        }

        $modify = $this->_modify($taskId, $name, $desc, $start, $due,
                                 $priority, $estimate, $completed, $category,
                                 $alarm, $parent, $private, $owner, $assignee,
                                 $completed_date);
        if (is_a($modify, 'PEAR_Error')) {
            return $modify;
        }

        /* Update alarm if necessary. */
        if (!empty($GLOBALS['conf']['alarms']['driver'])) {
            require_once 'Horde/Alarm.php';
            $horde_alarm = Horde_Alarm::factory();
            if (empty($alarm) || $completed) {
                $horde_alarm->delete($task->uid);
            } else {
                $task = $this->get($taskId);
                $alarm = $task->toAlarm();
                if ($alarm) {
                    $alarm['start'] = new Horde_Date($alarm['start']);
                    $horde_alarm->set($alarm);
                }
            }
        }

        $new_task = $this->get($task->id);
        $log_tasklist = $this->_tasklist;
        if (!is_null($tasklist) && $task->tasklist != $tasklist) {
            /* Moving the task to another tasklist. */
            $share = $GLOBALS['nag_shares']->getShare($task->tasklist);
            if (is_a($share, 'PEAR_Error')) {
                return $share;
            }

            if (!$share->hasPermission(Auth::getAuth(), PERMS_DELETE)) {
                $GLOBALS['notification']->push(sprintf(_("Access denied removing task from %s."), $share->get('name')), 'horde.error');
                return false;
            }

            $share = $GLOBALS['nag_shares']->getShare($tasklist);
            if (is_a($share, 'PEAR_Error')) {
                return $share;
            }

            if (!$share->hasPermission(Auth::getAuth(), PERMS_EDIT)) {
                $GLOBALS['notification']->push(sprintf(_("Access denied moving the task to %s."), $share->get('name')), 'horde.error');
            }

            $moved = $this->_move($task->id, $tasklist);
            if (is_a($moved, 'PEAR_Error')) {
                return $moved;
            }
            $new_storage = &Nag_Driver::singleton($tasklist);
            $new_task = $new_storage->get($task->id);

            /* Log the moving of this item in the history log. */
            if (!empty($task->uid)) {
                $history = &Horde_History::singleton();
                $history->log('nag:' . $task->tasklist . ':' . $task->uid, array('action' => 'delete'), true);
                $history->log('nag:' . $tasklist . ':' . $task->uid, array('action' => 'add'), true);
                $log_tasklist = $tasklist;
            }
        }

        /* Log the modification of this item in the history log. */
        if (!empty($task->uid)) {
            $history = &Horde_History::singleton();
            $history->log('nag:' . $log_tasklist . ':' . $task->uid, array('action' => 'modify'), true);
        }

        /* Log completion status changes. */
        if ($task->completed != $completed) {
            $history = &Horde_History::singleton();
            $attributes = array('action' => 'complete');
            if (!$completed) {
                $attributes['ts'] = 0;
            }
            $history->log('nag:' . $log_tasklist . ':' . $task->uid, $attributes, true);
        }

        /* Notify users about the changed event. */
        $result = Nag::sendNotification('edit', $new_task, $task);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return true;
    }
    
    /**
     * Deletes a task and handles notification.
     *
     * @param string $taskId  The task to delete.
     */
    function delete($taskId)
    {
        /* Get the task's details for use later. */
        $task = $this->get($taskId);

        $delete = $this->_delete($taskId);
        if (is_a($delete, 'PEAR_Error')) {
            return $delete;
        }

        /* Log the deletion of this item in the history log. */
        if (!empty($task->uid)) {
            $history = &Horde_History::singleton();
            $history->log('nag:' . $this->_tasklist . ':' . $task->uid, array('action' => 'delete'), true);
        }

        /* Notify users about the deleted event. */
        $result = Nag::sendNotification('delete', $task);
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        /* Delete alarm if necessary. */
        if (!empty($GLOBALS['conf']['alarms']['driver']) &&
            !empty($task->alarm)) {
            require_once 'Horde/Alarm.php';
            $horde_alarm = Horde_Alarm::factory();
            $horde_alarm->delete($task->uid);
        }

        return true;
    }

    /**
     * Retrieves tasks from the database.
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function retrieve()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Retrieves sub-tasks from the database.
     *
     * @param string $parentId  The parent id for the sub-tasks to retrieve.
     *
     * @return array  List of sub-tasks.
     */
    function getChildren($parentId)
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Retrieves one task from the database.
     *
     * @param string $taskId  The id of the task to retrieve.
     *
     * @return Nag_Task  A Nag_Task object.
     */
    function get($taskId)
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * Retrieves one task from the database by UID.
     *
     * @param string $uid  The UID of the task to retrieve.
     *
     * @return Nag_Task  A Nag_Task object.
     */
    function getByUID($uid)
    {
        return PEAR::raiseError($this->_errormsg);
    }

}

/**
 * Nag_Task handles as single task as well as a list of tasks and implements a
 * recursive iterator to handle a (hierarchical) list of tasks.
 *
 * @package Nag
 */
class Nag_Task {

    /**
     * The task id.
     *
     * @var string
     */
    var $id;

    /**
     * This task's tasklist id.
     *
     * @var string
     */
    var $tasklist;

    /**
     * The task uid.
     *
     * @var string
     */
    var $uid;

    /**
     * The task owner.
     *
     * @var string
     */
    var $owner;

    /**
     * The task assignee.
     *
     * @var string
     */
    var $assignee;

    /**
     * The task title.
     *
     * @var string
     */
    var $name;

    /**
     * The task decription.
     *
     * @var string
     */
    var $desc;

    /**
     * The start date timestamp.
     *
     * @var integer
     */
    var $start;

    /**
     * The due date timestamp.
     *
     * @var integer
     */
    var $due;

    /**
     * The task priority.
     *
     * @var integer
     */
    var $priority;

    /**
     * The estimated task length.
     *
     * @var float
     */
    var $estimate;

    /**
     * Whether the task is completed.
     *
     * @var boolean
     */
    var $completed;

    /**
     * The completion date timestamp.
     *
     * @var integer
     */
    var $completed_date;

    /**
     * The task category
     *
     * @var string
     */
    var $category;

    /**
     * The task alarm threshold.
     *
     * @var integer
     */
    var $alarm;

    /**
     * Whether the task is private.
     *
     * @var boolean
     */
    var $private;

    /**
     * URL to view the task.
     *
     * @var string
     */
    var $view_link;

    /**
     * URL to complete the task.
     *
     * @var string
     */
    var $complete_link;

    /**
     * URL to edit the task.
     *
     * @var string
     */
    var $edit_link;

    /**
     * URL to delete the task.
     *
     * @var string
     */
    var $delete_link;

    /**
     * The parent task's id.
     *
     * @var string
     */
    var $parent_id = '';

    /**
     * The parent task.
     *
     * @var Nag_Task
     */
    var $parent;

    /**
     * The sub-tasks.
     *
     * @var array
     */
    var $children = array();

    /**
     * This task's idention (child) level.
     *
     * @var integer
     */
    var $indent = 0;

    /**
     * Whether this is the last sub-task.
     *
     * @var boolean
     */
    var $lastChild;

    /**
     * Internal flag.
     *
     * @var boolean
     * @see each()
     */
    var $_inlist = false;

    /**
     * Internal pointer.
     *
     * @var integer
     * @see each()
     */
    var $_pointer;

    /**
     * Task id => pointer dictionary.
     *
     * @var array
     */
    var $_dict = array();

    /**
     * Constructor.
     *
     * Takes a hash and returns a nice wrapper around it.
     *
     * @param array $task  A task hash.
     */
    function Nag_Task($task = null)
    {
        if ($task) {
            $this->merge($task);
        }
    }

    /**
     * Merges a task hash into this task object.
     *
     * @param array $task  A task hash.
     */
    function merge($task)
    {
        foreach ($task as $key => $val) {
            if ($key == 'tasklist_id') {
                $key = 'tasklist';
            } elseif ($key == 'task_id') {
                $key = 'id';
            } elseif ($key == 'parent') {
                $key = 'parent_id';
            }
            $this->$key = $val;
        }
    }

    /**
     * Saves this task in the storage backend.
     */
    function save()
    {
        $storage = &Nag_Driver::singleton($this->tasklist);
        return $storage->modify($this->id,
                                $this->name,
                                $this->desc,
                                $this->start,
                                $this->due,
                                $this->priority,
                                $this->estimate,
                                $this->completed,
                                $this->category,
                                $this->alarm,
                                $this->parent_id,
                                $this->private,
                                $this->owner,
                                $this->assignee,
                                $this->completed_date);
    }

    /**
     * Returns the parent task of this task, if one exists.
     *
     * @return Nag_Task  The parent task, null if none exists, PEAR_Error on
     *                   failure.
     */
    function getParent()
    {
        if (!$this->parent_id) {
            return null;
        }
        return Nag::getTask($this->tasklist, $this->parent_id);
    }

    /**
     * Adds a sub task to this task.
     *
     * @param Nag_Task $task  A sub task.
     */
    function add(&$task)
    {
        $this->_dict[$task->id] = count($this->children);
        $task->parent = &$this;
        $this->children[] = &$task;
    }

    /**
     * Loads all sub-tasks.
     */
    function loadChildren()
    {
        $storage = &Nag_Driver::singleton($this->tasklist);
        $children = $storage->getChildren($this->id);
        if (!is_a($children, 'PEAR_Error')) {
            $this->children = $children;
        }
    }

    /**
     * Merges an array of tasks into this task's children.
     *
     * @param array $children  A list of Nag_Tasks.
     *
     */
    function mergeChildren($children)
    {
        for ($i = 0, $c = count($children); $i < $c; ++$i) {
            $this->add($children[$i]);
        }
    }

    /**
     * Returns a sub task by its id.
     *
     * The methods goes recursively through all sub tasks until it finds the
     * searched task.
     *
     * @param string $key  A task id.
     *
     * @return Nag_Task  The searched task or null.
     */
    function &get($key)
    {
        if (isset($this->_dict[$key])) {
            $task = &$this->children[$this->_dict[$key]];
        } else {
            $task = null;
        }
        return $task;
    }

    /**
     * Returns whether this is a task (not a container) or contains any sub
     * tasks.
     *
     * @return boolean  True if this is a task or has sub tasks.
     */
    function hasTasks()
    {
        if ($this->id) {
            return true;
        }
        return $this->hasSubTasks();
    }

    /**
     * Returns whether this task contains any sub tasks.
     *
     * @return boolean  True if this task has sub tasks.
     */
    function hasSubTasks()
    {
        foreach ($this->children as $task) {
            if ($task->hasTasks()) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns whether all sub tasks are completed.
     *
     * @return boolean  True if all sub tasks are completed.
     */
    function childrenCompleted()
    {
        foreach ($this->children as $task) {
            if (!$task->completed || !$task->childrenCompleted()) {
                return false;
            }
        }
        return true;
    }

    /**
     * Returns the number of tasks including this and any sub tasks.
     *
     * @return integer  The number of tasks and sub tasks.
     */
    function count()
    {
        $count = $this->id ? 1 : 0;
        foreach ($this->children as $task) {
            $count += $task->count();
        }
        return $count;
    }

    /**
     * Returns the estimated length for this and any sub tasks.
     *
     * @return integer  The estimated length sum.
     */
    function estimation()
    {
        $estimate = $this->estimate;
        foreach ($this->children as $task) {
            $estimate += $task->estimation();
        }
        return $estimate;
    }

    /**
     * Format the description - link URLs, etc.
     *
     * @return string
     */
    function getFormattedDescription()
    {
        require_once 'Horde/Text/Filter.php';
        $desc = Text_Filter::filter($this->desc, 'text2html', array('parselevel' => TEXT_HTML_MICRO));
        $desc = Horde::callHook('_nag_hook_format_description', array($desc), 'nag', $desc);
        return $desc;
    }

    /**
     * Resets the tasks iterator.
     *
     * Call this each time before looping through the tasks.
     *
     * @see each()
     */
    function reset()
    {
        foreach (array_keys($this->children) as $key) {
            $this->children[$key]->reset();
        }
        $this->_pointer = 0;
        $this->_inlist = false;
    }

    /**
     * Returns the next task iterating through all tasks and sub tasks.
     *
     * Call reset() each time before looping through the tasks:
     * <code>
     * $tasks->reset();
     * while ($task = &$tasks->each() {
     *     ...
     * }
     *
     * @see reset()
     */
    function &each()
    {
        if ($this->id && !$this->_inlist) {
            $this->_inlist = true;
            return $this;
        }
        if ($this->_pointer >= count($this->children)) {
            $task = false;
            return $task;
        }
        $next = &$this->children[$this->_pointer]->each();
        if ($next) {
            return $next;
        }
        $this->_pointer++;
        return $this->each();
    }

    /**
     * Processes a list of tasks by adding action links, obscuring details of
     * private tasks and calculating indentation.
     *
     * @param integer $indent  The indention level of the tasks.
     */
    function process($indent = 0)
    {
        /* Link cache. */
        static $view_url_list, $task_url_list;

        /* Set indention. */
        $this->indent = $indent;
        if ($this->id) {
            ++$indent;
        }

        /* Process children. */
        for ($i = 0, $c = count($this->children); $i < $c; ++$i) {
            $this->children[$i]->process($indent);
        }

        /* Mark last child. */
        if (count($this->children)) {
            $this->children[count($this->children) - 1]->lastChild = true;
        }

        /* Only process further if this is really a (parent) task, not only a
         * task list container. */
        if (!$this->id) {
            return;
        }

        if (!isset($view_url_list[$this->tasklist])) {
            $view_url_list[$this->tasklist] = Util::addParameter(Horde::applicationUrl('view.php'), 'tasklist', $this->tasklist);
            $task_url_list[$this->tasklist] = Util::addParameter(Horde::applicationUrl('task.php'), 'tasklist', $this->tasklist);
        }

        /* Obscure private tasks. */
        if ($this->private && $this->owner != Auth::getAuth()) {
            $this->name = _("Private Task");
            $this->desc = '';
            $this->category = _("Private");
        }

        /* Create task links. */
        $this->view_link = Util::addParameter($view_url_list[$this->tasklist], 'task', $this->id);

        $task_url_task = Util::addParameter($task_url_list[$this->tasklist], 'task', $this->id);
        $this->complete_link = Util::addParameter($task_url_task, 'actionID', 'complete_task');
        $this->edit_link = Util::addParameter($task_url_task, 'actionID', 'modify_task');
        $this->delete_link = Util::addParameter($task_url_task, 'actionID', 'delete_tasks');
    }

    /**
     * Returns the HTML code for any tree icons, when displaying this task in
     * a tree view.
     *
     * @return string  The HTML code for necessary tree icons.
     */
    function treeIcons()
    {
        $treedir = $GLOBALS['registry']->getImageDir('horde');
        $html = '';

        $parent = $this->parent;
        for ($i = 1; $i < $this->indent; ++$i) {
            if ($parent && $parent->lastChild) {
                $html = Horde::img('tree/blank.png', '', '', $treedir) . $html;
            } else {
                $html = Horde::img('tree/line.png', '|', '', $treedir) . $html;
            }
            $parent = $parent->parent;
        }
        if ($this->indent) {
            if ($this->lastChild) {
                $html .= Horde::img(empty($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'tree/joinbottom.png' : 'tree/rev-joinbottom.png', '\\', '', $treedir);
            } else {
                $html .= Horde::img(empty($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'tree/join.png' : 'tree/rev-join.png', '+', '', $treedir);
            }
        }

        return $html;
    }

    /**
     * Sorts sub tasks by the given criteria.
     *
     * @param string $sortby     The field by which to sort
     *                           (NAG_SORT_PRIORITY, NAG_SORT_NAME
     *                           NAG_SORT_DUE, NAG_SORT_COMPLETION).
     * @param integer $sortdir   The direction by which to sort
     *                           (NAG_SORT_ASCEND, NAG_SORT_DESCEND).
     * @param string $altsortby  The secondary sort field.
     */
    function sort($sortby, $sortdir, $altsortby)
    {
        /* Sorting criteria for the task list. */
        $sort_functions = array(
            NAG_SORT_PRIORITY => 'ByPriority',
            NAG_SORT_NAME => 'ByName',
            NAG_SORT_CATEGORY => 'ByCategory',
            NAG_SORT_DUE => 'ByDue',
            NAG_SORT_COMPLETION => 'ByCompletion',
            NAG_SORT_ASSIGNEE => 'ByAssignee',
            NAG_SORT_ESTIMATE => 'ByEstimate',
            NAG_SORT_OWNER => 'ByOwner'
        );

        /* Sort the array if we have a sort function defined for this
         * field. */
        if (isset($sort_functions[$sortby])) {
            $prefix = ($sortdir == NAG_SORT_DESCEND) ? '_rsort' : '_sort';
            usort($this->children, array('Nag', $prefix . $sort_functions[$sortby]));
            if (isset($sort_functions[$altsortby]) && $altsortby !== $sortby) {
                $task_buckets = array();
                for ($i = 0, $c = count($this->children); $i < $c; ++$i) {
                    if (!isset($task_buckets[$this->children[$i]->$sortby])) {
                        $task_buckets[$this->children[$i]->$sortby] = array();
                    }
                    $task_buckets[$this->children[$i]->$sortby][] = &$this->children[$i];
                }
                $tasks = array();
                foreach ($task_buckets as $task_bucket) {
                    usort($task_bucket, array('Nag', $prefix . $sort_functions[$altsortby]));
                    $tasks = array_merge($tasks, $task_bucket);
                }
                $this->children = $tasks;
            }

            /* Mark last child. */
            for ($i = 0, $c = count($this->children); $i < $c; ++$i) {
                $this->children[$i]->lastChild = false;
            }
            if (count($this->children)) {
                $this->children[count($this->children) - 1]->lastChild = true;
            }

            for ($i = 0, $c = count($this->children); $i < $c; ++$i) {
                $this->_dict[$this->children[$i]->id] = $i;
                $this->children[$i]->sort($sortby, $sortdir, $altsortby);
            }
        }
    }

    /**
     * Returns a hash representation for this task.
     *
     * @return array  A task hash.
     */
    function toHash()
    {
        return array('tasklist_id' => $this->tasklist,
                     'task_id' => $this->id,
                     'uid' => $this->uid,
                     'parent' => $this->parent_id,
                     'owner' => $this->owner,
                     'assignee' => $this->assignee,
                     'name' => $this->name,
                     'desc' => $this->desc,
                     'category' => $this->category,
                     'start' => $this->start,
                     'due' => $this->due,
                     'priority' => $this->priority,
                     'estimate' => $this->estimate,
                     'completed' => $this->completed,
                     'completed_date' => $this->completed_date,
                     'alarm' => $this->alarm,
                     'private' => $this->private);
    }

    /**
     * Returns an alarm hash of this task suitable for Horde_Alarm.
     *
     * @param string $user  The user to return alarms for.
     * @param Prefs $prefs  A Prefs instance.
     *
     * @return array  Alarm hash or null.
     */
    function toAlarm($user = null, $prefs = null)
    {
        if (empty($this->alarm) || $this->completed) {
            return;
        }

        if (empty($user)) {
            $user = Auth::getAuth();
        }
        if (empty($prefs)) {
            $prefs = $GLOBALS['prefs'];
        }

        $methods = @unserialize($prefs->getValue('task_alarms'));
        if (!$methods) {
            $methods = array();
        }

        if (isset($methods['notify'])) {
            $methods['notify']['show'] = array(
                '__app' => $GLOBALS['registry']->getApp(),
                'task' => $this->id,
                'tasklist' => $this->tasklist);
            if (!empty($methods['notify']['sound'])) {
                if ($methods['notify']['sound'] == 'on') {
                    // Handle boolean sound preferences;
                    $methods['notify']['sound'] = $GLOBALS['registry']->get('themesuri') . '/sounds/theetone.wav';
                } else {
                    // Else we know we have a sound name that can be
                    // served from Horde.
                    $methods['notify']['sound'] = $GLOBALS['registry']->get('themesuri', 'horde') . '/sounds/' . $methods['notify']['sound'];
                }
            }
        }
        if (isset($methods['popup'])) {
            $methods['popup']['message'] = $this->name;
            if (!empty($this->desc)) {
                $methods['popup']['message'] .= "\n\n" . $this->desc;
            }
        }
        if (isset($methods['mail'])) {
            $methods['mail']['body'] = sprintf(
                _("We would like to remind you of this due task.\n\n%s\n\nDate: %s\nTime: %s\n\n%s"),
                $this->name,
                strftime($prefs->getValue('date_format'), $this->due),
                date($prefs->getValue('twentyFour') ? 'H:i' : 'h:ia', $this->due),
                $this->desc);
        }
        return array(
            'id' => $this->uid,
            'user' => $user,
            'start' => $this->due - $this->alarm * 60,
            'methods' => array_keys($methods),
            'params' => $methods,
            'title' => $this->name,
            'text' => $this->desc);
    }

    /**
     * Exports this task in iCalendar format.
     *
     * @param Horde_iCalendar $calendar  A Horde_iCalendar object that acts as
     *                                   the container.
     *
     * @return Horde_iCalendar_vtodo  A vtodo component of this task.
     */
    function toiCalendar(&$calendar)
    {
        $vTodo = &Horde_iCalendar::newComponent('vtodo', $calendar);
        $v1 = $calendar->getAttribute('VERSION') == '1.0';

        $vTodo->setAttribute('UID', $this->uid);

        if (!empty($this->assignee)) {
            $vTodo->setAttribute('ORGANIZER', $this->assignee);
        }

        if (!empty($this->name)) {
            $vTodo->setAttribute('SUMMARY', $v1 ? $this->name : String::convertCharset($this->name, NLS::getCharset(), 'utf-8'));
        }

        if (!empty($this->desc)) {
            $vTodo->setAttribute('DESCRIPTION', $v1 ? $this->desc : String::convertCharset($this->desc, NLS::getCharset(), 'utf-8'));
        }

        if (isset($this->priority)) {
            $vTodo->setAttribute('PRIORITY', $this->priority);
        }

        if (!empty($this->parent_id)) {
            $vTodo->setAttribute('RELATED-TO', $this->parent->uid);
        }

        if ($this->private) {
            $vTodo->setAttribute('CLASS', 'PRIVATE');
        }

        if (!empty($this->start)) {
            $vTodo->setAttribute('DTSTART', $this->start);
        }

        if ($this->due) {
            $vTodo->setAttribute('DUE', $this->due);

            if ($this->alarm) {
                if ($v1) {
                    $vTodo->setAttribute('AALARM', $this->due - $this->alarm * 60);
                } else {
                    $vAlarm = &Horde_iCalendar::newComponent('valarm', $vTodo);
                    $vAlarm->setAttribute('ACTION', 'DISPLAY');
                    $vAlarm->setAttribute('TRIGGER;VALUE=DURATION', '-PT' . $this->alarm . 'M');
                    $vTodo->addComponent($vAlarm);
                }
            }
        }

        if ($this->completed) {
            $vTodo->setAttribute('STATUS', 'COMPLETED');
            $vTodo->setAttribute('COMPLETED', $this->completed_date ? $this->completed_date : time());
        } else {
            if ($v1) {
                $vTodo->setAttribute('STATUS', 'NEEDS ACTION');
            } else {
                $vTodo->setAttribute('STATUS', 'NEEDS-ACTION');
            }
        }

        if (!empty($this->category)) {
            $vTodo->setAttribute('CATEGORIES', $v1 ? $this->category : String::convertCharset($this->category, NLS::getCharset(), 'utf-8'));
        }

        /* Get the task's history. */
        $history = &Horde_History::singleton();
        $log = $history->getHistory('nag:' . $this->tasklist . ':' . $this->uid);
        if ($log && !is_a($log, 'PEAR_Error')) {
            foreach ($log->getData() as $entry) {
                switch ($entry['action']) {
                case 'add':
                    $created = $entry['ts'];
                    break;

                case 'modify':
                    $modified = $entry['ts'];
                    break;
                }
            }
        }
        if (!empty($created)) {
            $vTodo->setAttribute($v1 ? 'DCREATED' : 'CREATED', $created);
            if (empty($modified)) {
                $modified = $created;
            }
        }
        if (!empty($modified)) {
            $vTodo->setAttribute('LAST-MODIFIED', $modified);
        }

        return $vTodo;
    }

    /**
     * Creates a task from a Horde_iCalendar_vtodo object.
     *
     * @param Horde_iCalendar_vtodo $vTodo  The iCalendar data to update from.
     */
    function fromiCalendar($vTodo)
    {
        $name = $vTodo->getAttribute('SUMMARY');
        if (!is_array($name) && !is_a($name, 'PEAR_Error')) {
            $this->name = $name;
        }

        $assignee = $vTodo->getAttribute('ORGANIZER');
        if (!is_array($assignee) && !is_a($assignee, 'PEAR_Error')) {
            $this->assignee = $assignee;
        }

        $uid = $vTodo->getAttribute('UID');
        if (!is_array($uid) && !is_a($uid, 'PEAR_Error')) {
            $this->uid = $uid;
        }

        $relations = $vTodo->getAttribute('RELATED-TO');
        if (!is_a($relations, 'PEAR_Error')) {
            if (!is_array($relations)) {
                $relations = array($relations);
            }
            $params = $vTodo->getAttribute('RELATED-TO', true);
            foreach ($relations as $id => $relation) {
                if (empty($params[$id]['RELTYPE']) ||
                    String::upper($params[$id]['RELTYPE']) == 'PARENT') {
                    $storage = &Nag_Driver::singleton($this->tasklist);

                    $parent = $storage->getByUID($relation);
                    if (!is_a($parent, 'PEAR_Error')) {
                        $this->parent_id = $parent->id;
                    }
                    break;
                }
            }
        }

        $start = $vTodo->getAttribute('DTSTART');
        if (!is_a($start, 'PEAR_Error')) {
            if (!is_array($start)) {
                // Date-Time field
                $this->start = $start;
            } else {
                // Date field
                $this->start = mktime(0, 0, 0, (int)$start['month'], (int)$start['mday'], (int)$start['year']);
            }
        }

        $due = $vTodo->getAttribute('DUE');
        if (!is_a($due, 'PEAR_Error')) {
            if (is_array($due)) {
                $this->due = mktime(0, 0, 0, (int)$due['month'], (int)$due['mday'], (int)$due['year']);
            } elseif (!empty($due)) {
                $this->due = $due;
            }
        }

        // vCalendar 1.0 alarms
        $alarm = $vTodo->getAttribute('AALARM');
        if (!is_array($alarm) && !is_a($alarm, 'PEAR_Error') &&
            !empty($alarm) && !empty($this->due)) {
            $this->alarm = intval(($this->due - $alarm) / 60);
            if ($this->alarm === 0) {
                // We don't support alarms exactly at due date.
                $this->alarm = 1;
            }
        }

        // @TODO: vCalendar 2.0 alarms

        $desc = $vTodo->getAttribute('DESCRIPTION');
        if (!is_array($desc) && !is_a($desc, 'PEAR_Error')) {
            $this->desc = $desc;
        }

        $priority = $vTodo->getAttribute('PRIORITY');
        if (!is_array($priority) && !is_a($priority, 'PEAR_Error')) {
            $this->priority = $priority;
        }

        $cat = $vTodo->getAttribute('CATEGORIES');
        if (!is_array($cat) && !is_a($cat, 'PEAR_Error')) {
            $this->category = $cat;
        }

        $status = $vTodo->getAttribute('STATUS');
        if (!is_array($status) && !is_a($status, 'PEAR_Error')) {
            $this->completed = !strcasecmp($status, 'COMPLETED');
        }

        $class = $vTodo->getAttribute('CLASS');
        if (!is_array($class) && !is_a($class, 'PEAR_Error')) {
            $class = String::upper($class);
            $this->private = $class == 'PRIVATE' || $class == 'CONFIDENTIAL';
        }
    }

}
