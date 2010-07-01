<?php
/**
 * Nag external API interface.
 *
 * $Horde: nag/lib/api.php,v 1.100.10.46 2009-09-04 10:38:38 jan Exp $
 *
 * This file defines Nag's external API interface. Other applications can
 * interact with Nag through this API.
 *
 * @package Nag
 */

$_services['perms'] = array(
    'args' => array(),
    'type' => '{urn:horde}hashHash'
);

$_services['removeUserData'] = array(
    'args' => array('user' => 'string'),
    'type' => 'boolean'
);

$_services['show'] = array(
    'link' => '%application%/view.php?tasklist=|tasklist|&task=|task|&uid=|uid|',
);

$_services['browse'] = array(
    'args' => array('path' => 'string'),
    'type' => '{urn:horde}hashHash',
);

$_services['put'] = array(
    'args' => array('path' => 'string', 'content' => 'string', 'content_type' => 'string'),
    'type' => 'int',
);

$_services['path_delete'] = array(
    'args' => array('path' => 'string'),
    'type' => 'boolean',
);

$_services['addTasklist'] = array(
    'args' => array('name' => 'string', 'description' => 'string'),
    'type' => 'string',
);

$_services['listTasklists'] = array(
    'args' => array('owneronly' => 'boolean', 'permission' => 'int'),
    'type' => '{urn:horde}stringArray',
);

$_services['listTasks'] = array(
    'args' => array('sortby' => 'string', 'sortdir' => 'int'),
    'type' => '{urn:horde}stringArray',
);

$_services['listAlarms'] = array(
    'args' => array('time' => 'int', 'user' => 'string'),
    'type' => '{urn:horde}hashHash'
);

$_services['list'] = array(
    'args' => array(),
    'type' => '{urn:horde}stringArray',
);

$_services['listBy'] = array(
    'args' => array('action' => 'string', 'timestamp' => 'int', 'tasklist' => 'string'),
    'type' => '{urn:horde}stringArray',
);

$_services['getActionTimestamp'] = array(
    'args' => array('uid' => 'string', 'action' => 'string', 'tasklist' => 'string'),
    'type' => 'int',
);

$_services['import'] = array(
    'args' => array('content' => 'string', 'contentType' => 'string', 'tasklist' => 'string'),
    'type' => 'string',
);

$_services['export'] = array(
    'args' => array('uid' => 'string', 'contentType' => '{urn:horde}stringArray'),
    'type' => 'string',
);

$_services['exportTasklist'] = array(
    'args' => array('tasklist' => 'string', 'contentType' => 'string'),
    'type' => 'string'
);

$_services['delete'] = array(
    'args' => array('uid' => '{urn:horde}stringArray'),
    'type' => 'boolean',
);

$_services['replace'] = array(
    'args' => array('uid' => 'string', 'content' => 'string', 'contentType' => 'string'),
    'type' => 'boolean',
);

$_services['listCostObjects'] = array(
    'args' => array('criteria' => '{urn:horde}hash'),
    'type' => '{urn:horde}stringArray'
);

$_services['listTimeObjectCategories'] = array(
    'type' => '{urn:horde}stringArray'
);

$_services['listTimeObjects'] = array(
    'args' => array('start' => 'int', 'end' => 'int'),
    'type' => '{urn:horde}hashHash'
);

$_services['synchronize'] = array(
    'args' => array(),
    'type' => 'boolean'
);

/**
 * Returns a list of available permissions.
 *
 * @return array  An array describing all available permissions.
 */
function _nag_perms()
{
    $perms = array();
    $perms['tree']['nag']['max_tasks'] = false;
    $perms['title']['nag:max_tasks'] = _("Maximum Number of Tasks");
    $perms['type']['nag:max_tasks'] = 'int';

    return $perms;
}

/**
 * Removes user data.
 *
 * @param string $user  Name of user to remove data for.
 *
 * @return mixed  true on success | PEAR_Error on failure
 */
