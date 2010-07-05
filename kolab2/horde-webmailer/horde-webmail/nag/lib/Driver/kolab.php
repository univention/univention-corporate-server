<?php
/**
 * Nag driver classes for the Kolab IMAP server.
 *
 * $Horde: nag/lib/Driver/kolab.php,v 1.6.10.17 2009-10-22 14:24:20 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Nag
 */

/** Kolab */
require_once 'Horde/Kolab.php';

/**
 * Nag driver proxy class for the Kolab IMAP server.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Nag
 */
class Nag_Driver_kolab extends Nag_Driver {

    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * The wrapper to decide between the Kolab implementation
     *
     * @var Nag_Driver_kolab_wrapper
     */
    var $_wrapper = null;

    /**
     * Constructs a new Kolab storage object.
     *
     * @param string $tasklist  The tasklist to load.
     * @param array $params     A hash containing connection parameters.
     */
    function Nag_Driver_kolab($tasklist, $params = array())
    {
        if (empty($tasklist)) {
            $tasklist = Auth::getAuth();
        }

        $this->_tasklist = $tasklist;

        $this->_kolab = &new Kolab();
        if (empty($this->_kolab->version)) {
            $wrapper = 'Nag_Driver_kolab_wrapper_old';
        } else {
            $wrapper = 'Nag_Driver_kolab_wrapper_new';
        }

        $this->_wrapper = &new $wrapper($this->_tasklist, $this->_kolab);
    }

    /**
     * Attempts to open a Kolab Groupware folder.
     *
     * @return boolean  True on success, PEAR_Error on failure.
     */
    function initialize()
    {
        return $this->_wrapper->connect();
    }

    /**
     * Retrieves one task from the store.
     *
     * @param string $taskId  The id of the task to retrieve.
     *
     * @return array  The array of task attributes.
     */
    function get($taskId)
    {
        return $this->_wrapper->get($taskId);
    }

    /**
     * Retrieves one task from the database by UID.
     *
     * @param string $uid  The UID of the task to retrieve.
     *
     * @return array  The array of task attributes.
     */
    function getByUID($uid)
    {
        return $this->_wrapper->getByUID($uid);
    }

    /**
     * Adds a task to the backend storage.
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
     * @param string $parent      The parent task id.
     * @param boolean $private    Whether the task is private.
     * @param string $owner       The owner of the event.
     * @param string $assignee    The assignee of the event.
     *
     * @return string  The Nag ID of the new task.
     */
    function _add($name, $desc, $start = 0, $due = 0, $priority = 0,
                  $completed = 0, $estimate = 0.0, $category = '', $alarm = 0,
                  $uid = null, $parent = null, $private = false, $owner = null,
                  $assignee = null)
    {
        return $this->_wrapper->add($name, $desc, $start, $due, $priority,
                                    $completed, $estimate, $category, $alarm,
                                    $uid, $parent, $private, $owner, $assignee);
    }

    /**
     * Modifies an existing task.
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
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     *
     * @return boolean  Indicates if the modification was successfull.
     */
    function _modify($taskId, $name, $desc, $start = 0, $due = 0, $priority = 0,
                     $estimate = 0.0, $completed = 0, $category = '',
                     $alarm = 0, $parent = null, $private = false,
                     $owner = null, $assignee = null, $completed_date = null)
    {
        return $this->_wrapper->modify($taskId, $name, $desc, $start, $due,
                                       $priority, $estimate, $completed,
                                       $category, $alarm, $parent, $private,
                                       $owner, $assignee, $completed_date);
    }

    /**
     * Moves a task to a different tasklist.
     *
     * @param string $taskId       The task to move.
     * @param string $newTasklist  The new tasklist.
     */
    function _move($taskId, $newTasklist)
    {
        return $this->_wrapper->move($taskId, $newTasklist);
    }

    /**
     * Deletes a task from the backend.
     *
     * @param string $taskId  The task to delete.
     */
    function _delete($taskId)
    {
        return $this->_wrapper->delete($taskId);
    }

    /**
     * Deletes all tasks from the backend.
     */
    function deleteAll()
    {
        return $this->_wrapper->deleteAll();
    }

