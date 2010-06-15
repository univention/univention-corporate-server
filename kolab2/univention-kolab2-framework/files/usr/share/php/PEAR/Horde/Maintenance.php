<?php

/** @constant MAINTENANCE_YEARLY Do task yearly (First login after/on January 1). */
define('MAINTENANCE_YEARLY', 1);

/** @constant MAINTENANCE_MONTHLY Do task monthly (First login after/on first of month). */
define('MAINTENANCE_MONTHLY', 2);

/** @constant MAINTENANCE_WEEKLY Do task weekly (First login after/on a Sunday). */
define('MAINTENANCE_WEEKLY', 3);

/** @constant MAINTENANCE_DAILY Do task daily (First login of the day). */
define('MAINTENANCE_DAILY', 4);

/** @constant MAINTENANCE_EVERY Do task every login. */
define('MAINTENANCE_EVERY', 5);

/** @constant MAINTENANCE_FIRST_LOGIN Do task on first login only. */
define('MAINTENANCE_FIRST_LOGIN', 6);

/** @constant MAINTENANCE_OUTPUT_CONFIRM Confirmation-style output for maintenance page. */
define('MAINTENANCE_OUTPUT_CONFIRM', 7);

/** @constant MAINTENANCE_OUTPUT_AGREE Agreement-style output for maintenance page. */
define('MAINTENANCE_OUTPUT_AGREE', 8);

/** @constant MAINTENANCE_OUTPUT_NOTICE Notice-style output for maintenance page. */
define('MAINTENANCE_OUTPUT_NOTICE', 9);

/** @constant MAINTENANCE_CACHE_PARAM The name of the URL parameter that contains the session ID of the cache object. */
define('MAINTENANCE_CACHE_PARAM', 'maintenance_cache');

/** @constant MAINTENANCE_DONE_PARAM The name of the URL parameter that indicates that the maintenance tasks are completed. */
define('MAINTENANCE_DONE_PARAM', 'maintenance_done');

/* Intervals hash - used to build select tables in preferences menu. */
$intervals = array();
$intervals[MAINTENANCE_YEARLY]  = _("Yearly");
$intervals[MAINTENANCE_MONTHLY] = _("Monthly");
$intervals[MAINTENANCE_WEEKLY]  = _("Weekly");
$intervals[MAINTENANCE_DAILY]   = _("Daily");
$intervals[MAINTENANCE_EVERY]   = _("Every Login");
$GLOBALS['intervals'] = &$intervals;

/**
 * The Maintenance:: class provides a set of methods for dealing with
 * maintenance operations run upon login to Horde applications.
 *
 * $Horde: framework/Maintenance/Maintenance.php,v 1.44 2004/04/07 14:43:10 chuck Exp $
 *
 * Copyright 2001-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3.5
 * @package Horde_Maintenance
 */
class Maintenance {

    /**
     * Hash holding maintenance preference names.
     * Syntax:  PREFNAME => interval
     * Valid intervals are: MAINTENANCE_YEARLY, MAINTENANCE_MONTHLY,
     *                      MAINTENANCE_WEEKLY, MAINTENANCE_DAILY,
     *                      MAINTENANCE_EVERY,  MAINTENANCE_FIRST_LOGIN
     * Operations will be run in the order they appear in the array -
     *   MAKE SURE FUNCTIONS ARE IN THE CORRECT ORDER!
     * Operations can appear more than once - they will only be run once per
     *   login though (the operation will run the first time it is seen in
     *   the array).
     *
     * This array should be filled in for each Horde module that extends
     *   the Maintenance class.
     *
     * @var array $maint_tasks
     */
    var $maint_tasks = array();

    /**
     * UNIX timestamp of the last login time for user.
     *
     * @var integer $_lastLogin
     */
    var $_lastLogin = 0;

    /**
     * The Maintenance_Tasklist object for this login.
     *
     * @var object Maintenance_Tasklist $_tasklist
     */
    var $_tasklist;

    /**
     * Array to store Maintenance_Task objects.
     *
     * @var array $_modulesCache
     */
    var $_taskCache = array();

