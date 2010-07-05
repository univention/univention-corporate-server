<?php
/**
 * IMAP access for Kolab free/busy.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Imap.php,v 1.9.2.2 2009-05-09 20:30:56 mrubinsk Exp $
 *
 * @package Kolab_FreeBusy
 */

/** We need the Kolab Stores library for connecting to the IMAP storage. */
require_once 'Horde/Kolab/Storage/List.php';

/** We need the Date library for event handling. */
require_once 'Horde/Date.php';

/** We need the Recurrence library for recurrence handling. */
require_once 'Horde/Date/Recurrence.php';

/** Event status - Taken from Kronolith*/
define('KRONOLITH_STATUS_NONE', 0);
define('KRONOLITH_STATUS_TENTATIVE', 1);
define('KRONOLITH_STATUS_CONFIRMED', 2);
define('KRONOLITH_STATUS_CANCELLED', 3);
define('KRONOLITH_STATUS_FREE', 4);

/**
 * The Horde_Kolab_Freebusy class provides a library for quickly
 * generating free/busy information from the Kolab IMAP data.
 * 
 * This class is a merged result from the Kolab free/busy package and
 * the Horde::Kronolith free/busy driver.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Imap.php,v 1.9.2.2 2009-05-09 20:30:56 mrubinsk Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_Imap {

    /**
     * Our list of Kolab server IMAP folders.
     *
     * @var Kolab_List
     */
    var $_kolab = null;

    /**
     * The folder we are generating free/busy information for.
     *
     * @var Kolab_Folder
     */
    var $_folder;

    /**
     * The link to the folder data.
     *
     * @var Kolab_Data
     */
    var $_data;

    /**
     * Is this store relevant only for users or admins?
     *
     * @var string
     */
    var $_relevance;

    /**
     * Store ACLs.
     *
     * @var string
     */
    var $_acl;

    /**
     * Store extended attributes ACL.
     *
     * @var string
     */
    var $_xacl;

    /**
     * Initialize the free/busy IMAP handler.
     */
    function Horde_Kolab_FreeBusy_Imap()
    {
        $this->_kolab = &Kolab_List::singleton();
    }

    /**
     * Connect to IMAP.
     *
     * This function has been derived from the synchronize() function
     * in the Kolab driver for Kronolith.
     *
     * @param string $folder         The folder to generate free/busy data for.
     */
    function connect($folder)
    {
        // Connect to the Kolab backend
        $this->_folder = $this->_kolab->getFolder($folder);
        if (is_a($this->_folder, 'PEAR_Error')) {
            return $this->_folder;
        }

        $this->_data = $this->_folder->getData();
        if (is_a($this->_data, 'PEAR_Error')) {
            return $this->_data;
        }
        if (!$this->_folder->exists()) {
            return PEAR::raiseError(sprintf(_("Folder %s does not exist!"), $folder));
        }
        $type = $this->_folder->getType();
        if (is_a($type, 'PEAR_Error')) {
            return $type;
        }
        if ($type != 'event') {
            return PEAR::raiseError(sprintf(_("Folder %s has type \"%s\" not \"event\"!"), 
                                            $folder, $type));
        }
    }

    /**
     * Lists all events in the time range, optionally restricting
     * results to only events with alarms.
     *
     * Taken from the Kolab driver for Kronolith.
     *
     * @param Horde_Date $startInterval  Start of range date object.
     * @param Horde_Date $endInterval    End of range data object.
     *
     * @return array  Events in the given time range.
     */
    function listEvents($startDate = null, $endDate = null)
    {
        $objects = $this->_data->getObjects();
        if (is_a($objects, 'PEAR_Error')) {
            return $objects;
        }

        if (is_null($startDate)) {
            $startDate = &new Horde_Date(array('mday' => 1, 'month' => 1, 'year' => 0000));
        }
        if (is_null($endDate)) {
            $endDate = &new Horde_Date(array('mday' => 31, 'month' => 12, 'year' => 9999));
        }
        $startts = $startDate->timestamp();
        $endts = $endDate->timestamp();

        $result = array();

        foreach($objects as $object) {
            /* check if event period intersects with given period */
            if (!(($object['start-date'] > $endts) || 
                  ($object['end-date'] < $startts))) {
                $event = &new Kolab_Event($object);
                $result[] = $event;
                continue;
            }

            /* do recurrence expansion if not keeping anyway */
            if (isset($object['recurrence'])) {
                $event = &new Kolab_Event($object);
                $next = $event->recurrence->nextRecurrence($startDate);
                while ($next !== false && 
                       $event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                    $next->mday++;
                    $next = $event->recurrence->nextRecurrence($next);
                }

                if ($next !== false) {
                    $duration = $next->timestamp() - $event->start->timestamp();
                    $next_end = &new Horde_Date($event->end->timestamp() + $duration);

                    if ((!(($endDate->compareDateTime($next) < 0) || 
                           ($startDate->compareDateTime($next_end) > 0)))) {
                        $result[] = $event;
                    }

                }
            }
        }

        return $result;
    }

    /**
     * Fetch the relevance of this calendar folder.
     *
     * @return string|PEAR_Error Relevance of this folder.
     */
    function getRelevance() {

        /* cached? */
        if (isset($this->_relevance)) {
            return $this->_relevance;
        }

        $annotation = $this->_folder->getKolabAttribute('incidences-for');
        if (is_a($annotation, 'PEAR_Error')) {
            return $annotation;
        }

        if (empty($annotation)) {
            Horde::logMessage(sprintf('No relevance value found for %s', $this->_folder->name),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_relevance = 'admins';
        } else {
            Horde::logMessage(sprintf('Relevance for %s is %s', $this->_folder->name, $annotation),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_relevance = $annotation;
        }
        return $this->_relevance;
    }

    /**
     * Fetch the ACL of this calendar folder.
     *
     * @return array|PEAR_Error IMAP ACL of this folder.
     */
    function getACL() {

        /* cached? */
        if (isset($this->_acl)) {
            return $this->_acl;
        }

        $perm = $this->_folder->getPermission();
        if (is_a($perm, 'PEAR_Error')) {
            return $perm;
        }

        $acl = &$perm->acl;
        if (empty($acl)) {
            Horde::logMessage(sprintf('No ACL found for %s', $this->_folder->name),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_acl = array();
        } else {
            Horde::logMessage(sprintf('ACL for %s is %s', 
                                      $this->_folder->name, serialize($acl)),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_acl = $acl;
        }
        return $this->_acl;
    }

    /**
     * Fetch the extended ACL of this calendar folder.
     *
     * @return array|PEAR_Error Extended ACL of this folder.
     */
    function getExtendedACL() {

        /* cached? */
        if (isset($this->_xacl)) {
            return $this->_xacl;
        }

        $annotation = $this->_folder->getXfbaccess();
        if (is_a($annotation, 'PEAR_Error')) {
            return $annotation;
        }

        if (empty($annotation)) {
            Horde::logMessage(sprintf('No extended ACL value found for %s', $this->_folder->name),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_xacl = '';
        } else {
            $annotation = join(' ', $annotation);
            Horde::logMessage(sprintf('Extended ACL for %s is %s', $this->_folder->name, $annotation),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $this->_xacl = $annotation;
        }
        return $this->_xacl;
    }

    /**
     * Generates the free/busy text for $calendar. Cache it for at least an
     * hour, as well.
     *
     * @param integer $startstamp     The start of the time period to retrieve.
     * @param integer $endstamp       The end of the time period to retrieve.
     * @param integer $fbpast         The number of days that free/busy should
     *                                be calculated for the past
     * @param integer $fbfuture       The number of days that free/busy should
     *                                be calculated for the future
     * @param string  $user           Set organizer to this user.
     * @param string  $cn             Set the common name of this user.
     *
     * @return Horde_iCalendar  The iCal object or a PEAR error.
     */
    function &generate($startstamp = null, $endstamp = null,
                       $fbpast = 0, $fbfuture = 60,
                       $user = null, $cn = null)
    {
        /* Get the iCalendar library at this point */
        require_once 'Horde/iCalendar.php';

        /* Default the start date to today. */
        if (is_null($startstamp)) {
            $month = date('n');
            $year = date('Y');
            $day = date('j');

            $startstamp = mktime(0, 0, 0, $month, $day - $fbpast, $year);
        }

        /* Default the end date to the start date + freebusy_days. */
        if (is_null($endstamp) || $endstamp < $startstamp) {
            $month = date('n');
            $year = date('Y');
            $day = date('j');

            $endstamp = mktime(0, 0, 0,
                               $month,
                               $day + $fbfuture,
                               $year);
        }

        Horde::logMessage(sprintf('Creating free/busy information from %s to %s',
                                  $startstamp, $endstamp), __FILE__, __LINE__,
                          PEAR_LOG_DEBUG);

        /* Fetch events. */
        $startDate = new Horde_Date($startstamp);
        $endDate = new Horde_Date($endstamp);
        $events = $this->listEvents($startDate, $endDate);
        if (is_a($events, 'PEAR_Error')) {
            return $events;
        }

        /* Create the new iCalendar. */
        $vCal = new Horde_iCalendar();
        $vCal->setAttribute('PRODID', '-//kolab.org//NONSGML Kolab Server 2//EN');
        $vCal->setAttribute('METHOD', 'PUBLISH');

        /* Create new vFreebusy. */
        $vFb = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
        $params = array();
        if ($cn) {
            $params['cn'] = $cn;
        }
        $vFb->setAttribute('ORGANIZER', 'MAILTO:' . $user, $params);

        $vFb->setAttribute('DTSTAMP', $_SERVER['REQUEST_TIME']);
        $vFb->setAttribute('DTSTART', $startstamp);
        $vFb->setAttribute('DTEND', $endstamp);
        // URL is not required, so out it goes...
        //$vFb->setAttribute('URL', Horde::applicationUrl('fb.php?u=' . $share->get('owner'), true, -1));

        /* Add all the busy periods. */
        foreach ($events as $event) {
            if ($event->hasStatus(KRONOLITH_STATUS_FREE)) {
                continue;
            }

            $duration = $event->end->timestamp() - $event->start->timestamp();
            $extra = array('X-UID'      => base64_encode($event->eventID),
                           'X-SUMMARY'  => base64_encode($event->private ? '' : $event->title),
                           'X-LOCATION' => base64_encode($event->private ? '' : $event->location));

            /* Make sure that we're using the current date for recurring
             * events. */
            if ($event->recurs()) {
                $startThisDay = mktime($event->start->hour,
                                       $event->start->min,
                                       $event->start->sec,
                                       date('n', $day),
                                       date('j', $day),
                                       date('Y', $day));
            } else {
                $startThisDay = $event->start->timestamp($extra);
            }
            if (!$event->recurs()) {
                $vFb->addBusyPeriod('BUSY', $startThisDay, null, $duration, $extra);
            } else {
                $next = $event->recurrence->nextRecurrence($startDate);
                while ($next) {
                    if ($endDate->compareDateTime($next) < 0) {
                        break;
                    }
                    if (!$event->recurrence->hasException($next->year, $next->month, $next->mday)) {
                        $vFb->addBusyPeriod('BUSY', $next->timestamp(), null, $duration, $extra);
                    }
                    $next->mday++;
                    $next = $event->recurrence->nextRecurrence($next);
                }
            }
        }

        /* Remove the overlaps. */
        $vFb->simplify();
        $vCal->addComponent($vFb);

        return $vCal;
    }
}

/**
 * A reduced event representation derived from the Kronolith event
 * representation.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/Imap.php,v 1.9.2.2 2009-05-09 20:30:56 mrubinsk Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_FreeBusy
 */
class Kolab_Event {

    /**
     * The driver unique identifier for this event.
     *
     * @var string
     */
    var $eventID = null;

    /**
     * The start time of the event.
     *
     * @var Horde_Date
     */
    var $start;

    /**
     * The end time of the event.
     *
     * @var Horde_Date
     */
    var $end;

    /**
     * The title of this event.
     *
     * @var string
     */
    var $title = '';

    /**
     * The location this event occurs at.
     *
     * @var string
     */
    var $location = '';

    /**
     * Whether the event is private.
     *
     * @var boolean
     */
    var $private = false;

    function Kolab_Event($event) 
    {
        $this->eventID = $event['uid'];

        $this->start = new Horde_Date($event['start-date']);
        $this->end = new Horde_Date($event['end-date']);

        if (isset($event['summary'])) {
            $this->title = $event['summary'];
        }

        if (isset($event['location'])) {
            $this->location = $event['location'];
        }

        if ($event['sensitivity'] == 'private' || $event['sensitivity'] == 'confidential') {
            $this->private = true;
        }

        if (isset($event['show-time-as'])) {
            switch ($event['show-time-as']) {
                case 'free':
                    $this->status = KRONOLITH_STATUS_FREE;
                    break;

                case 'tentative':
                    $this->status = KRONOLITH_STATUS_TENTATIVE;
                    break;

                case 'busy':
                case 'outofoffice':
                default:
                    $this->status = KRONOLITH_STATUS_CONFIRMED;
            }
        } else {
            $this->status = KRONOLITH_STATUS_CONFIRMED;
        }

        // Recurrence
        if (isset($event['recurrence'])) {
            $this->recurrence = new Horde_Date_Recurrence($this->start);
            $this->recurrence->fromHash($event['recurrence']);
        }

    }

    /**
     * Returns whether this event is a recurring event.
     *
     * @return boolean  True if this is a recurring event.
     */
    function recurs()
    {
        return isset($this->recurrence) &&
            !$this->recurrence->hasRecurType(HORDE_DATE_RECUR_NONE);
    }

    /**
     * Sets the global UID for this event.
     *
     * @param string $uid  The global UID for this event.
     */
    function setUID($uid)
    {
        $this->_uid = $uid;
    }

    /**
     * Checks whether the events status is the same as the specified value.
     *
     * @param integer $status  The status value to check against.
     *
     * @return boolean  True if the events status is the same as $status.
     */
    function hasStatus($status)
    {
        return ($status == $this->status);
    }

}
