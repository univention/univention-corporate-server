<?php
/**
 * @package Horde_Scheduler
 */

/** Date_Calc */
require_once 'Date/Calc.php';

/** Horde_Date */
require_once 'Horde/Date.php';

/** Horde_Scheduler */
require_once 'Horde/Scheduler.php';

/** Horde_Share */
require_once 'Horde/Share.php';

/** Kronolith */
require_once KRONOLITH_BASE . '/lib/Kronolith.php';

/** Kronolith_Driver */
require_once KRONOLITH_BASE . '/lib/Driver.php';

/** Horde_Date_Recurrence */
require_once KRONOLITH_BASE . '/lib/Recurrence.php';

/**
 * Horde_Scheduler_kronolith::
 *
 * Act on alarms in events and send emails/pages/etc. to users.
 *
 * $Horde: kronolith/lib/Scheduler/kronolith.php,v 1.25.6.23 2009-04-21 13:36:12 jan Exp $
 *
 * @package Horde_Scheduler
 */
class Horde_Scheduler_kronolith extends Horde_Scheduler {

    /**
     * Cache of event ids that have already been seen/had reminders sent.
     *
     * @var array
     */
    var $_seen = array();

    /**
     * The list of calendars. We store this so we're not fetching it all the
     * time, but update the cache occasionally to find new calendars.
     *
     * @var array
     */
    var $_calendars = array();

    /**
     * The last timestamp that we ran.
     *
     * @var integer
     */
    var $_runtime;

    /**
     * The last time we fetched the full calendar list.
     *
     * @var integer
     */
    var $_listtime;

    /**
     * The last time we processed agendas.
     *
     * @var integer
     */
    var $_agendatime;

    /**
     */
    function Horde_Scheduler_kronolith($params = array())
    {
        parent::Horde_Scheduler($params);

        // Load the Registry and setup conf, etc.
        $GLOBALS['registry'] = &Registry::singleton(HORDE_SESSION_NONE);
        $GLOBALS['registry']->pushApp('kronolith', false);

        // Notification instance for code that relies on it.
        $GLOBALS['notification'] = &Notification::singleton();

        // Create a share instance. This must exist in the global scope for
        // Kronolith's API calls to function properly.
        $GLOBALS['shares'] = &Horde_Share::singleton($GLOBALS['registry']->getApp());

        // Create a calendar backend object. This must exist in the global
        // scope for Kronolith's API calls to function properly.
        $GLOBALS['kronolith_driver'] = &Kronolith_Driver::factory();
    }