    /**
     * Attempts to return a concert Maintenance_* object based on the
     * module name passed into it.
     *
     * @access public
     *
     * @param string $module           The name of the Horde module.
     * @param optional array $params   A hash containing additional data
     *                                 needed by the constructor.
     *
     * @return object Maintenance  The Maintenance object.
     *                             Returns false on error.
     */
    function &factory($module, $params = array())
    {
        global $registry;

        /* Spawn the relevant driver, and return it (or false on failure). */
        include_once $registry->getParam('fileroot', $module) . '/lib/Maintenance/' . $module . '.php';
        $class = 'Maintenance_' . $module;
        if (class_exists($class)) {
            return $ret = &new $class($params);
        } else {
            return false;
        }
    }

    /**
     * Constructor.
     *
     * @access public
     *
     * @param array $params  A hash containing the following entries:
     *                       'last_login' => The last login timestamp.
     */
    function Maintenance($params = array())
    {
        /* Set the class variable $_lastLogin. */
        if (array_key_exists('last_login', $params)) {
            $this->_lastLogin = $params['last_login'];
        }

        /* Retrieve the Maintenance_Tasklist object from the session. */
        if (($sid = Util::getFormData(MAINTENANCE_CACHE_PARAM))) {
            $this->_retrieveSessionData($sid);
        }
    }

    /**
     * Do maintenance operations needed for this login.
     * This function will generate the list of tasks to perform during
     * this login and will redirect to the maintenance page if necessary.
     * This is the function that should be called from the
     * application upon login.
     *
     * @access public
     */
    function runMaintenance()
    {
        /* Check to see if we are finished with maintenance operations. */
        if (!Util::getFormData(MAINTENANCE_DONE_PARAM)) {
            /* Generate the list of tasks. */
            $this->_createTaskList();

            /* Determine if we should redirect to the maintenance page. */
            if ($this->_needMaintenancePage() !== null) {
                header('Location: ' . $this->_getMaintenanceURL(), true);
                exit;
            }
        }

        /* Finally, run any tasks that need to be executed. */
        $this->_doMaintenanceTasks();
    }

    /**
     * Do the necessary maintenance tasks for this loading of the
     * maintenance page.
     * This is the function that is called from the maintenance page
     * every time it is loaded.
     *
     * @access public
     *
     * @return integer  The display required for the maintenance page.
     */
    function runMaintenancePage()
    {
        /* Should we run any tasks? */
        $this->_doMaintenanceTasks();

        /* Get the list of tasks we need to display to the user. */
        $task_no = $this->_needMaintenancePage();
        $tasks = $this->_tasklist->getList();

        /* Remove 'newflag' from first task. */
        if (!$this->_tasklist->processed(true)) {
            reset($tasks);
            $this->_tasklist->unsetNewPage(key($tasks));
        }

        if (!is_null($task_no)) {
            $tasks = array_slice($tasks, 0, $task_no + 1);
        }
        reset($tasks);
        $action = $tasks[key($tasks)]['display'];

        return array($action, array_keys($tasks));
    }

    /**
     * Returns the informational text message on what the operation is about
     * to do. Also indicates whether the box should be checked by default or
     * not. Operations that have been locked by the admin will return null.
     *
     * @access public
     *
     * @param string $pref  Name of the operation to get information for.
     *
     * @return array  1st element - Description of what the operation is about
     *                              to do during this login.
     *                2nd element - Whether the preference is set to on or not.
     */
    function infoMaintenance($pref)
    {
        global $prefs;

        /* If the preference has been locked by the admin, do not show
           the user. */
        if ($prefs->isLocked($pref)) {
            return;
        }

        $mod = &$this->_loadModule($pref);
        return array($mod->describeMaintenance(), $prefs->getValue($pref));
    }

    /**
     * Export variable names to use for creating select tables in the
     * preferences menu.
     *
     * @access public
     *
     * @return array  An array of variable names to be imported into the
     *                prefs.php namespace.
     */
    function exportIntervalPrefs()
    {
        global $prefs;

        $return_array = array();

        foreach (array_keys($this->maint_tasks) as $val) {
            if (!$prefs->isLocked($val . '_interval')) {
                $return_array[] = $val . '_interval_options';
            }
        }

        return $return_array;
    }

