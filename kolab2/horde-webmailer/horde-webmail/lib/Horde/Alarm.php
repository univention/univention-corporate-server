<?php
/**
 * @package Horde_Alarm
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * $Horde: framework/Alarm/Alarm.php,v 1.40.2.5 2009-01-06 15:22:48 jan Exp $
 */

/** Horde_Date */
require_once 'Horde/Date.php';

/**
 * The Horde_Alarm:: class provides an interface to deal with reminders,
 * alarms and notifications through a standardized API.
 *
 * Alarm hashes have the following fields:
 * - id: Unique alarm id.
 * - user: The alarm's user. Empty if a global alarm.
 * - start: The alarm start as a Horde_Date.
 * - end: The alarm end as a Horde_Date.
 * - methods: The notification methods for this alarm.
 * - params: The paramters for the notification methods.
 * - title: The alarm title.
 * - text: An optional alarm description.
 * - snooze: The snooze time (next time) of the alarm as a Horde_Date.
 * - internal: Holds internally used data.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package Horde_Alarm
 */
class Horde_Alarm {

    /**
     * Hash containing connection parameters.
     *
     * @var array
     */
    var $_params = array('ttl' => 300);

    /**
     * An error message to throw when something is wrong.
     *
     * @var string
     */
    var $_errormsg;

    /**
     * Constructor - just store the $params in our newly-created object. All
     * other work is done by initialize().
     *
     * @param array $params  Any parameters needed for this driver.
     */
    function Horde_Alarm($params = array(), $errormsg = null)
    {
        $this->_params = array_merge($this->_params, $params);
        if ($errormsg === null) {
            $this->_errormsg = _("The alarm backend is not currently available.");
        } else {
            $this->_errormsg = $errormsg;
        }
    }

    /**
     * Returns an alarm hash from the backend.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user
     *
     * @return array  An alarm hash.
     */
    function get($id, $user)
    {
        $alarm = $this->_get($id, $user);
        if (is_a($alarm, 'PEAR_Error')) {
            return $alarm;
        }
        if (isset($alarm['mail']['body'])) {
            $alarm['mail']['body'] = $this->_fromDriver($alarm['mail']['body']);
        }
        return $alarm;
    }

    /**
     * Stores an alarm hash in the backend.
     *
     * The alarm will be added if it doesn't exist, and updated otherwise.
     *
     * @param array $alarm  An alarm hash.
     */
    function set($alarm)
    {
        if (isset($alarm['mail']['body'])) {
            $alarm['mail']['body'] = $this->_toDriver($alarm['mail']['body']);
        }
        if ($this->exists($alarm['id'], isset($alarm['user']) ? $alarm['user'] : '')) {
            return $this->_update($alarm);
        } else {
            return $this->_add($alarm);
        }
    }

    /**
     * Returns whether an alarm with the given id exists already.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user
     *
     * @return boolean  True if the specified alarm exists.
     */
    function exists($id, $user)
    {
        $exists = $this->_exists($id, $user);
        return $exists && !is_a($exists, 'PEAR_Error');
    }

    /**
     * Delays (snoozes) an alarm for a certain period.
     *
     * @param string $id        The alarm's unique id.
     * @param string $user      The notified user.
     * @param integer $minutes  The delay in minutes. A negative value
     *                          dismisses the alarm completely.
     */
    function snooze($id, $user, $minutes)
    {
        $alarm = $this->get($id, $user);
        if (is_a($alarm, 'PEAR_Error')) {
            return $alarm;
        }
        if (empty($user)) {
            return PEAR::raiseError(_("This alarm cannot be snoozed."));
        }
        if ($alarm) {
            if ($minutes > 0) {
                $alarm['snooze'] = new Horde_Date(time());
                $alarm['snooze']->min += $minutes;
                $alarm['snooze']->correct();
                return $this->_snooze($id, $user, $alarm['snooze']);
            } else {
                return $this->_dismiss($id, $user);
            }
        }
    }

    /**
     * Returns whether an alarm is snoozed.
     *
     * @param string $id        The alarm's unique id.
     * @param string $user      The alarm's user
     * @param Horde_Date $time  The time when the alarm may be snoozed.
     *                          Defaults to now.
     *
     * @return boolean  True if the alarm is snoozed.
     */
    function isSnoozed($id, $user, $time = null)
    {
        if (is_null($time)) {
            $time = new Horde_Date(time());
        }
        return (bool)$this->_isSnoozed($id, $user, $time);
    }