function _nag_removeUserData($user)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!Auth::isAdmin() && $user != Auth::getAuth()) {
        return PEAR::raiseError(_("You are not allowed to remove user data."));
    }

    /* Error flag */
    $hasError = false;

    /* Get the share for later deletion */
    $share = $GLOBALS['nag_shares']->getShare($user);
    if(is_a($share, 'PEAR_Error')) {
        Horde::logMessage($share->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        unset($share);
    } else {
        /* Get the list of all tasks */
        $tasks = Nag::listTasks(null, null, null, $user, 1);
        if (is_a($tasks, 'PEAR_Error')) {
            $hasError = true;
            Horde::logMessage($share->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            $uids = array();
            $tasks->reset();
            while ($task = $tasks->each()) {
                $uids[] = $task->uid;
            }

            /* ... and delete them. */
            foreach ($uids as $uid) {
                _nag_delete($uid);
            }
        }
    }

    /* Now delete history as well. */
    $history = &Horde_History::singleton();
    if (method_exists($history, 'removeByParent')) {
        $histories = $history->removeByParent('nag:' . $user);
    } else {
        /* Remove entries 100 at a time. */
        $all = $history->getByTimestamp('>', 0, array(), 'nag:' . $user);
        if (is_a($all, 'PEAR_Error')) {
            Horde::logMessage($all, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            $all = array_keys($all);
            while (count($d = array_splice($all, 0, 100)) > 0) {
                $history->removebyNames($d);
            }
        }
    }

    /* ...and finally, delete the actual share */
    if (!empty($share)) {
        $result = $GLOBALS['nag_shares']->removeShare($share);
        if (is_a($result, 'PEAR_Error')) {
            $hasError = true;
            Horde::logMessage($result->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
        }
    }

    /* Now remove perms for this user from all other shares */
    $shares = $GLOBALS['nag_shares']->listShares($user);
    if (is_a($shares, 'PEAR_Error')) {
        $hasError = true;
        Horde::logMessage($shares, __FILE__, __LINE__, PEAR_LOG_ERR);
    }
    foreach ($shares as $share) {
        $share->removeUser($user);
    }

    if ($hasError) {
        return PEAR::raiseError(sprintf(_("There was an error removing tasks for %s. Details have been logged."), $user));
    } else {
        return true;
    }
}

/**
 * Retrieves the current user's task list from storage.
 *
 * This function will also sort the resulting list, if requested.
 *
 * @param string $sortby      The field by which to sort
 *                            (NAG_SORT_PRIORITY, NAG_SORT_NAME
 *                            NAG_SORT_DUE, NAG_SORT_COMPLETION).
 * @param integer $sortdir    The direction by which to sort
 *
 * @return Nag_Task  A list of the requested tasks.
 */
function _nag_listTasks($sortby = null, $sortdir = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!isset($sortby)) {
        $sortby = $GLOBALS['prefs']->getValue('sortby');
    }
    if (!isset($sortdir)) {
        $sortdir = $GLOBALS['prefs']->getValue('sortdir');
    }

    $tasks = Nag::listTasks($sortby, $sortdir);
    $tasks->reset();
    $list = array();
    while ($task = $tasks->each()) {
        $list[$task->id] = $task->toHash();
    }

    return $list;
}

/**
 * Add a new task list
 *
 * @param string $name        Task list name
 * @param string $description Task list description
 *
 * @return integer  The new tasklist's id.
 */
function _nag_addTasklist($name, $description = '')
{
    if (!Auth::getAuth()) {
        return PEAR::raiseError(_("Permission denied"));
    }

    require_once dirname(__FILE__) . '/base.php';
    global $nag_shares;

    $tasklistId = md5(microtime());
    $tasklist = $nag_shares->newShare($tasklistId);

    if (is_a($tasklist, 'PEAR_Error')) {
        return $tasklist;
    }

    $tasklist->set('name', $name, false);
    $tasklist->set('desc', $description, false);
    $result = $nag_shares->addShare($tasklist);

    if (is_a($result, 'PEAR_Error')) {
        return $result;
    }

    return $tasklistId;
}

/**
 * Returns the last modification timestamp of a given uid.
 *
 * @param string $uid      The uid to look for.
 * @param string $tasklist The tasklist to look in.
 *
 * @return integer  The timestamp for the last modification of $uid.
 */
function __nag_modified($uid, $tasklist = null)
{
    $modified = _nag_getActionTimestamp($uid, 'modify', $tasklist);
    if (empty($modified)) {
        $modified = _nag_getActionTimestamp($uid, 'add', $tasklist);
    }
    return $modified;
}

/**
 * Browse through Nag's object tree.
 *
 * @param string $path       The level of the tree to browse.
 * @param array $properties  The item properties to return. Defaults to 'name',
 *                           'icon', and 'browseable'.
 *
 * @return array  The contents of $path
 */
function _nag_browse($path = '', $properties = array())
{
    require_once dirname(__FILE__) . '/base.php';
    global $registry;

    function _getTasklistSize($tasklistID)
    {
        // This ugly and performance-heavy hack is required to set the content
        // length.  Some clients (at least OS X) respect the content-length
        // header a little too exactly.  If we send a content-length that is
        // longer than the actual data it will complain that the connection
        // broke.  If we specify one that is too short it will truncate the
        // downlaoded file.  To make matters worse it seems to respect the
        // content-length from the PROPFIND request used to enumerate objects
        // rather than the actual content-length sent at the time the file is
        // downloaded.  Way to go, Apple.
        return strlen(_nag_exportTasklist($tasklistID, 'text/calendar'));
    }

    // Default properties.
    if (!$properties) {
        $properties = array('name', 'icon', 'browseable');
    }

    if (substr($path, 0, 3) == 'nag') {
        $path = substr($path, 3);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (empty($path)) {
        //
        // This request is for a list of all users who have tasklists visible
        // to the requesting user.
        //
        $tasklists = Nag::listTasklists(false, PERMS_READ);
        $owners = array();
        foreach ($tasklists as $tasklist) {
            $owners[$tasklist->get('owner')] = true;
        }

        $results = array();
        foreach (array_keys($owners) as $owner) {
            if (in_array('name', $properties)) {
                $results['nag/' . $owner]['name'] = $owner;
            }
            if (in_array('icon', $properties)) {
                $results['nag/' . $owner]['icon'] =
                    $registry->getImageDir('horde') . '/user.png';
            }
            if (in_array('browseable', $properties)) {
                $results['nag/' . $owner]['browseable'] = true;
            }
            if (in_array('contenttype', $properties)) {
                $results['nag/' . $owner]['contenttype'] =
                    'httpd/unix-directory';
            }
            if (in_array('contentlength', $properties)) {
                $results['nag/' . $owner]['contentlength'] = 0;
            }
            if (in_array('modified', $properties)) {
                $results['nag/' . $owner]['modified'] =
                    $_SERVER['REQUEST_TIME'];
            }
            if (in_array('created', $properties)) {
                $results['nag/' . $owner]['created'] = 0;
            }
        }
        return $results;

    } elseif (count($parts) == 1) {
        //
        // This request is for all tasklists owned by the requested user
        //
        $tasklists = $GLOBALS['nag_shares']->listShares($parts[0],
                                                        PERMS_SHOW,
                                                        $parts[0]);

        // The last check returns all addressbooks for the requested user,
        // but that does not mean the requesting user has access to them.
        // Filter out those address books for which the requesting user has
        // no access.
        $tasklists = Nag::permissionsFilter($tasklists);

        $results = array();
        foreach ($tasklists as $tasklistId => $tasklist) {
            $retpath = 'nag/' . $parts[0] . '/' . $tasklistId;
            if (in_array('name', $properties)) {
                $results[$retpath]['name'] = sprintf(_("Tasks from %s"), $tasklist->get('name'));
                $results[$retpath . '.ics']['name'] = $tasklist->get('name');
            }
            if (in_array('icon', $properties)) {
                $results[$retpath]['icon'] = $registry->getImageDir() . '/nag.png';
                $results[$retpath . '.ics']['icon'] = $registry->getImageDir() . '/mime/icalendar.png';
            }
            if (in_array('browseable', $properties)) {
                $results[$retpath]['browseable'] = $tasklist->hasPermission(Auth::getAuth(), PERMS_READ);
                $results[$retpath . '.ics']['browseable'] = false;
            }
            if (in_array('contenttype', $properties)) {
                $results[$retpath]['contenttype'] = 'httpd/unix-directory';
                $results[$retpath . '.ics']['contenttype'] = 'text/calendar';
            }
            if (in_array('contentlength', $properties)) {
                $results[$retpath]['contentlength'] = 0;
                $results[$retpath . '.ics']['contentlength'] = _getTasklistSize($tasklistId);
            }
            if (in_array('modified', $properties)) {
                // @TODO Find a way to get the actual modification times
                $results[$retpath]['modified'] = $_SERVER['REQUEST_TIME'];
                $results[$retpath . '.ics']['modified'] = $_SERVER['REQUEST_TIME'];
            }
            if (in_array('created', $properties)) {
                // @TODO Find a way to get the actual creation times
                $results[$retpath]['created'] = 0;
                $results[$retpath . '.ics']['created'] = 0;
            }
        }
        return $results;

    } elseif (count($parts) == 2 && substr($parts[1], -4) == '.ics') {
        //
        // This is a request for the entire tasklist in iCalendar format.
        //
        $tasklist = substr($parts[1], 0, -4);
        if (!array_key_exists($tasklist, Nag::listTasklists(false, PERMS_READ))) {
            return PEAR::raiseError(_("Invalid tasklist file requested."), 404);
        }
        $ical_data = _nag_exportTasklist($tasklist, 'text/calendar');
        $result = array('data'          => $ical_data,
                        'mimetype'      => 'text/calendar',
                        'contentlength' => strlen($ical_data),
                        'mtime'         => $_SERVER['REQUEST_TIME']);

        return $result;

    } elseif (count($parts) == 2) {
        //
        // This request is browsing into a specific tasklist.  Generate the list
        // of items and represent them as files within the directory.
        //
        if (!array_key_exists($parts[1], Nag::listTasklists(false, PERMS_READ))) {
            return PEAR::raiseError(_("Invalid tasklist requested."), 404);
        }
        $storage = &Nag_Driver::singleton($parts[1]);
        $result = $storage->retrieve();
        if (is_a($result, 'PEAR_Error')) {
            $result->code = 500;
            return $result;
        }

        $icon = $registry->getImageDir() . '/nag.png';
        $results = array();
        $storage->tasks->reset();
        while ($task = $storage->tasks->each()) {
            $key = 'nag/' . $parts[0] . '/' . $parts[1] . '/' . $task->id;
            if (in_array('name', $properties)) {
                $results[$key]['name'] = $task->name;
            }
            if (in_array('icon', $properties)) {
                $results[$key]['icon'] = $icon;
            }
            if (in_array('browseable', $properties)) {
                $results[$key]['browseable'] = false;
            }
            if (in_array('contenttype', $properties)) {
                $results[$key]['contenttype'] = 'text/calendar';
            }
            if (in_array('contentlength', $properties)) {
                // FIXME:  This is a hack.  If the content length is longer
                // than the actual data then some WebDAV clients will report
                // an error when the file EOF is received.  Ideally we should
                // determine the actual size of the data and report it here, but
                // the performance hit may be prohibitive.  This requires
                // further investigation.
                $results[$key]['contentlength'] = 1;
            }
            if (in_array('modified', $properties)) {
                $results[$key]['modified'] = __nag_modified($task->uid, $path);
            }
            if (in_array('created', $properties)) {
                $results[$key]['created'] = _nag_getActionTimestamp($task->uid, 'add', $path);
            }
        }
        return $results;
    } else {
        //
        // The only valid request left is for either a specific task item.
        //
        if (count($parts) == 3 &&
            array_key_exists($parts[1], Nag::listTasklists(false,
                             PERMS_READ))) {
            //
            // This request is for a specific item within a given task list.
            //
            /* Create a Nag storage instance. */
            $storage = &Nag_Driver::singleton($parts[1]);
            if (is_a($storage, 'PEAR_Error')) {
                return PEAR::raiseError(sprintf(_("Connection failed: %s"), $storage->getMessage()));
            }
            $storage->retrieve();

            $task = $storage->get($parts[2]);
            if (is_a($task, 'PEAR_Error')) {
                $task->code = 500;
                return $task;
            }

            $result = array('data' => _nag_export($task->uid, 'text/calendar'),
                            'mimetype' => 'text/calendar');
            $modified = __nag_modified($task->uid, $parts[1]);
            if (!empty($modified)) {
                $result['mtime'] = $modified;
            }
            return $result;
        } elseif (count($parts) == 2 &&
                  substr($parts[1], -4) == '.ics' &&
                  array_key_exists(substr($parts[1], 0, -4), Nag::listTasklists(false, PERMS_READ))) {
        } else {
            //
            // All other requests are a 404: Not Found
            //
            return false;
        }
    }
}

/**
 * Saves a file into the Nag tree.
 *
 * @param string $path          The path where to PUT the file.
 * @param string $content       The file content.
 * @param string $content_type  The file's content type.
 *
 * @return array  The event UIDs, or a PEAR_Error on failure.
 */
function _nag_put($path, $content, $content_type)
{
    require_once dirname(__FILE__) . '/base.php';

    if (substr($path, 0, 3) == 'nag') {
        $path = substr($path, 3);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (count($parts) == 2 &&
        substr($parts[1], -4) == '.ics') {

        // Workaround for WebDAV clients that are not smart enough to send
        // the right content type.  Assume text/calendar.
        if ($content_type == 'application/octet-stream') {
            $content_type = 'text/calendar';
        }
        $tasklist = substr($parts[1], 0, -4);
    } elseif (count($parts) == 3) {
        $tasklist = $parts[1];

        // Workaround for WebDAV clients that are not smart enough to send
        // the right content type.  Assume the same format we send individual
        // tasklist items: text/calendar
        if ($content_type == 'application/octet-stream') {
            $content_type = 'text/calendar';
        }
    } else {
        return PEAR::raiseError(_("Invalid tasklist name supplied."), 403);
    }

    if (!array_key_exists($tasklist, Nag::listTasklists(false, PERMS_EDIT))) {
        // FIXME: Should we attempt to create a tasklist based on the filename
        // in the case that the requested tasklist does not exist?
        return PEAR::raiseError(_("Tasklist does not exist or no permission to edit"), 403);
    }

    // Store all currently existings UIDs. Use this info to delete UIDs not
    // present in $content after processing.
    $ids = array();
    $uids_remove = array_flip(_nag_list($tasklist));

    $storage = &Nag_Driver::singleton($tasklist);

    switch ($content_type) {
    case 'text/calendar':
    case 'text/x-vcalendar':
        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar();
        if (!is_a($content, 'Horde_iCalendar_vtodo')) {
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."), 400);
            }
        } else {
            $iCal->addComponent($content);
        }

        foreach ($iCal->getComponents() as $content) {
            if (is_a($content, 'Horde_iCalendar_vtodo')) {
                $task = new Nag_Task();
                $task->fromiCalendar($content);
                $task->tasklist = $tasklist;
                if (isset($task->uid) &&
                    !is_a(($existing = $storage->getByUID($task->uid)), 'PEAR_Error')) {
                    // Entry exists, remove from uids_remove list so we won't
                    // delete in the end.
                    if (isset($uids_remove[$task->uid])) {
                        unset($uids_remove[$task->uid]);
                    }
                    if ($existing->private &&
                        $existing->owner != Auth::getAuth()) {
                        continue;
                    }
                    // Check if our task is newer then the existing - get the
                    // task's history.
                    $history = &Horde_History::singleton();
                    $created = $modified = null;
                    $log = $history->getHistory('nag:' . $tasklist . ':' . $task->uid);
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
                    if (empty($modified) && !empty($add)) {
                        $modified = $add;
                    }
                    if (!empty($modified) &&
                        $modified >= $content->getAttribute('LAST-MODIFIED')) {
                        // LAST-MODIFIED timestamp of existing entry is newer:
                        // don't replace it.
                        continue;
                    }

                    // Don't change creator/owner.
                    $owner = $existing->owner;
                    $taskId = $existing->id;
                    $result = $storage->modify(
                        $taskId,
                        isset($task->name) ? $task->name : $existing->name,
                        isset($task->desc) ? $task->desc : $existing->desc,
                        isset($task->start) ? $task->start : $existing->start,
                        isset($task->due) ? $task->due : $existing->due,
                        isset($task->priority) ? $task->priority : $existing->priority,
                        isset($task->estimate) ? $task->estimate : 0,
                        isset($task->completed) ? (int)$task->completed : $existing->completed,
                        isset($task->category) ? $task->category : $existing->category,
                        isset($task->alarm) ? $task->alarm : $existing->alarm,
                        isset($task->parent_id) ? $task->parent_id : $existing->parent_id,
                        isset($task->private) ? $task->private : $existing->private,
                        $owner,
                        isset($task->assignee) ? $task->assignee : $existing->assignee);

                    if (is_a($result, 'PEAR_Error')) {
                        $result->code = 500;
                        return $result;
                    }
                    $ids[] = $task->uid;
                } else {
                    $newTask = $storage->add(
                        isset($task->name) ? $task->name : '',
                        isset($task->desc) ? $task->desc : '',
                        isset($task->start) ? $task->start : 0,
                        isset($task->due) ? $task->due : 0,
                        isset($task->priority) ? $task->priority : 3,
                        isset($task->estimate) ? $task->estimate : 0,
                        !empty($task->completed),
                        isset($task->category) ? $task->category : '',
                        isset($task->alarm) ? $task->alarm : 0,
                        isset($task->uid) ? $task->uid : null,
                        isset($task->parent_id) ? $task->parent_id : '',
                        !empty($task->private),
                        Auth::getAuth(),
                        isset($task->assignee) ? $task->assignee : null);
                    if (is_a($newTask, 'PEAR_Error')) {
                        $newtask->code = 500;
                        return $newTask;
                    }
                    // use UID rather than ID
                    $ids[] = $newTask[1];
                }
            }
        }
        break;

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $content_type), 400);
    }

    if (array_key_exists($tasklist, Nag::listTasklists(false, PERMS_DELETE))) {
        foreach (array_keys($uids_remove) as $uid) {
            _nag_delete($uid);
        }
    }

    return $ids;
}

/**
 * Deletes a file from the Nag tree.
 *
 * @param string $path  The path to the file.
 *
 * @return mixed  The event's UID, or a PEAR_Error on failure.
 */
function _nag_path_delete($path)
{
    require_once dirname(__FILE__) . '/base.php';

    if (substr($path, 0, 3) == 'nag') {
        $path = substr($path, 3);
    }
    $path = trim($path, '/');
    $parts = explode('/', $path);

    if (count($parts) == 2) {
        // @TODO Deny deleting of the entire tasklist for now.
        // Allow users to delete tasklists but not create them via WebDAV will
        // be more confusing than helpful.  They are, however, still able to
        // delete individual task items within the tasklist folder.
        return PEAR::raiseError(_("Deleting entire tasklists is not supported."), 403);
        // To re-enable the functionality just remove this if {} block.
    }

    if (substr($parts[1], -4) == '.ics') {
        $tasklistID = substr($parts[1], 0, -4);
    } else {
        $tasklistID = $parts[1];
    }

    if (!(count($parts) == 2 || count($parts) == 3) ||
        !array_key_exists($tasklistID, Nag::listTasklists(false, PERMS_DELETE))) {
        return PEAR::raiseError(_("Tasklist does not exist or no permission to delete"), 403);
    }

    /* Create a Nag storage instance. */
    $storage = &Nag_Driver::singleton($tasklistID);
    if (is_a($storage, 'PEAR_Error')) {
        return PEAR::raiseError(sprintf(_("Connection failed: %s"), $storage->getMessage()), 500);
    }
    $retrieved = $storage->retrieve();
    if (is_a($retrieved, 'PEAR_Error')) {
        $retrieved->code = 500;
        return $retrieved;
    }

    if (count($parts) == 3) {
        // Delete just a single entry
        return $storage->delete($parts[2]);
    } else {
        // Delete the entire task list
        $result = $storage->deleteAll();
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Unable to delete tasklist \"%s\": %s"), $tasklistID, $result->getMessage()), 500);
        } else {
            // Remove share and all groups/permissions.
            $share = $GLOBALS['nag_shares']->getShare($tasklistID);
            $result = $GLOBALS['nag_shares']->removeShare($share);
            if (is_a($result, 'PEAR_Error')) {
                $result->code = 500;
                return $result;
            }
        }
    }
}