    /**
     * Output hidden for elements for the POST form to ensure the calling
     * script has the same POST elements as when the maintenance operations
     * first run.
     *
     * @access public
     *
     * @return string  The form data.
     */
    function getPostData()
    {
        $text = '';

        if (($data = $this->_tasklist->getPostData())) {
            foreach ($data as $name => $val) {
                $text .= '<input type="hidden" name="' . htmlspecialchars($name) . '" value="' . htmlspecialchars($val) . '" />' . "\n";
            }
        }

        return $text;
    }

    /**
     * Creates the list of maintenance operations that are available for
     * this session (stored in Maintenance_Tasklist object).
     *
     * @access private
     *
     * @return boolean  Returns true if list was created.
     *                  False if not (e.g. list already exists).
     */
    function _createTaskList()
    {
        global $prefs;

        /* Create a new Maintenance_Tasklist object. */
        $this->_tasklist = &new Maintenance_Tasklist();

        /* Create time objects for today's date and last login date. */
        $last_date = getdate($this->_lastLogin);
        $cur_date  = getdate();

        /* Go through each item in $maint_tasks and determine if we need to
           run it during this login. */
        foreach ($this->maint_tasks as $key => $val) {
            /* Skip item if it already appears in the tasks list. */
            if ($this->_tasklist->inList($key)) {
                continue;
            }

            /* Determine the correct interval for the item. */
            if (($interval = $prefs->getValue($key . '_interval'))) {
                $val = $interval;
            }

            $addTask = false;

            /* FIRST LOGIN OPERATIONS */
            /* If $_lastLogin is empty (= 0), this is the first time the user
               has logged in. Don't run any other maintenance operations on
               the first login. */
            if (empty($this->_lastLogin)) {
                if ($val == MAINTENANCE_FIRST_LOGIN) {
                    $addTask = true;
                }
            }

            /* YEARLY_OPERATIONS */
            elseif (($val == MAINTENANCE_YEARLY) &&
                    ($cur_date['year'] > $last_date['year'])) {
                $addTask = true;
            }

            /* MONTHLY OPERATIONS */
            elseif (($val == MAINTENANCE_MONTHLY) &&
                    (($cur_date['year'] > $last_date['year']) || ($cur_date['mon'] > $last_date['mon']))) {
                $addTask = true;
            }

            /* WEEKLY OPERATIONS */
            elseif (($val == MAINTENANCE_WEEKLY) &&
                    (($cur_date['wday'] < $last_date['wday']) || ((time() - 604800) > $this->_lastLogin))) {
                $addTask = true;
            }

            /* DAILY OPERATIONS */
            elseif (($val == MAINTENANCE_DAILY) &&
                    (($cur_date['year'] > $last_date['year']) || ($cur_date['yday'] > $last_date['yday']))) {
                $addTask = true;
            }

            /* EVERY LOGIN OPERATIONS */
            elseif ($val == MAINTENANCE_EVERY) {
                $addTask = true;
            }
            /* Skip the task if any of the following:
               + This task does not need to be run in this login
               + This task is not set in the preferences */
            if (!$addTask || !$prefs->getValue($key)) continue;

            /* Load the task module now. */
            $mod = &$this->_loadModule($key);

            /* Determine if this task has already been confirmed/set via some
               sort of admin setting. Also, if the user/admin has set the
               'confirm_maintenance' flag, use the preferences value. */
            $confirmed = false;
            if ($prefs->isLocked($key) ||
                !$prefs->getValue('confirm_maintenance')) {
                $confirmed = (boolean) $prefs->getValue($key);
            }

            /* Add the task to the tasklist. */
            $this->_tasklist->addTask($key, $confirmed, $mod->getDisplayType());
        }
    }