    /**
     * Deletes an alarm from the backend.
     *
     * @param string $id    The alarm's unique id.
     * @param string $user  The alarm's user. All users' alarms if null.
     */
    function delete($id, $user = null)
    {
        return $this->_delete($id, $user);
    }

    /**
     * Retrieves active alarms from all applications and stores them in the
     * backend.
     *
     * The applications will only be called once in the configured time span,
     * by default 5 minutes.
     *
     * @param string $user      Retrieve alarms for this user, or for all users
     *                          if null.
     * @param boolean $preload  Preload alarms that go off within the next
     *                          ttl time span?
     */
    function load($user = null, $preload = true)
    {
        if (isset($_SESSION['horde']['alarm']['loaded']) &&
            time() - $_SESSION['horde']['alarm']['loaded'] < $this->_params['ttl']) {
            return;
        }

        global $registry;

        $apps = $registry->listApps(null, false, PERMS_READ);
        if (is_a($apps, 'PEAR_Error')) {
            return false;
        }
        foreach ($apps as $app) {
            if ($registry->hasMethod('listAlarms', $app)) {
                $pushed = $registry->pushApp($app, false);
                if (is_a($pushed, 'PEAR_Error')) {
                    Horde::logMessage($pushed, __FILE__, __LINE__, PEAR_LOG_ERR);
                    continue;
                }
                /* Preload alarms that happen in the next ttl seconds. */
                if ($preload) {
                    $alarms = $registry->callByPackage($app, 'listAlarms', array(time() + $this->_params['ttl'], $user));
                    if (is_a($alarms, 'PEAR_Error')) {
                        if ($pushed) {
                            $registry->popApp();
                        }
                        continue;
                    }
                } else {
                    $alarms = array();
                }
                /* Load current alarms if no preloading requested or if this
                 * is the first call in this session. */
                if (!$preload || !isset($_SESSION['horde']['alarm']['loaded'])) {
                    $app_alarms = $registry->callByPackage($app, 'listAlarms', array(time(), $user));
                    if (is_a($app_alarms, 'PEAR_Error')) {
                        Horde::logMessage($app_alarms, __FILE__, __LINE__, PEAR_LOG_ERR);
                        $app_alarms = array();
                    }
                    $alarms = array_merge($alarms, $app_alarms);
                }
                if ($pushed) {
                    $registry->popApp();
                }
                if (is_a($alarms, 'PEAR_Error') || empty($alarms)) {
                    continue;
                }
                foreach ($alarms as $alarm) {
                    $alarm['start'] = new Horde_Date($alarm['start']);
                    if (!empty($alarm['end'])) {
                        $alarm['end'] = new Horde_Date($alarm['end']);
                    }
                    $this->set($alarm);
                }
            }
        }

        $_SESSION['horde']['alarm']['loaded'] = time();
    }

    /**
     * Returns a list of alarms from the backend.
     *
     * @param string $user      Return alarms for this user, all users if
     *                          null, or global alarms if empty.
     * @param Horde_Date $time  The time when the alarms should be active.
     *                          Defaults to now.
     * @param boolean $load     Update active alarms from all applications?
     * @param boolean $preload  Preload alarms that go off within the next
     *                          ttl time span?
     *
     * @return array  A list of alarm hashes.
     */
    function listAlarms($user = null, $time = null, $load = false,
                        $preload = true)
    {
        if (empty($time)) {
            $time = new Horde_Date(time());
        }
        if ($load) {
            $this->load($user, $preload);
        }

        $alarms = $this->_list($user, $time);
        if (is_a($alarms, 'PEAR_Error')) {
            return $alarms;
        }

        foreach (array_keys($alarms) as $alarm) {
            if (isset($alarms[$alarm]['mail']['body'])) {
                $alarms[$alarm]['mail']['body'] = $this->_fromDriver($alarms[$alarm]['mail']['body']);
            }
        }
        return $alarms;
    }