/**
 * @param boolean $owneronly   Only return tasklists that this user owns?
 *                             Defaults to false.
 * @param integer $permission  The permission to filter tasklists by.
 *
 * @return array  The task lists.
 */
function _nag_listTasklists($owneronly, $permission)
{
    require_once dirname(__FILE__) . '/base.php';

    return Nag::listTasklists($owneronly, $permission);
}

/**
 * Returns an array of UIDs for all tasks that the current user is authorized
 * to see.
 *
 * @param variant $tasklist  The tasklist or an array of taskslists to list.
 *
 * @return array             An array of UIDs for all tasks
 *                           the user can access.
 */
function _nag_list($tasklist = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!isset($GLOBALS['conf']['storage']['driver'])) {
        return PEAR::raiseError(_("Not configured"));
    }

    if ($tasklist === null) {
        $tasklist = Nag::getDefaultTasklist(PERMS_READ);
    }

    if (!array_key_exists($tasklist,
                          Nag::listTasklists(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $tasks = Nag::listTasks(null, null, null, $tasklist, 1);
    if (is_a($tasks, 'PEAR_Error')) {
        return $tasks;
    }

    $uids = array();
    $tasks->reset();
    while ($task = $tasks->each()) {
        $uids[] = $task->uid;
    }

    return $uids;
}

/**
 * Returns an array of UIDs for tasks that have had $action happen since
 * $timestamp.
 *
 * @param string  $action     The action to check for - add, modify, or delete.
 * @param integer $timestamp  The time to start the search.
 * @param string  $tasklist   The tasklist to be used. If 'null', the
 *                            user's default tasklist will be used.
 *
 * @return array  An array of UIDs matching the action and time criteria.
 */
function _nag_listBy($action, $timestamp, $tasklist = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if ($tasklist === null) {
        $tasklist = Nag::getDefaultTasklist(PERMS_READ);
    }

    if (!array_key_exists($tasklist,
                          Nag::listTasklists(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $history = &Horde_History::singleton();
    $histories = $history->getByTimestamp('>', $timestamp, array(array('op' => '=', 'field' => 'action', 'value' => $action)), 'nag:' . $tasklist);
    if (is_a($histories, 'PEAR_Error')) {
        return $histories;
    }

    // Strip leading nag:username:.
    return preg_replace('/^([^:]*:){2}/', '', array_keys($histories));
}

/**
 * Returns the timestamp of an operation for a given uid an action.
 *
 * @param string $uid      The uid to look for.
 * @param string $action   The action to check for - add, modify, or delete.
 * @param string $tasklist The tasklist to be used. If 'null', the
 *                         user's default tasklist will be used.
 *
 * @return integer  The timestamp for this action.
 */
function _nag_getActionTimestamp($uid, $action, $tasklist = null)
{
    require_once dirname(__FILE__) . '/base.php';

    if ($tasklist === null) {
        $tasklist = Nag::getDefaultTasklist(PERMS_READ);
    }

    if (!array_key_exists($tasklist,
                          Nag::listTasklists(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $history = &Horde_History::singleton();
    return $history->getActionTimestamp('nag:' . $tasklist . ':' . $uid, $action);
}

/**
 * Imports one or more tasks represented in the specified content type.
 *
 * If a UID is present in the content and the task is already in the
 * database, a replace is performed rather than an add.
 *
 * @param string $content      The content of the task.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             text/calendar
 *                             text/x-vcalendar
 * @param string $tasklist     The tasklist into which the task will be
 *                             imported.  If 'null', the user's default
 *                             tasklist will be used.
 *
 * @return string  The new UID on one import, an array of UIDs on multiple imports,
 *                 or PEAR_Error on failure.
 */
function _nag_import($content, $contentType, $tasklist = null)
{
    require_once dirname(__FILE__) . '/base.php';

    global $prefs;

    if ($tasklist === null) {
        $tasklist = Nag::getDefaultTasklist(PERMS_EDIT);
    }

    if (!array_key_exists($tasklist, Nag::listTasklists(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    require_once 'Horde/iCalendar.php';

    /* Create a Nag_Driver instance. */
    require_once NAG_BASE . '/lib/Driver.php';

    $storage = &Nag_Driver::singleton($tasklist);

    switch ($contentType) {
    case 'text/x-vcalendar':
    case 'text/calendar':
    case 'text/x-vtodo':
        $iCal = new Horde_iCalendar();
        if (!is_a($content, 'Horde_iCalendar_vtodo')) {
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }
        } else {
            $iCal->addComponent($content);
        }

        $components = $iCal->getComponents();
        if (count($components) == 0) {
            return PEAR::raiseError(_("No iCalendar data was found."));
        }

        $ids = array();
        foreach ($components as $content) {
            if (is_a($content, 'Horde_iCalendar_vtodo')) {
                $task = new Nag_Task();
                $task->fromiCalendar($content);
                if (isset($task->uid) &&
                    !is_a(($existing = $storage->getByUID($task->uid)), 'PEAR_Error')) {
                    $taskId = $existing->id;
                    $result = $storage->modify(
                        $taskId,
                        isset($task->name) ? $task->name : $existing->name,
                        isset($task->desc) ? $task->desc : $existing->desc,
                        isset($task->start) ? $task->start : $existing->start,
                        isset($task->due) ? $task->due : $existing->due,
                        isset($task->priority) ? $task->priority : $existing->priority,
                        isset($task->estimate) ? $task->estimate : 0,
                        isset($task->completed) ? (int)$task->completed : $existing->completed,
                        isset($task->category) ? $task->category : $existing->category,
                        isset($task->alarm) ? $task->alarm : $existing->alarm,
                        isset($task->parent_id) ? $task->parent_id : $existing->parent_id,
                        isset($task->private) ? $task->private : $existing->private,
                        isset($task->owner) ? $task->owner : $existing->owner,
                        isset($task->assignee) ? $task->assignee : $existing->assignee);

                    if (is_a($result, 'PEAR_Error')) {
                        return $result;
                    }
                    $ids[] = $task->uid;
                } else {
                    $newTask = $storage->add(
                        isset($task->name) ? $task->name : '',
                        isset($task->desc) ? $task->desc : '',
                        isset($task->start) ? $task->start : 0,
                        isset($task->due) ? $task->due : 0,
                        isset($task->priority) ? $task->priority : 3,
                        isset($task->estimate) ? $task->estimate : 0,
                        !empty($task->completed),
                        isset($task->category) ? $task->category : '',
                        isset($task->alarm) ? $task->alarm : 0,
                        isset($task->uid) ? $task->uid : null,
                        isset($task->parent_id) ? $task->parent_id : '',
                        !empty($task->private),
                        Auth::getAuth(),
                        isset($task->assignee) ? $task->assignee : null);
                    if (is_a($newTask, 'PEAR_Error')) {
                        return $newTask;
                    }
                    // use UID rather than ID
                    $ids[] = $newTask[1];

                }

            }
        }
        if (count($ids) == 0) {
            return PEAR::raiseError(_("No iCalendar data was found."));
        } else if (count($ids) == 1) {
            return $ids[0];
        }
        return $ids;
    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));

}

/**
 * Exports a task, identified by UID, in the requested content type.
 *
 * @param string $uid          Identify the task to export.
 * @param string $contentType  What format should the data be in?
 *                             A string with one of:
 * <pre>
 * text/calendar    - (VCALENDAR 2.0. Recommended as this is specified in
 *                    rfc2445)
 * text/x-vcalendar - (old VCALENDAR 1.0 format. Still in wide use)
 * </pre>
 *
 * @return string  The requested data.
 */
function _nag_export($uid, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';

    $storage = &Nag_Driver::singleton();
    $task = $storage->getByUID($uid);
    if (is_a($task, 'PEAR_Error')) {
        return $task;
    }

    if (!array_key_exists($task->tasklist, Nag::listTasklists(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $version = '2.0';
    switch ($contentType) {
    case 'text/x-vcalendar':
        $version = '1.0';
    case 'text/calendar':
        require_once dirname(__FILE__) . '/version.php';
        require_once 'Horde/iCalendar.php';

        // Create the new iCalendar container.
        $iCal = new Horde_iCalendar($version);
        $iCal->setAttribute('PRODID', '-//The Horde Project//Nag ' . NAG_VERSION . '//EN');
        $iCal->setAttribute('METHOD', 'PUBLISH');

        // Create new vTodo object.
        $vTodo = $task->toiCalendar($iCal);
        $vTodo->setAttribute('VERSION', $version);

        $iCal->addComponent($vTodo);

        return $iCal->exportvCalendar();

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));
    }
}

/**
 * Exports a tasklist in the requested content type.
 *
 * @param string $tasklist     The tasklist to export.
 * @param string $contentType  What format should the data be in?
 *                             A string with one of:
 *                             <pre>
 *                             text/calendar (VCALENDAR 2.0. Recommended as
 *                                            this is specified in rfc2445)
 *                             text/x-vcalendar (old VCALENDAR 1.0 format.
 *                                              Still in wide use)
 *                             </pre>
 *
 * @return string  The iCalendar representation of the tasklist.
 */
function _nag_exportTasklist($tasklist, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';

    if (!array_key_exists($tasklist,
                          Nag::listTasklists(false, PERMS_READ))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $tasks = Nag::listTasks(null, null, null, array($tasklist), 1);

    $version = '2.0';
    switch ($contentType) {
    case 'text/x-vcalendar':
        $version = '1.0';
    case 'text/calendar':
        $share = &$GLOBALS['nag_shares']->getShare($tasklist);

        require_once 'Horde/iCalendar.php';
        $iCal = new Horde_iCalendar($version);
        $iCal->setAttribute('X-WR-CALNAME', String::convertCharset($share->get('name'), NLS::getCharset(), 'utf-8'));

        $tasks->reset();
        while ($task = $tasks->each()) {
            $iCal->addComponent($task->toiCalendar($iCal));
        }

        return $iCal->exportvCalendar();
    }

    return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));

}

/**
 * Deletes a task identified by UID.
 *
 * @param string|array $uid  Identify the task to delete, either a single UID
 *                           or an array.
 *
 * @return boolean  Success or failure.
 */
function _nag_delete($uid)
{
    // Handle an arrray of UIDs for convenience of deleting multiple tasks at
    // once.
    if (is_array($uid)) {
        foreach ($uid as $g) {
            $result = _nag_delete($g);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
    }

    require_once dirname(__FILE__) . '/base.php';

    $storage = &Nag_Driver::singleton();
    $task = $storage->getByUID($uid);
    if (is_a($task, 'PEAR_Error')) {
        return $task;
    }

    if (!Auth::isAdmin() &&
        !array_key_exists($task->tasklist,
                          Nag::listTasklists(false, PERMS_DELETE))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    return $storage->delete($task->id);
}

/**
 * Replaces the task identified by UID with the content represented in the
 * specified content type.
 *
 * If you want to replace multiple tasks with the UID specified in the
 * VCALENDAR data, you may use _nag_import instead. This automatically does a
 * replace if existings UIDs are found.
 *
 *
 * @param string $uid          Identify the task to replace.
 * @param string $content      The content of the task.
 * @param string $contentType  What format is the data in? Currently supports:
 *                             - text/x-vcalendar
 *                             - text/calendar
 *
 * @return boolean  Success or failure.
 */
function _nag_replace($uid, $content, $contentType)
{
    require_once dirname(__FILE__) . '/base.php';

    $storage = &Nag_Driver::singleton();
    $existing = $storage->getByUID($uid);
    if (is_a($existing, 'PEAR_Error')) {
        return $existing;
    }
    $taskId = $existing->id;

    if (!array_key_exists($existing->tasklist, Nag::listTasklists(false, PERMS_EDIT))) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    switch ($contentType) {
    case 'text/calendar':
    case 'text/x-vcalendar':
        if (!is_a($content, 'Horde_iCalendar_vtodo')) {
            require_once 'Horde/iCalendar.php';
            $iCal = new Horde_iCalendar();
            if (!$iCal->parsevCalendar($content)) {
                return PEAR::raiseError(_("There was an error importing the iCalendar data."));
            }

            $components = $iCal->getComponents();
            $component = null;
            foreach ($components as $content) {
                if (is_a($content, 'Horde_iCalendar_vtodo')) {
                    if ($component !== null) {
                        return PEAR::raiseError(_("Multiple iCalendar components found; only one vTodo is supported."));
                    }
                    $component = $content;
                }

            }
            if ($component === null) {
                return PEAR::raiseError(_("No iCalendar data was found."));
            }
        }

        $task = new Nag_Task();
        $task->fromiCalendar($content);
        $result = $storage->modify(
            $taskId,
            isset($task->name) ? $task->name : $existing->name,
            isset($task->desc) ? $task->desc : $existing->desc,
            isset($task->start) ? $task->start : $existing->start,
            isset($task->due) ? $task->due : $existing->due,
            isset($task->priority) ? $task->priority : $existing->priority,
            isset($task->estimate) ? $task->estimate : 0,
            isset($task->completed) ? (int)$task->completed : $existing->completed,
            isset($task->category) ? $task->category : $existing->category,
            isset($task->alarm) ? $task->alarm : $existing->alarm,
            isset($task->parent_id) ? $task->parent_id : $existing->parent_id,
            isset($task->private) ? $task->private : $existing->private,
            isset($task->owner) ? $task->owner : $existing->owner,
            isset($task->assignee) ? $task->assignee : $existing->assignee);

        break;

    default:
        return PEAR::raiseError(sprintf(_("Unsupported Content-Type: %s"), $contentType));
    }

    return $result;
}

/**
 * Lists active tasks as cost objects.
 *
 * @todo Implement $criteria parameter.
 *
 * @param array $criteria   Filter attributes
 */
function _nag_listCostObjects($criteria)
{
    require_once dirname(__FILE__) . '/base.php';

    $tasks = Nag::listTasks(null, null, null, null, 1);
    $result = array();
    $tasks->reset();
    while ($task = $tasks->each()) {
        $result[$task->id] = array('id' => $task->id,
                                   'active' => !$task->completed,
                                   'name' => $task->name);
        if (!empty($task->estimate)) {
            $result[$task->id]['estimate'] = $task->estimate;
        }
    }

    if (count($result) == 0) {
        return array();
    } else {
        return array(array('category' => _("Tasks"),
                           'objects'  => array_values($result)));
    }
}

function _nag_listTimeObjectCategories()
{
    require_once dirname(__FILE__) . '/base.php';

    $categories = array();
    $tasklists = Nag::listTasklists(false, PERMS_SHOW | PERMS_READ);
    foreach ($tasklists as $tasklistId => $tasklist) {
        $categories[$tasklistId] = $tasklist->get('name');
    }
    return $categories;
}

/**
 * Lists active tasks as time objects.
 *
 * @param array $categories  The time categories (from listTimeObjectCategories) to list.
 * @param mixed $start       The start date of the period.
 * @param mixed $end         The end date of the period.
 */
function _nag_listTimeObjects($categories, $start, $end)
{
    require_once dirname(__FILE__) . '/base.php';

    $allowed_tasklists = Nag::listTasklists(false, PERMS_READ);
    foreach ($categories as $tasklist) {
        if (!array_key_exists($tasklist, $allowed_tasklists)) {
            return PEAR::raiseError(_("Permission Denied"));
        }
    }

    $timeobjects = array();
    $start = new Horde_Date($start);
    $start_ts = $start->timestamp();
    $end = new Horde_Date($end);
    $end_ts = $end->timestamp();

    // List incomplete tasks.
    $tasks = Nag::listTasks(null, null, null, $categories, 0);
    $tasks->reset();
    while ($task = $tasks->each()) {
        // If there's no due date, it's not a time object.
        if (!$task->due || $task->due + 1 < $start_ts || $task->due > $end_ts) {
            continue;
        }
        $due_date = date('Y-m-d\TH:i:s', $task->due);
        $timeobjects[$task->id] = array(
            'id' => $task->id,
            'title' => $task->name,
            'description' => $task->desc,
            'start' => $due_date,
            'end' => $due_date,
            'category' => $task->category,
            'params' => array('task' => $task->id,
                              'tasklist' => $task->tasklist));
    }

    return $timeobjects;
}

/**
 * Lists alarms for a given moment.
 *
 * @param integer $time  The time to retrieve alarms for.
 * @param string $user   The user to retreive alarms for. All users if null.
 *
 * @return array  An array of UIDs
 */
function _nag_listAlarms($time, $user = null)
{
    require_once dirname(__FILE__) . '/base.php';
    require_once 'Horde/Group.php';

    if ((empty($user) || $user != Auth::getAuth()) && !Auth::isAdmin()) {
        return PEAR::raiseError(_("Permission Denied"));
    }

    $storage = &Nag_Driver::singleton();
    $group = &Group::singleton();
    $alarm_list = array();
    $tasklists = is_null($user) ? array_keys($GLOBALS['nag_shares']->listAllShares()) :  $GLOBALS['display_tasklists'];

    $alarms = Nag::listAlarms($time, $tasklists);
    if (is_a($alarms, 'PEAR_Error')) {
        return $alarms;
    }

    foreach ($alarms as $alarm) {
        $share = $GLOBALS['nag_shares']->getShare($alarm->tasklist);
        if (is_a($share, 'PEAR_Error')) {
            continue;
        }
        if (empty($user)) {
            $users = $share->listUsers(PERMS_READ);
            $groups = $share->listGroups(PERMS_READ);
            foreach ($groups as $gid) {
                $users = array_merge($users, $group->listUsers($gid));
            }
            $users = array_unique($users);
        } else {
            $users = array($user);
        }
        foreach ($users as $alarm_user) {
            $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                       'nag', $alarm_user, null, null, false);
            /* @todo: replace with NLS::setLanguageEnvironement(). */
            NLS::setLang($prefs->getValue('language'));
            NLS::setTextdomain('nag', NAG_BASE . '/locale', NLS::getCharset());
            String::setDefaultCharset(NLS::getCharset());
            $alarm_list[] = $alarm->toAlarm($alarm_user, $prefs);
        }
    }

    return $alarm_list;
}

/**
 * Synchronizes nag with the IMAP backend
 *
 * @return boolean  False if something went wrong
 */
function _nag_synchronize()
{
    require_once dirname(__FILE__) . '/base.php';

    $tasklist = Nag::getDefaultTasklist(PERMS_READ);

    if (!array_key_exists($tasklist,
                          Nag::listTasklists(false, PERMS_READ))) {
        return False;
    }

    $storage = &Nag_Driver::singleton($tasklist);
    if (get_class ($storage) == 'Nag_Driver_kolab' &&
        get_class ($storage->_wrapper) == 'Nag_Driver_kolab_wrapper_new') {

        $storage->_wrapper->connect ();
        if (get_class ($storage->_wrapper->_store) == 'Kolab_IMAP') {
            $storage->_wrapper->_store->_synchronize ();
        }
    }

    return True;
}