    /**
     * Retrieves tasks from the Kolab server.
     *
     * @param integer $completed  Which tasks to retrieve (1 = all tasks,
     *                            0 = incomplete tasks, 2 = complete tasks).
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function retrieve($completed = 1)
    {
        $tasks = $this->_wrapper->retrieve($completed);
        if (is_a($tasks, 'PEAR_Error')) {
            return $tasks;
        }

        $this->tasks = $tasks;

        return true;
    }

    /**
     * Lists all alarms near $date.
     *
     * @param integer $date  The unix epoch time to check for alarms.
     *
     * @return array  An array of tasks that have alarms that match.
     */
    function listAlarms($date)
    {
        return $this->_wrapper->listAlarms($date);
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
        return $this->_wrapper->getChildren($parentId);
    }
}

/**
 * Horde Nag wrapper to distinguish between both Kolab driver implementations.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Nag
 */

class Nag_Driver_kolab_wrapper {

    /**
     * Indicates if the wrapper has connected or not
     *
     * @var boolean
     */
    var $_connected = false;

    /**
     * String containing the current tasklist name.
     *
     * @var string
     */
    var $_tasklist = '';

    /**
     * Our Kolab server connection.
     *
     * @var Kolab
     */
    var $_kolab = null;

    /**
     * Constructor
     *
     * @param string      $tasklist  The tasklist to load.
     * @param Horde_Kolab $kolab     The Kolab connection object
     */
    function Nag_Driver_kolab_wrapper($tasklist, &$kolab)
    {
        $this->_tasklist = $tasklist;
        $this->_kolab = &$kolab;
    }

    /**
     * Connect to the Kolab backend
     *
     * @param int    $loader         The version of the XML
     *                               loader
     *
     * @return mixed True on success, a PEAR error otherwise
     */
    function connect($loader = 0)
    {
        if ($this->_connected) {
            return true;
        }

        $result = $this->_kolab->open($this->_tasklist, $loader);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_connected = true;

        return true;
    }
}

/**
 * Old Nag driver for the Kolab IMAP server.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Nag
 */
class Nag_Driver_kolab_wrapper_old extends Nag_Driver_kolab_wrapper {

    function _buildTask()
    {
        $private = String::lower($this->_kolab->getVal('sensitivity'));
        $private = ($private == 'private' || $private == 'confidential');

        return array(
            'tasklist_id' => $this->_tasklist,
            'task_id' => $this->_kolab->getUID(),
            'uid' => $this->_kolab->getUID(),
            'owner' => Auth::getAuth(),
            'name' => $this->_kolab->getStr('summary'),
            'desc' => $this->_kolab->getStr('body'),
            'category' => $this->_kolab->getStr('categories'),
            'due' => Kolab::decodeDateOrDateTime($this->_kolab->getVal('due-date')),
            'priority' => $this->_kolab->getVal('priority'),
            'parent' => $this->_kolab->getVal('parent'),
            'estimate' => (float)$this->_kolab->getVal('priority'),
            'completed' => Kolab::percentageToBoolean($this->_kolab->getVal('completed')),
            'alarm' => $this->_kolab->getVal('alarm'),
            'private' => $private,
        );
    }

    /**
     * Retrieves one task from the store.
     *
     * @param string $taskId  The id of the task to retrieve.
     *
     * @return array  The array of task attributes.
     */
    function get($taskId)
    {
        $result = $this->_kolab->loadObject($taskId);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return new Nag_Task($this->_buildTask());
    }

    /**
     * Retrieves one task from the database by UID.
     *
     * @param string $uid  The UID of the task to retrieve.
     *
     * @return array  The array of task attributes.
     */
    function getByUID($uid)
    {
        return PEAR::raiseError("Not supported");
    }