    /**
     * Load module (if not already loaded).
     *
     * @access private
     *
     * @param string $modname  Name of the module to load.
     *
     * @return object Maintenance_Task  A reference to the requested module.
     */
    function &_loadModule($modname)
    {
        global $registry;

        if (!array_key_exists($modname, $this->_taskCache)) {
            include_once $registry->getParam('fileroot', $this->_tasklist->getModule()) . '/lib/Maintenance/Task/' . $modname . '.php';
            $class = 'Maintenance_Task_' . $modname;
            if (class_exists($class)) {
                $this->_taskCache[$modname] = new $class;
            } else {
                Horde::fatal(PEAR::raiseError(sprintf(_("Could not open Maintenance_Task module %s"), $class)), __FILE__, __LINE__);
            }
        }

        return $this->_taskCache[$modname];
    }

    /**
     * Return the URL needed for the maintenance form.
     *
     * @access public
     *
     * @return string  The URL to redirect to.
     */
    function getMaintenanceFormURL()
    {
       if ($this->_needMaintenancePage() !== null) {
           return $this->_getMaintenanceURL();
       } else {
           return $this->_getInitialPageURL();
       }
    }

    /**
     * Get the URL for the initial page.
     *
     * @access private
     *
     * @return string  The URL for the initial page.
     */
    function _getInitialPageURL()
    {
        $url = Util::addParameter($this->_tasklist->getTarget(), MAINTENANCE_CACHE_PARAM, $this->_createSessionData());
        return Util::addParameter($url, MAINTENANCE_DONE_PARAM, 1);
    }

    /**
     * Get the URL for the maintenance page.
     *
     * @access private
     *
     * @return string  The URL for the maintenance page.
     */
    function _getMaintenanceURL()
    {
        global $registry;

        /* We need to pass the cache ID and 'module' parameters. */
        $url = Horde::url($registry->getParam('webroot', 'horde') . '/services/maintenance.php');
        $url = Util::addParameter($url, MAINTENANCE_CACHE_PARAM, $this->_createSessionData());
        $url = Util::addParameter($url, 'module', $this->_tasklist->getModule());

        return $url;
    }

    /**
     * Creates the session cache used to hold data between requests.
     *
     * @access private
     *
     * @return string  Cache_session identifier string.
     */
    function _createSessionData()
    {
        require_once 'Horde/SessionObjects.php';
        $cacheSess = &Horde_SessionObjects::singleton();

        return $cacheSess->storeOid($this->_tasklist, false);
    }

    /**
     * Retrieves session data from a previous request.
     *
     * @access private
     *
     * @param string $sid  The session ID of the cache object.
     */
    function _retrieveSessionData($sid)
    {
        require_once 'Horde/SessionObjects.php';
        $cacheSess = &Horde_SessionObjects::singleton();

        $this->_tasklist = $cacheSess->query($sid);
        $cacheSess->setPruneFlag($sid, true);
    }

    /**
     * Execute all confirmed tasks.
     *
     * @access private
     */
    function _doMaintenanceTasks()
    {
        $tasks = $this->_tasklist->getList();

        foreach ($tasks as $key => $val) {
            if ($val['newpage']) {
                if ($this->_tasklist->processed()) {
                    $this->_tasklist->unsetNewPage($key);
                }
                break;
            } elseif ($val['confirmed'] ||
                      Util::getFormData($key . '_confirm')) {
                /* Perform maintenance if confirmed. */
                $mod = &$this->_loadModule($key);
                $mod->doMaintenance();
            }
            $this->_tasklist->removeTask($key);
        }
    }

    /**
     * Do any of the tasks require the maintenance page?
     *
     * @access private
     *
     * @return integer  The key of the task that requires the maintenance
     *                  page. Returns null if the maintenance page is no
     *                  longer needed.
     */
    function _needMaintenancePage()
    {
        $i = 0;
        foreach ($this->_tasklist->getList() as $val) {
            if ($val['newpage']) return $i;
            $i++;
        }

        return null;
    }

}

/**
 * The Maintenance_Tasklist:: class is used to store the list of maintenance
 * tasks that need to be run during this login.
 *
 * Copyright 2002-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Maintenance
 */
class Maintenance_Tasklist {

    /**
     * The Horde module running the maintenance tasks.
     *
     * @var string $_module
     */
    var $_module;