    /**
     * Notifies the user about any active alarms.
     *
     * @param string $user      Notify this user, all users if null, or guest
     *                          users if empty.
     * @param boolean $load     Update active alarms from all applications?
     * @param boolean $preload  Preload alarms that go off within the next
     *                          ttl time span?
     * @param array $exclude    Don't notify with these methods.
     */
    function notify($user = null, $load = true, $preload = true,
                    $exclude = array())
    {
        $alarms = $this->listAlarms($user, null, $load, $preload);
        if (is_a($alarms, 'PEAR_Error')) {
            Horde::logMessage($alarms, __FILE__, __LINE__, PEAR_LOG_ERR);
            return $alarms;
        }
        if (empty($alarms)) {
            return;
        }

        $methods = array_keys($this->notificationMethods());
        foreach ($alarms as $alarm) {
            foreach ($alarm['methods'] as $alarm_method) {
                if (in_array($alarm_method, $methods) &&
                    !in_array($alarm_method, $exclude)) {
                    $result = $this->{'_' . $alarm_method}($alarm);
                    if (is_a($result, 'PEAR_Error')) {
                        Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    }
                }
            }
        }
    }

    /**
     * Notifies about an alarm through Horde_Notification.
     *
     * @param array $alarm  An alarm hash.
     */
    function _notify($alarm)
    {
        static $sound_played;

        $message = htmlspecialchars($alarm['title']);
        if (!empty($alarm['params']['notify']['show'])) {
            $message = Horde::link(Horde::url($GLOBALS['registry']->linkByPackage($alarm['params']['notify']['show']['__app'], 'show', $alarm['params']['notify']['show'])), $alarm['text']) . $message . '</a>';
        }

        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();
        if (!empty($alarm['user']) && $browser->hasFeature('xmlhttpreq')) {
            Horde::addScriptFile('prototype.js', 'horde', true);
            $url = Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/snooze.php', true);
            $opts = array('-1' => _("Dismiss"),
                          '5' => _("5 minutes"),
                          '15' => _("15 minutes"),
                          '60' => _("1 hour"),
                          '360' => _("6 hours"),
                          '1440' => _("1 day"));
            $id = 'snooze_' . md5($alarm['id']);
            $message .= ' <small onmouseover="if(typeof ' . $id . '_t!=\'undefined\')clearTimeout(' . $id . '_t);Element.show(\'' . $id . '\')" onmouseout="' . $id . '_t=setTimeout(function(){Element.hide(\'' . $id . '\')},500)">[' . _("Snooze...") . '<span id="' . $id . '" style="display:none"> ';
            $first = true;
            foreach ($opts as $minutes => $desc) {
                if (!$first) {
                    $message .= ', ';
                }
                $message .= Horde::link('#', '', '', '', 'new Ajax.Request(\'' . $url . '\',{parameters:{alarm:\'' . $alarm['id'] . '\',snooze:' . $minutes . '},onSuccess:function(){Element.remove(this);}.bind(this.parentNode.parentNode.parentNode)});return false;') . $desc . '</a>';
                $first = false;
            }
            $message .= '</span>]</small>';
        }

        $GLOBALS['notification']->push($message, 'horde.alarm', array('content.raw'));
        if (!empty($alarm['params']['notify']['sound']) &&
            !isset($sound_played[$alarm['params']['notify']['sound']])) {
            require_once 'Horde/Notification/Listener/audio.php';
            $GLOBALS['notification']->attach('audio');
            $GLOBALS['notification']->push($alarm['params']['notify']['sound'], 'audio');
            $sound_played[$alarm['params']['notify']['sound']] = true;
        }
    }

    /**
     * Notifies about an alarm by a javascript popup.
     *
     * @param array $alarm  An alarm hash.
     */
    function _popup($alarm)
    {
        $message = empty($alarm['params']['popup']['message'])
            ? $alarm['title']
            : $alarm['params']['popup']['message'];
        $message = 'alert(\'' . addcslashes($message, "\r\n\"'") . '\');';
        $GLOBALS['notification']->push($message, 'javascript');
    }

    /**
     * Notifies about an alarm by email.
     *
     * @param array $alarm  An alarm hash.
     */
    function _mail($alarm)
    {
        if (!empty($alarm['internal']['mail']['sent'])) {
            return;
        }

        if (empty($alarm['params']['mail']['email'])) {
            if (empty($alarm['user'])) {
                return;
            }
            require_once 'Horde/Identity.php';
            $identity = &Identity::singleton('none', $alarm['user']);
            $email = $identity->getDefaultFromAddress(true);
        } else {
            $email = $alarm['params']['mail']['email'];
        }

        require_once 'Horde/MIME/Mail.php';
        $mail = new MIME_Mail($alarm['title'],
                              empty($alarm['params']['mail']['body']) ? $alarm['text'] : $alarm['params']['mail']['body'],
                              $email,
                              $email,
                              NLS::getCharset());
        $mail->addHeader('Auto-Submitted', 'auto-generated');
        $mail->addHeader('X-Horde-Alarm', $alarm['title'], NLS::getCharset());
        $sent = $mail->send($GLOBALS['conf']['mailer']['type'],
                            $GLOBALS['conf']['mailer']['params']);
        if (is_a($sent, 'PEAR_Error')) {
            return $sent;
        }

        $alarm['internal']['mail']['sent'] = true;
        $this->_internal($alarm['id'], $alarm['user'], $alarm['internal']);
    }