    /**
     * @todo Utilize $owner, $assignee, and $completed_date
     * parameters.
     *
     * @param string $name             The name (short) of the task.
     * @param string $desc             The description (long) of the task.
     * @param integer $start           The start date of the task.
     * @param integer $due             The due date of the task.
     * @param integer $priority        The priority of the task.
     * @param float $estimate          The estimated time to complete the task.
     * @param integer $completed       The completion state of the task.
     * @param string $category         The category of the task.
     * @param integer $alarm           The alarm associated with the task.
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     *
     * @return string  The ID of the task.
     */
    function _setObject($name, $desc, $start = 0, $due = 0, $priority = 0,
                        $estimate = 0.0, $completed = 0, $category = '',
                        $alarm = 0, $parent = null, $private = false,
                        $owner = null, $assignee = null, $completed_date = null)
    {
        if ($due == 0) {
            $alarm = 0;
        }

        $this->_kolab->setStr('summary', $name);
        $this->_kolab->setStr('body', $desc);
        $this->_kolab->setStr('categories', $category);
        $this->_kolab->setVal('priority', $priority);
        $this->_kolab->setVal('estimate', number_format($priority, 2));
        $this->_kolab->setVal('completed', Kolab::booleanToPercentage($completed));
        $this->_kolab->setVal('start-date', Kolab::encodeDateTime($start));
        $this->_kolab->setVal('due-date', Kolab::encodeDateTime($due));
        $this->_kolab->setVal('alarm', $alarm);
        if ($parent) {
            $this->_kolab->setVal('parent', $parent);
        }
        if ($private) {
            $this->_kolab->setVal('sensitivity', 'private');
        }

        $result = $this->_kolab->saveObject();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $this->_kolab->getUID();
    }

    /**
     * Adds a task to the backend storage.
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
     * @param string $parent      The parent task id.
     * @param boolean $private    Whether the task is private.
     * @param string $owner       The owner of the event.
     * @param string $assignee    The assignee of the event.
     *
     * @return string  The Nag ID of the new task.
     */
    function add($name, $desc, $start = 0, $due = 0, $priority = 0,
                 $completed = 0, $estimate = 0.0, $category = '', $alarm = 0,
                 $uid = null, $parent = null, $private = false, $owner = null,
                 $assignee = null)
    {
        // Usually provided by the generic Driver class
        if ($uid !== null) {
            $uid = $this->generateUID();
        }

        // Load the object into the kolab driver
        $object = $this->_kolab->newObject($uid);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        return $this->_setObject($name, $desc, $start, $due, $priority,
                                 $completed, $estimate, $category, $alarm,
                                 $parent, $private, $owner, $assignee);
    }

    /**
     * Modifies an existing task.
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
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     *
     * @return boolean  Indicates if the modification was successfull.
     */
    function modify($taskId, $name, $desc, $start = 0, $due = 0,
                    $priority = 0, $estimate = 0.0, $completed = 0,
                    $category = '', $alarm = 0, $parent = null,
                    $private = false, $owner = null, $assignee = null,
                    $completed_date = null)
    {
        // Load the object into the kolab driver
        $result = $this->_kolab->loadObject($taskId);
        if (is_a($object, 'PEAR_Error')) {
            return $object;
        }

        $result = $this->_setObject($name, $desc, $start, $due, $priority,
                                    $estimate, $completed, $category, $alarm,
                                    $parent, $private, $owner, $assignee,
                                    $completed_date);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $result == $taskId;
    }

    /**
     * Moves a task to a different tasklist.
     *
     * @param string $taskId       The task to move.
     * @param string $newTasklist  The new tasklist.
     */
    function move($taskId, $newTasklist)
    {
        return $this->_kolab->moveObject($taskId, $newTasklist);
    }

    /**
     * Deletes a task from the backend.
     *
     * @param string $taskId  The task to delete.
     */
    function delete($taskId)
    {
        return $this->_kolab->removeObjects($taskId);
    }

    /**
     * Deletes all tasks from the backend.
     */
    function deleteAll()
    {
        return $this->_kolab->removeAllObjects();
    }