    /**
     */
    function run()
    {
        if (isset($_SERVER['REQUEST_TIME'])) {
            $this->_runtime = $_SERVER['REQUEST_TIME'];
        } else {
            $this->_runtime = time();
        }

        // If we haven't fetched the list of calendars in over an hour,
        // re-list to pick up any new ones.
        if ($this->_runtime - $this->_listtime > 3600) {
            $this->_listtime = $this->_runtime;
            $this->_calendars = $GLOBALS['shares']->listAllShares();
        }

        // If there are no calendars to check, we're done.
        if (!count($this->_calendars)) {
            return;
        }

        if (!empty($GLOBALS['conf']['reminder']['server_name'])) {
            $GLOBALS['conf']['server']['name'] = $GLOBALS['conf']['reminder']['server_name'];
        }

        // Send agendas every hour.
        if ($this->_runtime - $this->_agendatime >= 0) {
            $this->agenda();
        }

        // Check for alarms and act on them.
        if (!empty($GLOBALS['conf']['alarms']['driver'])) {
            return;
        }

        require_once 'Horde/Group.php';
        require_once 'Horde/Identity.php';
        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        // Retrieve a list of users associated with each calendar, and
        // thus a list of users who have used kronolith and
        // potentially have a calendar with alarms set.
        $users = array();
        $groupManager = &Group::singleton();

        foreach (array_keys($this->_calendars) as $calendarId) {
            $calendar = $GLOBALS['shares']->getShare($calendarId);
            if (is_a($calendar, 'PEAR_Error')) {
                continue;
            }
            $users = array_merge($users, $calendar->listUsers(PERMS_READ));
            $groups = $calendar->listGroups(PERMS_READ);
            foreach ($groups as $gid) {
                $group = $groupManager->getGroupById($gid);
                $users = array_merge($users, $group->listAllUsers());
            }
        }

        // Remove duplicates.
        $users = array_unique($users);

        // Loop through the users and generate reminders
        foreach ($users as $user) {
            $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                       'kronolith', $user);
            $prefs->retrieve();

            // Set the timezone.
            @putenv('TZ=' . $prefs->getValue('timezone'));

            $alarms = Kronolith::listAlarms(new Horde_Date($this->_runtime),
                                            array_keys($this->_calendars));
            foreach ($alarms as $calId => $calarms) {
                $GLOBALS['kronolith_driver']->open($calId);
                $calendar = $GLOBALS['shares']->getShare($calId);
                $perms = $GLOBALS['shares']->getPermissions($calendar, $user);
                if (!isset($perms) || ($perms & PERMS_READ) == 0) {
                    continue;
                }
                foreach ($calarms as $eventId) {
                    $event = $GLOBALS['kronolith_driver']->getEvent($eventId);
                    if (is_a($event, 'PEAR_Error')) {
                        continue;
                    }

                    if ($event->recurs()) {
                        /* Set the event's start date to the next recurrence
                         * date. This should avoid problems when an alarm
                         * triggers on a different day from the actual event,
                         * and make $seenid unique for each occurrence of a
                         * recurring event. */
                        $event->start = $event->recurrence->nextRecurrence($this->_runtime);

                        /* Check for exceptions; do nothing if one is found. */
                        if ($event->recurrence->hasException($event->start->year, $event->start->month, $event->start->mday)) {
                            continue;
                        }
                    }

                    $seenid = $eventId . $user . $event->start->timestamp() . $event->getAlarm();
                    if (!isset($this->_seen[$seenid])) {
                        $this->_seen[$seenid] = $event->start->timestamp() + ($event->durMin * 60);
                        $result = $this->remind($calId, $event, $user);
                        if (is_a($result, 'PEAR_Error')) {
                            Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                        }
                    }
                }
            }
        }