    /**
     * Notifies about an alarm with an SMS through the sms/send API method.
     *
     * @param array $alarm  An alarm hash.
     */
    function _sms($alarm)
    {
    }

    /**
     * Returns a list of available notification methods and method parameters.
     *
     * The returned list is a hash with method names as the keys and
     * optionally associated parameters as values. The parameters are hashes
     * again with parameter names as keys and parameter information as
     * values. The parameter information is hash with the following keys:
     * 'desc' contains a parameter description; 'required' specifies whether
     * this parameter is required.
     *
     * @return array  List of methods and parameters.
     */
    function notificationMethods()
    {
        static $methods;

        if (!isset($methods)) {
            $methods = array('notify' => array(
                                 '__desc' => _("Inline Notification"),
                                 'sound' => array('type' => 'sound',
                                                  'desc' => _("Play a sound?"),
                                                  'required' => false)),
                             'popup' => array(
                                 '__desc' => _("Popup Notification")),
                             'mail' => array(
                                 '__desc' => _("Email Notification"),
                                 'email' => array('type' => 'text',
                                                  'desc' => _("Email address (optional)"),
                                                  'required' => false)));
            /*
            if ($GLOBALS['registry']->hasMethod('sms/send')) {
                $methods['sms'] = array(
                    'phone' => array('type' => 'text',
                                     'desc' => _("Cell phone number"),
                                     'required' => true));
            }
            */
        }

        return $methods;
    }

    /**
     * Garbage collects old alarms in the backend.
     */
    function gc()
    {
        /* A 1% chance we will run garbage collection during a call. */
        if (rand(0, 99) != 0) {
            return;
        }

        return $this->_gc();
    }

    /**
     * Attempts to return a concrete Horde_Alarm instance based on $driver.
     *
     * @param string $driver  The type of concrete Horde_Alarm subclass to
     *                        return. The class name is based on the storage
     *                        driver ($driver). The code is dynamically
     *                        included.
     * @param array $params   A hash containing any additional configuration
     *                        or connection parameters a subclass might need.
     *
     * @return mixed  The newly created concrete Horde_Alarm instance, or false
     *                on an error.
     */
    function factory($driver = null, $params = null)
    {
        if (is_null($driver)) {
            $driver = empty($GLOBALS['conf']['alarms']['driver']) ? 'sql' : $GLOBALS['conf']['alarms']['driver'];
        }

        $driver = basename($driver);

        if (is_null($params)) {
            $params = Horde::getDriverConfig('alarms', $driver);
        }

        $class = 'Horde_Alarm_' . $driver;
        if (!class_exists($class)) {
            include dirname(__FILE__) . '/Alarm/' . $driver . '.php';
        }
        if (class_exists($class)) {
            $alarm = new $class($params);
            $result = $alarm->initialize();
            if (is_a($result, 'PEAR_Error')) {
                $alarm = new Horde_Alarm($params, sprintf(_("The alarm backend is not currently available: %s"), $result->getMessage()));
            } else {
                $alarm->gc();
            }
        } else {
            $alarm = new Horde_Alarm($params, sprintf(_("Unable to load the definition of %s."), $class));
        }

        return $alarm;
    }

    /**
     * Converts a value from the driver's charset.
     *
     * @param mixed $value  Value to convert.
     *
     * @return mixed  Converted value.
     */
    function _fromDriver($value)
    {
        return $value;
    }

    /**
     * Converts a value to the driver's charset.
     *
     * @param mixed $value  Value to convert.
     *
     * @return mixed  Converted value.
     */
    function _toDriver($value)
    {
        return $value;
    }

    /**
     * @abstract
     */
    function _get()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _list()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _add()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _update()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _internal()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _exists()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _snooze()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _isSnoozed()
    {
        return PEAR::raiseError($this->_errormsg);
    }

    /**
     * @abstract
     */
    function _delete()
    {
        return PEAR::raiseError($this->_errormsg);
    }

}