    /**
     * Retrieves tasks from the Kolab server.
     *
     * @param integer $completed  Which tasks to retrieve (1 = all tasks,
     *                            0 = incomplete tasks, 2 = complete tasks,
     *                            3 = future tasks, 4 = future and incomplete
     *                            tasks).
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function retrieve($completed = 1)
    {
        $tasks = array();

        $msg_list = $this->_kolab->listObjects();
        if (is_a($msg_list, 'PEAR_Error')) {
            return $msg_list;
        }

        if (empty($msg_list)) {
            return true;
        }

        foreach ($msg_list as $msg) {
            $result = &$this->_kolab->loadObject($msg, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $complete = Kolab::percentageToBoolean($this->_kolab->getVal('completed'));
            $start_date = Kolab::decodeDateOrDateTime($this->_kolab->getVal('start-date'));
            if (($completed == 0 && ($complete || $start_date > time())) ||
                ($completed == 2 && !$complete) ||
                ($completed == 3 &&
                 ($complete || $start_date == 0 || $start_date < time())) ||
                ($completed == 4 && $complete)) {
                continue;
            }
            $tasks[$this->_kolab->getUID()] = new Nag_Task($this->_buildTask());
        }

        return $tasks;
    }

    /**
     * Lists all alarms near $date.
     *
     * @param integer $date  The unix epoch time to check for alarms.
     *
     * @return array  An array of tasks that have alarms that match.
     */
    function listAlarms($date)
    {
        $tasks = array();

        $msg_list = $this->_kolab->listObjects();
        if (is_a($msg_list, 'PEAR_Error')) {
            return $msg_list;
        }

        if (empty($msg_list)) {
            return $tasks;
        }

        foreach ($msg_list as $msg) {
            $result = &$this->_kolab->loadObject($msg, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $task = new Nag_Task($this->_buildTask());

            if ($task['alarm'] > 0 && $task['due'] >= time() && $task['due'] - ($task['alarm'] * 60) <= $date) {
                $tasks[$this->_kolab->getUID()] = $task;
            }
        }

        return $tasks;
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
        $tasks = array();

        $msg_list = $this->_kolab->listObjects();
        if (is_a($msg_list, 'PEAR_Error')) {
            return $msg_list;
        }

        if (empty($msg_list)) {
            return $tasks;
        }

        foreach ($msg_list as $msg) {
            $result = &$this->_kolab->loadObject($msg, true);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            if ($this->_kolab->getVal('parent') != $parentId) {
                continue;
            }
            $task = &new Nag_Task($this->_buildTask());
            $children = $this->getChildren($task->id);
            if (is_a($children, 'PEAR_Error')) {
                return $children;
            }
            $task->mergeChildren($children);
            $tasks[] = $task;
        }

        return $tasks;
    }
}


/**
 * New Nag driver for the Kolab IMAP server.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Nag
 */
class Nag_Driver_kolab_wrapper_new extends Nag_Driver_kolab_wrapper {

    /**
     * Shortcut to the imap connection
     *
     * @var Kolab_IMAP
     */
    var $_store = null;

    /**
     * Connect to the Kolab backend
     *
     * @return mixed True on success, a PEAR error otherwise
     */
    function connect()
    {
        if ($this->_connected) {
            return true;
        }

        $result = parent::connect(1);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_store = &$this->_kolab->_storage;

        return true;
    }

    /**
     * Split the tasklist name of the id. We use this to make ids
     * unique across folders.
     *
     * @param string $id The ID of the task appended with the tasklist
     *                   name.
     *
     * @return array  The task id and tasklist name
     */
    function _splitId($id)
    {
        $split = split('@', $id, 2);
        if (count($split) == 2) {
            list($id, $tasklist) = $split;
        } else if (count($split) == 1) {
            $tasklist = Auth::getAuth();
        }
        return array($id, $tasklist);
    }

    /**
     * Append the tasklist name to the id. We use this to make ids
     * unique across folders.
     *
     * @param string $id The ID of the task
     *
     * @return string  The task id appended with the tasklist
     *                 name.
     */
    function _uniqueId($id)
    {
        if ($this->_tasklist == Auth::getAuth()) {
            return $id;
        }
        return $id . '@' . $this->_tasklist;
    }

    /**
     * Retrieves one task from the store.
     *
     * @param string $taskId  The id of the task to retrieve.
     *
     * @return Nag_Task  A Nag_Task object.
     */
    function get($taskId)
    {
        list($taskId, $tasklist) = $this->_splitId($taskId);

        if ($this->_store->objectUidExists($taskId)) {
            $task = $this->_store->getObject($taskId);
            return new Nag_Task($this->_buildTask($task));
        } else {
            return PEAR::raiseError(sprintf(_('Nag/kolab: Did not find task %s'), $taskId));
        }
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
        list($taskId, $tasklist) = $this->_splitId($uid);

        if ($this->_tasklist != $tasklist) {
            $this->_tasklist = $tasklist;
            $this->_connected = false;
            $this->connect();
        }

        return $this->get($taskId);
    }