        // Discard seen ids that are now in the past (garbage collection).
        foreach (array_keys($this->_seen) as $seenid) {
            if ($this->_runtime > $this->_seen[$seenid] ||
                $this->_seen[$seenid] === true) {
                unset($this->_seen[$seenid]);
            }
        }
    }

    /**
     */
    function remind($calId, $event, $user)
    {
        if ($GLOBALS['kronolith_driver']->getCalendar() != $calId) {
            $GLOBALS['kronolith_driver']->open($calId);
        }

        /* Desired logic: list users and groups that can view $calId, and send
         * email to any of them that we can find an email address for. This
         * will hopefully be improved at some point so that people don't get
         * multiple emails, and can set more preferences on how they want to
         * be notified. */
        $share = $GLOBALS['shares']->getShare($calId);
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }

        if ($event->isPrivate() && $event->getCreatorId() != $user) {
            return false;
        }

        $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                   'kronolith', $user);
        $prefs->retrieve();
        $identity = &Identity::singleton('none', $user);
        $email = $identity->getValue('from_addr');
        if (strstr($email, '@')) {
            list($mailbox, $host) = explode('@', $email);
            $email = MIME::rfc822WriteAddress($mailbox, $host, $identity->getValue('fullname'));
        }

        $shown_calendars = unserialize($prefs->getValue('display_cals'));
        $reminder = $prefs->getValue('event_reminder');
        if (($reminder == 'owner' && $user == $share->get('owner')) ||
            ($reminder == 'show' && in_array($calId, $shown_calendars)) ||
            $reminder == 'read') {
            // Noop.
        } else {
            return false;
        }

        $lang = $prefs->getValue('language');
        $twentyFour = $prefs->getValue('twentyFour');
        $dateFormat = $prefs->getValue('date_format');

        $msg_headers = new MIME_Headers();
        $msg_headers->addMessageIdHeader();
        $msg_headers->addAgentHeader();
        $msg_headers->addHeader('Date', date('r'));
        $msg_headers->addHeader('To', 'CalendarReminders:;');
        $msg_headers->addHeader('From', $GLOBALS['conf']['reminder']['from_addr']);

        $mail_driver = $GLOBALS['conf']['mailer']['type'];
        $mail_params = $GLOBALS['conf']['mailer']['params'];
        if ($mail_driver == 'smtp' && $mail_params['auth'] &&
            empty($mail_params['username'])) {
            Horde::logMessage('Reminders don\'t work with user based SMTP authentication.', __FILE__, __LINE__, PEAR_LOG_ERR);
            return;
        }

        NLS::setLang($lang);
        NLS::setTextdomain('kronolith', KRONOLITH_BASE . '/locale', NLS::getCharset());
        String::setDefaultCharset(NLS::getCharset());

        $msg_headers->removeHeader('Subject');
        $msg_headers->addHeader('Subject', sprintf(_("Reminder: %s"), $event->title));

        $message = "\n" . sprintf(_("We would like to remind you of this upcoming event.\n\n%s\n\nLocation: %s\n\nDate: %s\nTime: %s\n\n%s"),
                                  $event->title,
                                  $event->location,
                                  strftime($dateFormat, $event->start->timestamp()),
                                  date($twentyFour ? 'H:i' : 'h:ia', $event->start->timestamp()),
                                  $event->getDescription());

        $mime = new MIME_Message();
        $body = new MIME_Part('text/plain', String::wrap($message, 76, "\n"), NLS::getCharset());

        $mime->addPart($body);
        $msg_headers->addMIMEHeaders($mime);

        Horde::logMessage(sprintf('Sending reminder for %s to %s', $event->title, $email), __FILE__, __LINE__, PEAR_LOG_DEBUG);
        $sent = $mime->send($email, $msg_headers, $mail_driver, $mail_params);
        if (is_a($sent, 'PEAR_Error')) {
            return $sent;
        }

        return true;
    }

    /**
     */
    function agenda()
    {
        // Send agenda only once per day.
        if (date('z', $this->_runtime) == date('z', $this->_agendatime)) {
            //return;
        }

        // Retrieve a list of users associated with each calendar, and
        // thus a list of users who have used kronolith and
        // potentially have an agenda preference set.
        $users = array();

        foreach (array_keys($this->_calendars) as $calendarId) {
            $calendar = $GLOBALS['shares']->getShare($calendarId);
            if (is_a($calendar, 'PEAR_Error')) {
                continue;
            }
            $users = array_merge($users, $calendar->listUsers(PERMS_READ));
        }

        // Remove duplicates.
        $users = array_unique($users);

        $runtime = new Horde_Date($this->_runtime);

        // Loop through the users and generate an agenda for them
        foreach ($users as $user) {
            $prefs = &Prefs::singleton($GLOBALS['conf']['prefs']['driver'],
                                       'kronolith', $user);
            $prefs->retrieve();
            $agenda_calendars = $prefs->getValue('daily_agenda');

            // Check if user has a timezone pref, and set it. Otherwise, make
            // sure to use the server's default timezone.
            @putenv('TZ=');
            $tz = $prefs->getValue('timezone');
            if (!empty($tz)) {
                @putenv('TZ=' . $tz);
            }

            if (!$agenda_calendars) {
                continue;
            }

            require_once 'Horde/Identity.php';
            require_once 'Horde/MIME.php';
            require_once 'Horde/MIME/Headers.php';
            require_once 'Horde/MIME/Message.php';

            // try to find an email address for the user
            $identity = &Identity::singleton('none', $user);
            $email = $identity->getValue('from_addr');
            if (strstr($email, '@')) {
                list($mailbox, $host) = explode('@', $email);
                $email = MIME::rfc822WriteAddress($mailbox, $host,
                                                  $identity->getValue('fullname'));
            }

            if (empty($email)) {
                continue;
            }

            // If we found an email address, generate the agenda.
            switch ($agenda_calendars) {
            case 'owner':
                $calendars = $GLOBALS['shares']->listShares($user, PERMS_SHOW,
                                                            $user);
                break;
            case 'read':
                $calendars = $GLOBALS['shares']->listShares($user, PERMS_SHOW,
                                                            null);
                break;
            case 'show':
            default:
                $calendars = array();
                $shown_calendars = unserialize($prefs->getValue('display_cals'));
                $cals = $GLOBALS['shares']->listShares(
                    $user, PERMS_SHOW, null);
                foreach ($cals as $calId => $cal) {
                    if (in_array($calId, $shown_calendars)) {
                        $calendars[$calId] = $cal;
                    }
                }
            }

            // Get a list of events for today
            $eventlist = array();
            foreach ($calendars as $calId => $calendar) {
                $GLOBALS['kronolith_driver']->open($calId);
                $events = $GLOBALS['kronolith_driver']->listEvents($runtime,
                                                                   $runtime);
                foreach ($events as $eventId) {
                    $event = $GLOBALS['kronolith_driver']->getEvent($eventId);
                    if (is_a($event, 'PEAR_Error')) {
                        return $event;
                    }
                    // The event list contains events starting at 12am.
                    if ($event->start->mday != $runtime->mday) {
                        continue;
                    }
                    $eventlist[$event->start->timestamp()] = $event;
                }
            }

            if (!count($eventlist)) {
                continue;
            }

            // If there are any events, generate and send the email.
            ksort($eventlist);
            $lang = $prefs->getValue('language');
            $twentyFour = $prefs->getValue('twentyFour');
            $dateFormat = $prefs->getValue('date_format');

            $msg_headers = new MIME_Headers();
            $msg_headers->addMessageIdHeader();
            $msg_headers->addAgentHeader();
            $msg_headers->addHeader('Date', date('r'));
            $msg_headers->addHeader('To', $email);
            $msg_headers->addHeader('From', $GLOBALS['conf']['reminder']['from_addr']);

            $mail_driver = $GLOBALS['conf']['mailer']['type'];
            $mail_params = $GLOBALS['conf']['mailer']['params'];
            if ($mail_driver == 'smtp' && $mail_params['auth'] &&
                empty($mail_params['username'])) {
                Horde::logMessage('Agenda Notifications don\'t work with user based SMTP authentication.',
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
                return;
            }

            NLS::setLang($lang);
            NLS::setTextdomain('kronolith', KRONOLITH_BASE . '/locale',
                               NLS::getCharset());
            String::setDefaultCharset(NLS::getCharset());
            $pad = max(String::length(_("All day")) + 2, $twentyFour ? 6 : 8);

            $msg_headers->removeHeader('Subject');
            $msg_headers->addHeader(
                'Subject',
                sprintf(_("Your daily agenda for %s"),
                        strftime($dateFormat, $this->_runtime)));

            $message = sprintf(_("Your daily agenda for %s"),
                               strftime($dateFormat, $this->_runtime))
                . "\n\n";
            foreach ($eventlist as $event) {
                if ($event->isAllDay()) {
                    $message .= str_pad(_("All day") . ':', $pad);
                } else {
                    $message .= str_pad(date($twentyFour ? 'H:i:' : 'h:ia:',
                                             $event->start->timestamp()),
                                        $pad);
                    }
                    $message .= $event->title . "\n";
            }

            $mime = new MIME_Message();
            $body = new MIME_Part('text/plain',
                                  String::wrap($message, 76, "\n"),
                                  NLS::getCharset());

            $mime->addPart($body);
            $msg_headers->addMIMEHeaders($mime);

            Horde::logMessage(sprintf('Sending daily agenda to %s', $email),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $sent = $mime->send($email, $msg_headers, $mail_driver,
                                $mail_params);
            if (is_a($sent, 'PEAR_Error')) {
                return $sent;
            }
        }

        $this->_agendatime = $this->_runtime;
    }

}
