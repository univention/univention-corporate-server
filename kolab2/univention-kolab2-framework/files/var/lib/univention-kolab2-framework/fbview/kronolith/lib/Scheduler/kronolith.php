<?php
/**
 * Horde_Scheduler_kronolith::
 *
 * Act on alarms in events and send emails/pages/etc. to users.
 *
 * $Horde: kronolith/lib/Scheduler/kronolith.php,v 1.17 2004/05/20 04:06:14 chuck Exp $
 *
 * @package Horde_Scheduler
 */
class Horde_Scheduler_kronolith extends Horde_Scheduler {

    /**
     * Cache of event ids that have already been seen/had reminders
     * sent.
     * @var array $_seen
     */
    var $_seen = array();

    /**
     * The list of calendars. We store this so we're not fetching it
     * all the time, but update the cache occasionally to find new
     * calendars.
     * @var array $_calendars
     */
    var $_calendars = array();

    /**
     * Cache email address so that we don't spend too much time
     * looking them up always. Maybe have to expire this at some
     * point?
     * @var array $_emails
     */
    var $_emails = array();

    /**
     * The last timestamp that we ran.
     * @var integer $_runtime
     */
    var $_runtime;

    /**
     * The last time we fetched the full calendar list.
     * @var integer $_listtime
     */
    var $_listtime;

    function Horde_Scheduler_kronolith($params = array())
    {
        parent::Horde_Scheduler($params);
    }

    function run()
    {
        $this->_runtime = time();

        // If we haven't fetched the list of calendars in over an
        // hour, re-list to pick up any new ones.
        if ($this->_runtime - $this->_listtime > 3600) {
            global $shares;

            $this->_listtime = $this->_runtime;
            $this->_calendars = $shares->listAllShares();
        }

        // If there are no calendars to monitor, just return.
        if (!count($this->_calendars)) {
            return;
        }

        // Check for alarms and act on them.
        $today = date('Ymd');
        $alarms = Kronolith::listAlarms(Kronolith::timestampToObject($this->_runtime), array_keys($this->_calendars));
        foreach ($alarms as $calId => $calarms) {
            foreach ($calarms as $eventId) {
                $seenid = $today . $eventId;
                if (!isset($this->_seen[$seenid])) {
                    $this->_seen[$seenid] = true;
                    $result = $this->remind($calId, $eventId);
                    if (is_a($result, 'PEAR_Error')) {
                        Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
                    }
                }
            }
        }
    }

    function remind($calId, $eventId)
    {
        global $kronolith, $conf, $shares;

        if ($kronolith->getCalendar() != $calId) {
            $kronolith->open($calId);
        }
        $event = &$kronolith->getEvent($eventId);

        // Check for exceptions; do nothing if one is found.
        if ($event->hasException(date('Y'), date('n'), date('j'))) {
            return;
        }

        require_once 'Horde/Group.php';
        require_once 'Horde/Identity.php';
        require_once 'Horde/Text.php';
        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        /* Desired logic: list users and groups that can view $calId,
         * and send email to any of them that we can find an email
         * address for. This will hopefully be improved at some point
         * so that people don't get multiple emails, and can set more
         * preferences on how they want to be notified. */
        $share = $shares->getShare($calId);
        if (is_a($share, 'PEAR_Error')) {
            return;
        }

        $recipients = array();

        $users = $share->listUsers(PERMS_READ);
        foreach ($users as $user) {
            if (empty($this->_emails[$user])) {
                $identity = &Identity::factory('none', $user);
                $email = $identity->getValue('from_addr');
                if (strstr($email, '@')) {
                    list($mailbox, $host) = explode('@', $email);
                    $this->_emails[$user] = MIME::rfc822WriteAddress($mailbox, $host, $identity->getValue('fullname'));
                }
            }

            if (!empty($this->_emails[$user])) {
                $recipients[] = $this->_emails[$user];
            }
        }

        $groups = $share->listGroups(PERMS_READ);
        $groupManager = &Group::singleton();
        foreach ($groups as $gid) {
            if (empty($this->_emails[$gid])) {
                $group = $groupManager->getGroupById($gid);
                if ($email = $group->get('email')) {
                    $this->_emails[$gid] = $group->get('email');
                }
            }

            if (!empty($this->_emails[$gid])) {
                $recipients[] = $this->_emails[$gid];
            }
        }

        $msg_headers = &new MIME_Headers();
        $msg_headers->addMessageIdHeader();
        $msg_headers->addAgentHeader();
        $msg_headers->addHeader('Date', date('r'));
        $msg_headers->addHeader('To', 'CalendarReminders:;');
        $msg_headers->addHeader('From', 'CalendarDaemon@' . $conf['server']['name']);
        $msg_headers->addHeader('Subject', sprintf(_("Reminder: %s"), $event->title));

        $message = "\n" . sprintf(_("You requested to be reminded about %s, which is at %s."), $event->title, date('H:i', $event->getStartTimestamp())) . "\n\n" . $event->getDescription();

        $mime = &new MIME_Message();
        $body = &new MIME_Part('text/plain', Text::wrap($message, 76, "\n"));

        $mime->addPart($body);
        $msg_headers->addMIMEHeaders($mime);

        if (!count($recipients)) {
            Horde::logMessage(sprintf('No email addresses available to send reminder for %s to recipient(s): %s %s', $event->title, implode(', ', $users), implode(', ', $groups)), __FILE__, __LINE__, PEAR_LOG_INFO);
            return false;
        } else {
            Horde::logMessage(sprintf('Sending reminder for %s to %s', $event->title, implode(', ', $recipients)), __FILE__, __LINE__, PEAR_LOG_DEBUG);
            return $mime->send(implode(', ', $recipients), $msg_headers);
        }
    }

}