    /**
     * Add or modify a task.
     *
     * @param string $name             The name (short) of the task.
     * @param string $desc             The description (long) of the task.
     * @param integer $start           The start date of the task.
     * @param integer $due             The due date of the task.
     * @param integer $priority        The priority of the task.
     * @param float $estimate          The estimated time to complete the task.
     * @param integer $completed       The completion state of the task.
     * @param string $category         The category of the task.
     * @param integer $alarm           The alarm associated with the task.
     * @param string $uid              A Unique Identifier for the task.
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     *
     * @return mixed The id of the task if successful, a PEAR error
     * otherwise
     */
    function _setObject($name, $desc, $start = 0, $due = 0, $priority = 0,
                        $estimate = 0.0, $completed = 0, $category = '',
                        $alarm = 0, $uid = null, $parent = null,
                        $private = false, $owner = null, $assignee = null,
                        $completed_date = null)
    {
        if (empty($uid)) {
            $task_uid = $this->_store->generateUID();
            $old_uid = null;
        } else {
            list($task_uid, $tasklist) = $this->_splitId($uid);
            $old_uid = $task_uid;
        }

        if ($parent) {
            list($parent,) = $this->_splitId($parent);
        }

        if ($private) {
            $sensitivity = 'private';
        } else {
            $sensitivity = 'public';
        }

        $result = $this->_store->save(array(
                                          'uid' => $task_uid,
                                          'name' => $name,
                                          'body' => $desc,
                                          'start' => $start,
                                          'due' => $due,
                                          'priority' => $priority,
                                          'completed' => $completed,
                                          'categories' => $category,
                                          'alarm' => $alarm,
                                          'parent' => $parent,
                                          'sensitivity' => $sensitivity,
                                          'estimate' => $estimate,
                                          'completed_date' => $completed_date,
                                          'creator' => array(
                                              'smtp-address' => $owner,
                                          ),
                                          'organizer' => array(
                                              'smtp-address' => $assignee,
                                          ),
                                      ),
                                      $old_uid);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $task_uid;
    }

    /**
     * Adds a task to the backend storage.
     *
     * @param string $name             The name (short) of the task.
     * @param string $desc             The description (long) of the task.
     * @param integer $start           The start date of the task.
     * @param integer $due             The due date of the task.
     * @param integer $priority        The priority of the task.
     * @param float $estimate          The estimated time to complete the task.
     * @param integer $completed       The completion state of the task.
     * @param string $category         The category of the task.
     * @param integer $alarm           The alarm associated with the task.
     * @param string $uid              A Unique Identifier for the task.
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     *
     * @return mixed The id of the task if successful, a PEAR error
     * otherwise
     */
    function add($name, $desc, $start = 0, $due = 0, $priority = 0,
                 $estimate = 0.0, $completed = 0, $category = '', $alarm = 0,
                 $uid = null, $parent = null, $private = false, $owner = null,
                 $assignee = null)
    {
        return $this->_setObject($name, $desc, $start, $due, $priority,
                                 $estimate, $completed, $category, $alarm,
                                 null, $parent, $private, $owner, $assignee);
    }

    /**
     * Modifies an existing task.
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
     * @param string $parent           The parent task id.
     * @param boolean $private         Whether the task is private.
     * @param string $owner            The owner of the event.
     * @param string $assignee         The assignee of the event.
     * @param integer $completed_date  The task's completion date.
     *
     * @return mixed The id of the task if successful, a PEAR error
     * otherwise
     */
    function modify($taskId, $name, $desc, $start = 0, $due = 0, $priority = 0,
                    $estimate = 0.0, $completed = 0, $category = '',
                    $alarm = 0, $parent = null, $private = false,
                    $owner = null, $assignee = null, $completed_date = null)
    {
        $result = $this->_setObject($name, $desc, $start, $due, $priority,
                                    $estimate, $completed, $category, $alarm,
                                    $taskId, $parent, $private, $owner, $assignee,
                                    $completed_date);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $result == $taskId;
    }

    /**
     * Moves a task to a different tasklist.
     *
     * @param string $taskId       The task to move.
     * @param string $newTasklist  The new tasklist.
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function move($taskId, $newTasklist)
    {
        list($taskId, $tasklist) = $this->_splitId($taskId);

        return $this->_store->move($taskId, $newTasklist);
    }

    /**
     * Deletes a task from the backend.
     *
     * @param string $taskId  The task to delete.
     */
    function delete($taskId)
    {
        list($taskId, $tasklist) = $this->_splitId($taskId);

        return $this->_store->delete($taskId);
    }