    /**
     * The URL of the web page to load after maintenance is complete.
     *
     * @var string $_target
     */
    var $_target;

    /**
     * POST data for the calling script.
     *
     * @var array $_postdata
     */
    var $_postdata;

    /**
     * The list of tasks to run during this login.
     *
     * KEY:    Task name
     * VALUE:  Array => (
     *           'confirmed'  =>  boolean,
     *           'display'    =>  integer,
     *           'newpage'    =>  boolean
     *         )
     *
     * @var array $_tasks
     */
    var $_tasks = array();

    /**
     * Internal flag for addTask().
     *
     * @var boolean $_addFlag
     */
    var $_addFlag = false;

    /**
     * Has the tasklist been processed yet?
     *
     * @var boolean $_processed
     */
    var $_processed = false;

    /**
     * Constructor.
     *
     * @access public
     */
    function Maintenance_Tasklist()
    {
        global $registry;

        $this->_module = $registry->getApp();
        $this->_target = Horde::selfURL(true);
//        $this->_postdata = $_POST;
    }

    /**
     * Adds a task to the tasklist.
     *
     * @access public
     *
     * @param string $key         The name of the task to perform.
     * @param boolean $confirmed  Has the task been confirmed?
     * @param integer $display    The display type of the task.
     */
    function addTask($key, $confirmed, $display)
    {
        $this->_tasks[$key] = array();
        $this->_tasks[$key]['confirmed'] = $confirmed;
        $this->_tasks[$key]['display'] = $display;

        if (($display == MAINTENANCE_OUTPUT_AGREE) ||
            ($display == MAINTENANCE_OUTPUT_NOTICE)) {
            $this->_tasks[$key]['newpage'] = true;
            $this->_addFlag = false;
        } elseif (($confirmed == false) && (!$this->_addFlag)) {
            $this->_tasks[$key]['newpage'] = true;
            $this->_addFlag = true;
        } else {
            $this->_tasks[$key]['newpage'] = false;
        }
    }

    /**
     * Unsets the newpage flag for a task.
     *
     * @access public
     *
     * @param string $task  The name of the task to alter.
     */
    function unsetNewPage($task)
    {
        if ($this->inList($task)) {
            $this->_tasks[$task]['newpage'] = false;
        }
    }

    /**
     * Removes the task from the tasklist.
     *
     * @access public
     *
     * @param string $task  The name of the task to alter.
     */
    function removeTask($task)
    {
        if ($this->inList($task)) {
            unset($this->_tasks[$task]);
        }
    }

    /**
     * Is this task already in the tasklist?
     *
     * @access public
     *
     * @param string $task  The name of the task.
     *
     * @return boolean  Whether the task is already in the tasklist.
     */
    function inList($task)
    {
        return array_key_exists($task, $this->_tasks);
    }

    /**
     * Return the list of tasks.
     *
     * @access public
     *
     * @return array  The list of tasks that still need to be done.
     */
    function getList()
    {
        return $this->_tasks;
    }

    /**
     * Return the Horde module the tasks are running under.
     *
     * @access public
     *
     * @return string  The Horde module name.
     */
    function getModule()
    {
        return $this->_module;
    }

    /**
     * Return the POST data.
     *
     * @access public
     *
     * @return array  The POST data from the initial URL.
     */
    function getPostData()
    {
        return $this->_postdata;
    }

    /**
     * Return the URL of the web page to load after maintenance is complete.
     *
     * @access public
     *
     * @return string  The target URL.
     */
    function getTarget()
    {
        return $this->_target;
    }

    /**
     * Sets/displays the flag to show that tasklist has been processed at
     * least once.
     *
     * @access public
     *
     * @param optional boolean $set  Set the flag?
     *
     * @return boolean  Has the tasklist been processed before?
     */
    function processed($set = false)
    {
        $retvalue = $this->_processed;
        if ($set) {
            $this->_processed = true;
        }
        return $retvalue;
    }

}