    /**
     * Deletes all tasks from the backend.
     */
    function deleteAll()
    {
        return $this->_store->deleteAll();
    }

    /**
     * Retrieves tasks from the Kolab server.
     *
     * @param integer $completed  Which tasks to retrieve (1 = all tasks,
     *                            0 = incomplete tasks, 2 = complete tasks,
     *                            3 = future tasks, 4 = future and incomplete
     *                            tasks).
     *
     * @return mixed  True on success, PEAR_Error on failure.
     */
    function retrieve($completed = 1)
    {
        $dict = array();
        $tasks = new Nag_Task();

        $task_list = $this->_store->getObjects();
        if (is_a($task_list, 'PEAR_Error')) {
            return $task_list;
        }

        if (empty($task_list)) {
            return $tasks;
        }

        foreach ($task_list as $task) {
            $tuid = $this->_uniqueId($task['uid']);
            $t = &new Nag_Task($this->_buildTask($task));
            $complete = $t->completed;
            if (empty($t->start)) {
                $start = null;
            } else {
                $start = $t->start;
            }

            if (($completed == 0 && ($complete || $start > time())) ||
                ($completed == 2 && !$complete) ||
                ($completed == 3 &&
                 ($complete || $start == 0 || $start < time())) ||
                ($completed == 4 && $complete)) {
                continue;
            }
            if (empty($t->parent_id)) {
                $tasks->add($t);
            } else {
                $dict[$tuid] = &$t;
            }
        }

        /* Build a tree from the subtasks. */
        foreach (array_keys($dict) as $key) {
            $task = &$tasks->get($dict[$key]->parent_id);
            if ($task) {
                $task->add($dict[$key]);
            } elseif (isset($dict[$dict[$key]->parent_id])) {
                $dict[$dict[$key]->parent_id]->add($dict[$key]);
            } else {
                $tasks->add($dict[$key]);
            }
        }

        return $tasks;
    }

    /**
     * Build a task based a data array
     *
     * @param array  $task     The data for the task
     *
     * @return array  The converted data array representing the task
     */
    function _buildTask($task)
    {
        $task['tasklist_id'] = $this->_tasklist;
        $task['task_id'] = $this->_uniqueId($task['uid']);

        if (!empty($task['parent'])) {
            $task['parent'] = $this->_uniqueId($task['parent']);
        }

        $task['category'] = $task['categories'];
        unset($task['categories']);

        $task['desc'] = $task['body'];
        unset($task['body']);

        if ($task['sensitivity'] == 'public') {
            $task['private'] = false;
        } else {
            $task['private'] = true;
        }
        unset($task['sensitivity']);

        $share = &$GLOBALS['nag_shares']->getShare($this->_tasklist);
        $task['owner'] = $share->get('owner');

        return $task;
    }

    /**
     * Lists all alarms near $date.
     *
     * @param integer $date  The unix epoch time to check for alarms.
     *
     * @return array  An array of tasks that have alarms that match.
     */
    function listAlarms($date)
    {
        $task_list = $this->_store->getObjects();
        if (is_a($task_list, 'PEAR_Error')) {
            return $task_list;
        }

        if (empty($task_list)) {
            return array();
        }

        $tasks = array();
        foreach ($task_list as $task) {
            $tuid = $this->_uniqueId($task['uid']);
            $t = new Nag_Task($this->_buildTask($task));
            if ($t->alarm && $t->due &&
                $t->due - $t->alarm * 60 < $date) {
                $tasks[] = $t;
            }
        }

        return $tasks;
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
        list($parentId, $tasklist) = $this->_splitId($parentId);

        $task_list = $this->_store->getObjects();
        if (is_a($task_list, 'PEAR_Error')) {
            return $task_list;
        }

        if (empty($task_list)) {
            return array();
        }

        $tasks = array();

        foreach ($task_list as $task) {
            if ($task['parent'] != $parentId) {
                continue;
            }
            $t = &new Nag_Task($this->_buildTask($task));
            $children = $this->getChildren($t->id);
            if (is_a($children, 'PEAR_Error')) {
                return $children;
            }
            $t->mergeChildren($children);
            $tasks[] = $t;
        }

        return $tasks;
    }
}