/**
 * Abstract class to allow for modularization of specific maintenace tasks.
 *
 * For this explanation, the specific Horde application you want to create
 * maintenance actions for will be labeled HORDEAPP.
 *
 * To add a new maintenance task, you need to do the following:
 * [1] Add preference to "HORDEAPP/config/prefs.php" file.
 *     (The name of this preference will be referred to as PREFNAME)
 *     This preference should be of type 'checkbox' (i.e. 1 = on; 0 = off).
 *     [Optional:]  Add a preference in prefs.php of the name
 *                  'PREFNAME_interval' to allow the user to set the interval.
 *                  'default' value should be set to the values of the interval
 *                  constants above.
 *                  If this preference doesn't exist, the default interval
 *                  used will be the one that appears in $maint_tasks.
 * [2] Create a directory named "HORDEAPP/lib/Maintenance".
 * [3] Create a class entitled Maintenance_HORDEAPP that extends the
 *     Maintenance class.
 *     This class should contain only the application specific definitions of
 *     $maint_tasks (see above for description).
 *     Save this file as "HORDEAPP/lib/Maintenance/HORDEAPP.php".
 * [4] Create a directory titled "HORDEAPP/lib/Maintenance/Task".
 * [5] Create modules in HORDEAPP/lib/Maintenance/Task named 'PREFNAME.php'
 *     that extend the Maintenance_Task class.
 *     The class should be named Maintenance_Task_PREFNAME.
 *     The class should declare the following two methods:
 *       'doMaintenance' - This is the function that is run to do the
 *                         specified maintenance operation.
 *       'describeMaintenance' - This function sets the preference text
 *                               and text to be used on the confirmation
 *                               page.  Should return a description of what
 *                               your 'doMaintenance' function is about to do.
 *     Neither function requires any parameters passed in.
 *
 * There are 3 different types of maintenance (set via $_display_type):
 * [1] MAINTENANCE_OUTPUT_CONFIRM
 *     Each output from describeMaintenance() will have a checkbox associated
 *     with it. For each checkbox selected, doMaintenance() for that task will
 *     be run. More than 1 confirmation message can be displayed on the
 *     maintenance page at once.
 *
 * [2] MAINTENANCE_OUTPUT_AGREE
 *     The output from describeMaintenance() should be text asking the user to
 *     agree/disagree to specified terms. If 'yes' is selected, the POST
 *     variable 'agree' will be set. If 'no' is selected, the POST variable
 *     'not_agree' will be set. In either case, doMaintenance() will ALWAYS be
 *     run.
 *     * This style will be displayed on its own, separate maintenance page. *
 *
 * [3] MAINTENANCE_OUTPUT_NOTICE
 *     The output from describeMaintenance() should be any non-interactive text
 *     desired. There will be a single 'Click to Continue' button below this
 *     text. doMaintenance() will ALWAYS be run.
 *     * This style will be displayed on its own, separate maintenance page. *
 *
 * Copyright 2001-2004 Michael Slusarz <slusarz@bigworm.colorado.edu>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Slusarz <slusarz@bigworm.colorado.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3.5
 * @package Horde_Maintenance
 */
class Maintenance_Task {

    /**
     * The style of the maintenance page output.
     * Possible values: MAINTENANCE_OUTPUT_CONFIRM,
     *                  MAINTENANCE_OUTPUT_AGREE,
     *                  MAINTENANCE_OUTPUT_NOTICE
     *
     * @var integer $_display_type
     */
    var $_display_type = MAINTENANCE_OUTPUT_CONFIRM;

    /**
     * Constructor
     *
     * @access public
     */
    function Maintenance_Task()
    {
    }

    /**
     * Do maintenance operation (if it has been confirmed).
     *
     * @access public
     *
     * @return boolean  Whether the maintenance operation was successful or
     *                  not.
     */
    function doMaintenance()
    {
        return false;
    }

    /**
     * Return description information for the maintenance page.
     *
     * @access public
     *
     * @return string  Description that will be displayed on the maintenance
     *                 confirmation page.
     */
    function describeMaintenance()
    {
        return '';
    }

    /**
     * Returns the desired output type for the maintenance page.
     *
     * @access public
     *
     * @return integer  Desired output type for the maintenance confirmation
     *                  page.
     */
    function getDisplayType()
    {
        return $this->_display_type;
    }

}
