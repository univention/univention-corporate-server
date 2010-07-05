<?php
/**
 * Resource management for the Kolab server.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Resource.php,v 1.15.2.11 2009-12-03 14:20:55 wrobel Exp $
 *
 * PHP version 4
 *
 * @category Kolab
 * @package  Kolab_Filter
 * @author   Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author   Gunnar Wrobel <wrobel@pardus.de>
 * @license  http://www.fsf.org/copyleft/lgpl.html LGPL
 * @link     http://pear.horde.org/index.php?package=Kolab_Server
 */

/** Load the iCal handling */
require_once 'Horde/iCalendar.php';

/** Load MIME handlers */
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Part.php';
require_once 'Horde/MIME/Structure.php';

require_once 'Horde/String.php';
String::setDefaultCharset('utf-8');

// What actions we can take when receiving an event request
define('RM_ACT_ALWAYS_ACCEPT',              'ACT_ALWAYS_ACCEPT');
define('RM_ACT_REJECT_IF_CONFLICTS',        'ACT_REJECT_IF_CONFLICTS');
define('RM_ACT_MANUAL_IF_CONFLICTS',        'ACT_MANUAL_IF_CONFLICTS');
define('RM_ACT_MANUAL',                     'ACT_MANUAL');
define('RM_ACT_ALWAYS_REJECT',              'ACT_ALWAYS_REJECT');

// What possible ITIP notification we can send
define('RM_ITIP_DECLINE',                   1);
define('RM_ITIP_ACCEPT',                    2);
define('RM_ITIP_TENTATIVE',                 3);

/**
 * Provides Kolab resource handling
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Resource.php,v 1.15.2.11 2009-12-03 14:20:55 wrobel Exp $
 *
 * Copyright 2004-2009 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @package Kolab_Filter
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 */
class Kolab_Resource
{

    /**
     * Returns the resource policy applying for the given sender
     *
     * @param string $sender   The sender address
     * @param string $resource The resource
     *
     * @return array|PEAR_Error An array with "cn", "home server" and the policy.
     */
    function _getResourceData($sender, $resource)
    {
        require_once 'Horde/Kolab/Server.php';
        $db = &Horde_Kolab_Server::singleton();
        if (is_a($db, 'PEAR_Error')) {
            $db->code = OUT_LOG | EX_SOFTWARE;
            return $db;
        }

        $dn = $db->uidForMail($resource, KOLAB_SERVER_RESULT_MANY);
        if (is_a($dn, 'PEAR_Error')) {
            $dn->code = OUT_LOG | EX_NOUSER;
            return $dn;
        }
        if (is_array($dn && count($dn) > 1)) {
            Horde::logMessage(sprintf("%s objects returned for %s",
                                      $count($dn), $resource),
                              __FILE__, __LINE__, PEAR_LOG_WARNING);
            return false;
        }
        $user = $db->fetch($dn, KOLAB_OBJECT_USER);

        $cn      = $user->get(KOLAB_ATTR_CN);
        $id      = $user->get(KOLAB_ATTR_MAIL);
        $hs      = $user->get(KOLAB_ATTR_HOMESERVER);
        if (is_a($hs, 'PEAR_Error')) {
            return $hs;
        }
        $hs      = strtolower($hs);
        $actions = $user->get(KOLAB_ATTR_IPOLICY);
        if (is_a($actions, 'PEAR_Error')) {
            $actions->code = OUT_LOG | EX_UNAVAILABLE;
            return $actions;
        }
        if ($actions === false) {
            $actions = array(RM_ACT_MANUAL);
        }

        $policies = array();
        $defaultpolicy = false;
        foreach ($actions as $action) {
            if (ereg('(.*):(.*)', $action, $regs)) {
                $policies[strtolower($regs[1])] = $regs[2];
            } else {
                $defaultpolicy = $action;
            }
        }
        // Find sender's policy
        if (array_key_exists($sender, $policies)) {
            // We have an exact match, stop processing
            $action = $policies[$sender];
        } else {
            $action = false;
            $dn = $db->uidForMailOrAlias($sender);
            if (is_a($dn, 'PEAR_Error')) {
                $dn->code = OUT_LOG | EX_NOUSER;
                return $dn;
            }
            if ($dn) {
                // Sender is local, check for groups
                foreach ($policies as $gid => $policy) {
                    if ($db->memberOfGroupAddress($dn, $gid)) {
                        // User is member of group
                        if (!$action) {
                            $action = $policy;
                        } else {
                            $action = min($action, $policy);
                        }
                    }
                }
            }
            if (!$action && $defaultpolicy) {
                $action = $defaultpolicy;
            }
        }
        return array('cn' => $cn, 'id' => $id,
                     'homeserver' => $hs, 'action' => $action);
    }

    function &_getICal($filename)
    {
        $requestText = '';
        $handle = fopen($filename, 'r');
        while (!feof($handle)) {
            $requestText .= fread($handle, 8192);
        }

        $mime = &MIME_Structure::parseTextMIMEMessage($requestText);

        $parts = $mime->contentTypeMap();
        foreach ($parts as $mimeid => $conttype) {
            if ($conttype == 'text/calendar') {
                $part = $mime->getPart($mimeid);

                $iCalendar = &new Horde_iCalendar();
                $iCalendar->parsevCalendar($part->transferDecode());

                return $iCalendar;
            }
        }
        // No iCal found
        return false;
    }

    function _imapConnect($id)
    {
        global $conf;

        // Handle virtual domains
        list($user, $domain) = split('@', $id);
        if (empty($domain)) {
            $domain = $conf['kolab']['filter']['email_domain'];
        }
        $calendar_user = $conf['kolab']['filter']['calendar_id'] . '@' . $domain;

        /* Load the authentication libraries */
        require_once "Horde/Auth.php";
        require_once 'Horde/Secret.php';

        $auth = &Auth::singleton(isset($conf['auth']['driver'])?$conf['auth']['driver']:'kolab');
        $authenticated = $auth->authenticate($calendar_user,
                                             array('password' => $conf['kolab']['filter']['calendar_pass']),
                                             false);

        if (is_a($authenticated, 'PEAR_Error')) {
            $authenticated->code = OUT_LOG | EX_UNAVAILABLE;
            return $authenticated;
        }
        if (!$authenticated) {
            return PEAR::raiseError(sprintf('Failed to authenticate as calendar user: %s',
                                            $auth->getLogoutReasonString()),
                                    OUT_LOG | EX_UNAVAILABLE);
        }
        @session_start();
        $_SESSION['__auth'] = array(
            'authenticated' => true,
            'userId' => $calendar_user,
            'timestamp' => time(),
            'credentials' => Secret::write(Secret::getKey('auth'),
                                           serialize(array('password' => $conf['kolab']['filter']['calendar_pass']))),
            'remote_addr' => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : null,
        );

        /* Kolab IMAP handling */
        require_once 'Horde/Kolab/Storage/List.php';
        $list = &Kolab_List::singleton();
        $default = $list->getForeignDefault($id, 'event');
        if (!$default || is_a($default, 'PEAR_Error')) {
            $default = &new Kolab_Folder();
            $default->setList($list);
            $default->setName($conf['kolab']['filter']['calendar_store']);
            //FIXME: The calendar user needs access here
            $attributes = array('default' => true,
                                'type' => 'event',
                                'owner' => $id);
            $result = $default->save($attributes);
            if (is_a($result, 'PEAR_Error')) {
                $result->code = OUT_LOG | EX_UNAVAILABLE;
                return $result;
            }
        }
        return $default;
    }

    function _objectFromItip(&$itip)
    {
        $object = array();
        $object['uid'] = $itip->getAttributeDefault('UID', '');

        $org_params = $itip->getAttribute('ORGANIZER', true);
        if (!is_a( $org_params, 'PEAR_Error')) {
            if (!empty($org_params[0]['CN'])) {
                $object['organizer']['display-name'] = $org_params[0]['CN'];
            }
            $orgemail = $itip->getAttributeDefault('ORGANIZER', '');
            if (eregi('mailto:(.*)', $orgemail, $regs )) {
                $orgemail = $regs[1];
            }
            $object['organizer']['smtp-address'] = $orgemail;
        }
        $object['summary'] = $itip->getAttributeDefault('SUMMARY', '');
        $object['location'] = $itip->getAttributeDefault('LOCATION', '');
        $object['body'] = $itip->getAttributeDefault('DESCRIPTION', '');
        $dtend = $itip->getAttributeDefault('DTEND', '');
        if (is_array($dtend)) {
            $object['_is_all_day'] = true;
        }
        $object['start-date'] = $this->convert2epoch($itip->getAttributeDefault('DTSTART', ''));
        $object['end-date'] = $this->convert2epoch($dtend);

        $attendees = $itip->getAttribute('ATTENDEE');
        if (!is_a( $attendees, 'PEAR_Error')) {
            $attendees_params = $itip->getAttribute('ATTENDEE', true);
            if (!is_array($attendees)) {
                $attendees = array($attendees);
            }
            if (!is_array($attendees_params)) {
                $attendees_params = array($attendees_params);
            }

            $object['attendee'] = array();
            for ($i = 0; $i < count($attendees); $i++) {
                $attendee = array();
                if (isset($attendees_params[$i]['CN'])) {
                    $attendee['display-name'] = $attendees_params[$i]['CN'];
                }

                $attendeeemail = $attendees[$i];
                if (eregi('mailto:(.*)', $attendeeemail, $regs)) {
                    $attendeeemail = $regs[1];
                }
                $attendee['smtp-address'] = $attendeeemail;

                if( $attendees_params[$i]['RSVP'] == 'FALSE' ) {
                    $attendee['request-response'] = false;
                } else {
                    $attendee['request-response'] = true;
                }

                if (isset($attendees_params[$i]['ROLE'])) {
                    $attendee['role'] = $attendees_params[$i]['ROLE'];
                }

                if (isset($attendees_params[$i]['PARTSTAT'])) {
                    $status = strtolower($attendees_params[$i]['PARTSTAT']);
                    switch ($status) {
                    case 'needs-action':
                    case 'delegated':
                        $attendee['status'] = 'none';
                        break;
                    default:
                        $attendee['status'] = $status;
                        break;
                    }
                }

                $object['attendee'][] = $attendee;
            }
        }

        // Alarm
        $valarm = $itip->findComponent('VALARM');
        if ($valarm) {
            $trigger = $valarm->getAttribute('TRIGGER');
            if (!is_a($trigger, 'PEAR_Error')) {
                $p = $valarm->getAttribute('TRIGGER', true);
                if ($trigger < 0) {
                    // All OK, enter the alarm into the XML
                    // NOTE: The Kolab XML format seems underspecified
                    // wrt. alarms currently...
                    $object['alarm'] = -$trigger / 60;
                }
            } else {
                Horde::logMessage('No TRIGGER in VALARM. ' . $trigger->getMessage(),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        // Recurrence
        $rrule_str = $itip->getAttribute('RRULE');
        if (!is_a($rrule_str, 'PEAR_Error')) {
            require_once 'Horde/Date/Recurrence.php';
            $recurrence = &new Horde_Date_Recurrence(time());
            $recurrence->fromRRule20($rrule_str);
            $object['recurrence'] = $recurrence->toHash();
        }

        Horde::logMessage(sprintf('Assembled event object: %s',
                                  print_r($object, true)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        return $object;
    }

    function handleMessage($fqhostname, $sender, $resource, $tmpfname)
    {
        global $conf;

        $rdata = $this->_getResourceData($sender, $resource);
        if (is_a($rdata, 'PEAR_Error')) {
            return $rdata;
        } else if ($rdata === false) {
            /* No data, probably not a local user */
            return true;
        } else if ($rdata['homeserver'] && $rdata['homeserver'] != $fqhostname) {
            /* Not the users homeserver, ignore */
            return true;
        }

        $cn = $rdata['cn'];
        $id = $rdata['id'];
        if (isset($rdata['action'])) {
            $action = $rdata['action'];
        } else {
            // Manual is the only safe default!
            $action = RM_ACT_MANUAL;
        }
        Horde::logMessage(sprintf('Action for %s is %s',
                                  $sender, $action),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Get out as early as possible if manual
        if ($action == RM_ACT_MANUAL) {
            Horde::logMessage(sprintf('Passing through message to %s', $id),
                              __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;
        }

        /* Get the iCalendar data (i.e. the iTip request) */
        $iCalendar = &$this->_getICal($tmpfname);
        if ($iCalendar === false) {
            // No iCal in mail
            Horde::logMessage(sprintf('Could not parse iCalendar data, passing through to %s', $id),
                              __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;
        }
        // Get the event details out of the iTip request
        $itip = &$iCalendar->findComponent('VEVENT');
        if ($itip === false) {
            Horde::logMessage(sprintf('No VEVENT found in iCalendar data, passing through to %s', $id),
                              __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;
        }

        // What is the request's method? i.e. should we create a new event/cancel an
        // existing event, etc.
        $method = strtoupper($iCalendar->getAttributeDefault('METHOD',
                                                             $itip->getAttributeDefault('METHOD', 'REQUEST')));

        // What resource are we managing?
        Horde::logMessage(sprintf('Processing %s method for %s', $method, $id),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // This is assumed to be constant across event creation/modification/deletipn
        $uid = $itip->getAttributeDefault('UID', '');
        Horde::logMessage(sprintf('Event has UID %s', $uid),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Who is the organiser?
        $organiser = preg_replace('/^mailto:\s*/i', '', $itip->getAttributeDefault('ORGANIZER', ''));
        Horde::logMessage(sprintf('Request made by %s', $organiser),
                      __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // What is the events summary?
        $summary = $itip->getAttributeDefault('SUMMARY', '');

        $dtstart = $this->convert2epoch($itip->getAttributeDefault('DTSTART', 0));
        $dtend = $this->convert2epoch($itip->getAttributeDefault('DTEND', 0));

        Horde::logMessage(sprintf('Event starts on <%s> %s and ends on <%s> %s.',
                                  $dtstart, $this->iCalDate2Kolab($dtstart), $dtend, $this->iCalDate2Kolab($dtend)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        if ($action == RM_ACT_ALWAYS_REJECT) {
            if ($method == 'REQUEST') {
                Horde::logMessage(sprintf('Rejecting %s method', $method),
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
                $this->sendITipReply($cn, $resource, $itip, RM_ITIP_DECLINE,
                                     $organiser, $uid, $is_update);
                return false;
            } else {
                Horde::logMessage(sprintf('Passing through %s method for ACT_ALWAYS_REJECT policy', $method),
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
                return true;
            }
        }

        $is_update  = false;
        $imap_error = false;
        $ignore     = array();

        $folder = $this->_imapConnect($id);
        if (is_a($folder, 'PEAR_Error')) {
            $imap_error = &$folder;
        }
        if (!is_a($imap_error, 'PEAR_Error') && !$folder->exists()) {
            $imap_error = &PEAR::raiseError('Error, could not open calendar folder!',
                                    OUT_LOG | EX_TEMPFAIL);
        }

        if (!is_a($imap_error, 'PEAR_Error')) {
            $data = $folder->getData();
            if (is_a($data, 'PEAR_Error')) {
                $imap_error = &$data;
            }
        }

        if (is_a($imap_error, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed accessing IMAP calendar: %s',
                                      $folder->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            if ($action == RM_ACT_MANUAL_IF_CONFLICTS) {
                return true;
            }
        }

        switch ($method) {
        case 'REQUEST':
            if ($action == RM_ACT_MANUAL) {
                Horde::logMessage(sprintf('Passing through %s method', $method),
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
                break;
            }

            if (is_a($imap_error, 'PEAR_Error') || !$data->objectUidExists($uid)) {
                $old_uid = null;
            } else {
                $old_uid = $uid;
                $ignore[] = $uid;
                $is_update = true;
            }

            /** Generate the Kolab object */
            $object = $this->_objectFromItip($itip);

            $outofperiod=0;

            // Don't even bother checking free/busy info if RM_ACT_ALWAYS_ACCEPT
            // is specified
            if ($action != RM_ACT_ALWAYS_ACCEPT) {

                /**
                 * FIXME: This is a temporary injection point for providing a mock
                 * free/busy setup. It would be better to implement a suite of
                 * different free/busy drivers.
                 */
                if (isset($GLOBALS['KOLAB_FILTER_TESTING'])) {
                    $vfb = $GLOBALS['KOLAB_FILTER_TESTING'];
                } else {
                    $vfb = &$this->internalGetFreeBusy($resource);
                    if (is_a($vfb, 'PEAR_Error')) {
                        return $vfb;
                    }
                }

                $vfbstart = $vfb->getAttributeDefault('DTSTART', 0);
                $vfbend = $vfb->getAttributeDefault('DTEND', 0);
                Horde::logMessage(sprintf('Free/busy info starts on <%s> %s and ends on <%s> %s',
                                          $vfbstart, $this->iCalDate2Kolab($vfbstart), $vfbend, $this->iCalDate2Kolab($vfbend)),
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);

                if ($vfbstart && $dtstart > $this->convert2epoch ($vfbend)) {
                    $outofperiod=1;
                } else {
                    // Check whether we are busy or not
                    $busyperiods = $vfb->getBusyPeriods();
                    Horde::logMessage(sprintf('Busyperiods: %s',
                                              print_r($busyperiods, true)),
                                      __FILE__, __LINE__, PEAR_LOG_DEBUG);
                    $extraparams = $vfb->getExtraParams();
                    Horde::logMessage(sprintf('Extraparams: %s',
                                              print_r($extraparams, true)),
                                      __FILE__, __LINE__, PEAR_LOG_DEBUG);
                    $conflict = false;
                    if (!empty($object['recurrence'])) {
                        $recurrence = &new Horde_Date_Recurrence(time());
                        $recurrence->fromHash($object['recurrence']);
                        $duration = $dtend - $dtstart;
                        $events = array();
                        $next_start = $vfbstart;
                        $next = $recurrence->nextActiveRecurrence($vfbstart);
                        while ($next !== false && $next->compareDate($vfbend) <= 0) {
                            $next_ts = $next->timestamp();
                            $events[$next_ts] = $next_ts + $duration;
                            $next = $recurrence->nextActiveRecurrence(array('year' => $next->year,
                                                                            'month' => $next->month,
                                                                            'mday' => $next->mday + 1,
                                                                            'hour' => $next->hour,
                                                                            'min' => $next->min,
                                                                            'sec' => $next->sec));
                        }
                    } else {
                        $events = array($dtstart => $dtend);
                    }

                    foreach ($events as $dtstart => $dtend) {
                        foreach ($busyperiods as $busyfrom => $busyto) {
                            if (empty($busyfrom) && empty($busyto)) {
                                continue;
                            }
                            Horde::logMessage(sprintf('Busy period from %s to %s',
                                                      strftime('%a, %d %b %Y %H:%M:%S %z', $busyfrom),
                                                      strftime('%a, %d %b %Y %H:%M:%S %z', $busyto)
                                              ),
                                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
                            if ((isset($extraparams[$busyfrom]['X-UID'])
                                 && in_array(base64_decode($extraparams[$busyfrom]['X-UID']), $ignore))
                                || (isset($extraparams[$busyfrom]['X-SID'])
                                    && in_array(base64_decode($extraparams[$busyfrom]['X-SID']), $ignore))) {
                                // Ignore
                                continue;
                            }
                            if (($busyfrom >= $dtstart && $busyfrom < $dtend) || ($dtstart >= $busyfrom && $dtstart < $busyto)) {
                                Horde::logMessage('Request overlaps',
                                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);
                                $conflict = true;
                                break;
                            }
                        }
                        if ($conflict) {
                            break;
                        }
                    }

                    if ($conflict) {
                        if ($action == RM_ACT_MANUAL_IF_CONFLICTS) {
                            //sendITipReply(RM_ITIP_TENTATIVE);
                            Horde::logMessage('Conflict detected; Passing mail through',
                                              __FILE__, __LINE__, PEAR_LOG_INFO);
                            return true;
                        } else if ($action == RM_ACT_REJECT_IF_CONFLICTS) {
                            Horde::logMessage('Conflict detected; rejecting',
                                              __FILE__, __LINE__, PEAR_LOG_INFO);
                            $this->sendITipReply($cn, $id, $itip, RM_ITIP_DECLINE,
                                                 $organiser, $uid, $is_update);
                            return false;
                        }
                    }
                }
            }

            if (is_a($imap_error, 'PEAR_Error')) {
                Horde::logMessage('Could not access users calendar; rejecting',
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
                $this->sendITipReply($cn, $id, $itip, RM_ITIP_DECLINE,
                                     $organiser, $uid, $is_update);
                return false;
            }

            // At this point there was either no conflict or RM_ACT_ALWAYS_ACCEPT
            // was specified; either way we add the new event & send an 'ACCEPT'
            // iTip reply

            Horde::logMessage(sprintf('Adding event %s', $uid),
                              __FILE__, __LINE__, PEAR_LOG_INFO);

            if (!empty($conf['kolab']['filter']['simple_locks'])) {
                if (!empty($conf['kolab']['filter']['simple_locks_timeout'])) {
                    $timeout = $conf['kolab']['filter']['simple_locks_timeout'];
                } else {
                    $timeout = 60;
                }
                if (!empty($conf['kolab']['filter']['simple_locks_dir'])) {
                    $lockdir = $conf['kolab']['filter']['simple_locks_dir'];
                } else {
                    $lockdir = Horde::getTempDir() . '/Kolab_Filter_locks';
                    if (!is_dir($lockdir)) {
                        mkdir($lockdir, 0700);
                    }
                }
                if (is_dir($lockdir)) {
                    $lockfile = $lockdir . '/' . $resource . '.lock';
                    $counter = 0;
                    while ($counter < $timeout && @file_get_contents($lockfile) == 'LOCKED') {
                        sleep(1);
                        $counter++;
                    }
                    if ($counter == $timeout) {
                        Horde::logMessage(sprintf('Lock timeout of %s seconds exceeded. Rejecting invitation.', $timeout),
                                          __FILE__, __LINE__, PEAR_LOG_ERR);
                        $this->sendITipReply($cn, $id, $itip, RM_ITIP_DECLINE,
                                             $organiser, $uid, $is_update);
                        return false;
                    }
                    $result = file_put_contents($lockfile, 'LOCKED');
                    if ($result === false) {
                        Horde::logMessage(sprintf('Failed creating lock file %s.', $lockfile),
                                          __FILE__, __LINE__, PEAR_LOG_ERR);
                    } else {
                        $this->lockfile = $lockfile;
                    }
                } else {
                    Horde::logMessage(sprintf('The lock directory %s is missing. Disabled locking.', $lockdir),
                                      __FILE__, __LINE__, PEAR_LOG_ERR);
                }
            }

            $result = $data->save($object, $old_uid);
            if (is_a($result, 'PEAR_Error')) {
                $result->code = OUT_LOG | EX_UNAVAILABLE;
                return $result;
            }

            // Update our status within the iTip request and send the reply
            $itip->setAttribute('STATUS', 'CONFIRMED', array(), false);
            $attendees = $itip->getAttribute('ATTENDEE');
            if (!is_array($attendees)) {
                $attendees = array($attendees);
            }
            $attparams = $itip->getAttribute('ATTENDEE', true);
            foreach ($attendees as $i => $attendee) {
                $attendee = preg_replace('/^mailto:\s*/i', '', $attendee);
                if ($attendee != $resource) {
                    continue;
                }

                $attparams[$i]['PARTSTAT'] = 'ACCEPTED';
                if (array_key_exists('RSVP', $attparams[$i])) {
                    unset($attparams[$i]['RSVP']);
                }
            }

            // Re-add all the attendees to the event, using our updates status info
            $firstatt = array_pop($attendees);
            $firstattparams = array_pop($attparams);
            $itip->setAttribute('ATTENDEE', $firstatt, $firstattparams, false);
            foreach ($attendees as $i => $attendee) {
                $itip->setAttribute('ATTENDEE', $attendee, $attparams[$i]);
            }

            if ($outofperiod) {
                $this->sendITipReply($cn, $resource, $itip, RM_ITIP_TENTATIVE,
                                     $organiser, $uid, $is_update);
                Horde::logMessage('No freebusy information available',
                                  __FILE__, __LINE__, PEAR_LOG_NOTICE);
            } else {
                $this->sendITipReply($cn, $resource, $itip, RM_ITIP_ACCEPT,
                                     $organiser, $uid, $is_update);
            }
            return false;

        case 'CANCEL':
            Horde::logMessage(sprintf('Removing event %s', $uid),
                              __FILE__, __LINE__, PEAR_LOG_INFO);

            if (is_a($imap_error, 'PEAR_Error')) {
                $body = sprintf(_("Unable to access %s's calendar:"), $resource) . "\n\n" . $summary;
                $subject = sprintf(_("Error processing \"%s\""), $summary);
            } else if (!$data->objectUidExists($uid)) {
                Horde::logMessage(sprintf('Canceled event %s is not present in %s\'s calendar',
                                          $uid, $resource),
                                  __FILE__, __LINE__, PEAR_LOG_WARNING);
                $body = sprintf(_("The following event that was canceled is not present in %s's calendar:"), $resource) . "\n\n" . $summary;
                $subject = sprintf(_("Error processing \"%s\""), $summary);
            } else {
                /**
                 * Delete the messages from IMAP
                 * Delete any old events that we updated
                 */
                Horde::logMessage(sprintf('Deleting %s because of cancel',
                                          $uid),
                                  __FILE__, __LINE__, PEAR_LOG_DEBUG);

                $result = $data->delete($uid);
                if (is_a($result, 'PEAR_Error')) {
                    Horde::logMessage(sprintf('Deleting %s failed with %s',
                                              $uid, $result->getMessage()),
                                      __FILE__, __LINE__, PEAR_LOG_DEBUG);
                }

                $body = _("The following event has been successfully removed:") . "\n\n" . $summary;
                $subject = sprintf(_("%s has been cancelled"), $summary);
            }

            Horde::logMessage(sprintf('Sending confirmation of cancelation to %s', $organiser),
                              __FILE__, __LINE__, PEAR_LOG_WARNING);

            $body = &new MIME_Part('text/plain', String::wrap($body, 76, "\n", 'utf-8'), 'utf-8');
            $mime = &MIME_Message::convertMimePart($body);
            $mime->setTransferEncoding('quoted-printable');
            $mime->transferEncodeContents();

            // Build the reply headers.
            $msg_headers = &new MIME_Headers();
            $msg_headers->addHeader('Date', date('r'));
            $msg_headers->addHeader('From', $resource);
            $msg_headers->addHeader('To', $organiser);
            $msg_headers->addHeader('Subject', $subject);
            $msg_headers->addMIMEHeaders($mime);

            // Send the reply.
            static $mailer;

            if (!isset($mailer)) {
                require_once 'Mail.php';
                $mailer = &Mail::factory('SMTP', array('auth' => false));
            }

            $msg = $mime->toString();
            if (is_object($msg_headers)) {
                $headerArray = $mime->encode($msg_headers->toArray(), 'UTF-8');
            } else {
                $headerArray = $mime->encode($msg_headers, 'UTF-8');
            }

            /* Make sure the message has a trailing newline. */
            if (substr($msg, -1) != "\n") {
                $msg .= "\n";
            }

            $status = $mailer->send(MIME::encodeAddress($organiser), $headerArray, $msg);

            //$status = $mime->send($organiser, $msg_headers);
            if (is_a($status, 'PEAR_Error')) {
                return PEAR::raiseError('Unable to send cancellation reply: ' . $status->getMessage(),
                                        OUT_LOG | EX_TEMPFAIL);
            } else {
                Horde::logMessage('Successfully sent cancellation reply',
                                  __FILE__, __LINE__, PEAR_LOG_INFO);
            }

            return false;;

        default:
            // We either don't currently handle these iTip methods, or they do not
            // apply to what we're trying to accomplish here
            Horde::logMessage(sprintf('Ignoring %s method and passing message through to %s',
                                      $method, $resource),
                              __FILE__, __LINE__, PEAR_LOG_INFO);
            return true;
        }
    }

    /**
     * Helper function to clean up after handling an invitation
     *
     * @return NULL
     */
    function cleanup()
    {
        if (!empty($this->lockfile)) {
            @unlink($this->lockfile);
            if (file_exists($this->lockfile)) {
                Horde::logMessage(sprintf('Failed removing the lockfile %s.', $lockfile),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
            }
            $this->lockfile = null;
        }
    }

    /**
     * Helper function to assemble a free/busy uri.
     *
     * @param array $parsed  The set of parameters that may influence the URI.
     *
     * @return mixed The assembled URI or false.
     */
    function assembleUri($parsed)
    {
        if (!is_array($parsed)) {
            return false;
        }

        $uri = empty($parsed['scheme']) ? '' :
            $parsed['scheme'] . ':' . ((strtolower($parsed['scheme']) == 'mailto') ? '' : '//');

        $uri .= empty($parsed['user']) ? '' :
            ($parsed['user']) . (empty($parsed['pass']) ? '' :
                                 ':'.($parsed['pass'])) . '@';

        $uri .= empty($parsed['host']) ? '' : $parsed['host'];
        $uri .= empty($parsed['port']) ? '' : ':' . $parsed['port'];
        $uri .= empty($parsed['path']) ? '' : $parsed['path'];
        $uri .= empty($parsed['query']) ? '' : '?' . $parsed['query'];
        $uri .= empty($parsed['anchor']) ? '' : '#' . $parsed['anchor'];

        return $uri;
    }

    /**
     * Retrieve Free/Busy information for the specified resource via
     * the given URL.
     *
     * @param string $resource  The name of the resource.
     *
     * @return Horde_iCalendar_vfreebusy|PEAR_Error The free/busy information.
     */
    function &internalGetFreeBusy($email)
    {
        global $conf;

        $server = Horde_Kolab_Server::singleton();
        $uid = $server->uidForMailAddress($email);
        if (is_a($uid, 'PEAR_Error')) {
            $uid->code = OUT_LOG | EX_UNAVAILABLE;
            return $uid;
        }

        $user_object = $server->fetch($uid);
        if (is_a($user_object, 'PEAR_Error')) {
            $user_object->code = OUT_LOG | EX_UNAVAILABLE;
            return $user_object;
        }

        $server = $user_object->getServer('freebusy');
        if (is_a($server, 'PEAR_Error')) {
            $server->code = OUT_LOG | EX_UNAVAILABLE;
            return $server;
        }

        $fb_url = sprintf('%s/%s.xfb', $server, $email);

        Horde::logMessage(sprintf('URL = %s', $fb_url), __FILE__, __LINE__, PEAR_LOG_DEBUG);

        $parsed = parse_url($fb_url);

        list($user, $domain) = split('@', $email);
        if (empty($domain)) {
            $domain = $conf['kolab']['filter']['email_domain'];
        }

        $options['method'] = 'GET';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
            $options = array_merge($options, $GLOBALS['conf']['http']['proxy']);
        }

        require_once 'HTTP/Request.php';
        $http = new HTTP_Request($fb_url, $options);
        $http->setBasicAuth($conf['kolab']['filter']['calendar_id'] . '@' . $domain,
                            $conf['kolab']['filter']['calendar_pass']);
        @$http->sendRequest();
        if ($http->getResponseCode() != 200) {
            return PEAR::raiseError(sprintf('Unable to retrieve free/busy information for %s',
                                            $email),
                                    OUT_LOG | EX_UNAVAILABLE);
        }
        $vfb_text = $http->getResponseBody();

        $iCal = new Horde_iCalendar;
        $iCal->parsevCalendar($vfb_text);

        $vfb = &$iCal->findComponent('VFREEBUSY');

        if ($vfb === false) {
            return PEAR::raiseError(sprintf('Invalid or no free/busy information available for %s',
                                            $resource),
                                    OUT_LOG | EX_UNAVAILABLE);
        }
        $vfb->simplify();

        return $vfb;
    }

    /**
     * Send an automated reply.
     *
     * @param string  $cn                     Common name to be used in the iTip
     *                                        response.
     * @param string  $resource               Resource we send the reply for.
     * @param string  $Horde_iCalendar_vevent The iTip information.
     * @param int     $type                   Type of response.
     * @param string  $organiser              The event organiser.
     * @param string  $uid                    The UID of the event.
     * @param boolean $is_update              Is this an event update?
     */
    function sendITipReply($cn, $resource, $itip, $type = RM_ITIP_ACCEPT,
                           $organiser, $uid, $is_update)
    {
        Horde::logMessage(sprintf('sendITipReply(%s, %s, %s, %s)',
                                  $cn, $resource, get_class($itip), $type),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // Build the reply.
        $vCal = &new Horde_iCalendar();
        $vCal->setAttribute('PRODID', '-//kolab.org//NONSGML Kolab Server 2//EN');
        $vCal->setAttribute('METHOD', 'REPLY');

        $summary = _('No summary available');

        $itip_reply =& Horde_iCalendar::newComponent('VEVENT', $vCal);
        $itip_reply->setAttribute('UID', $uid);
        if (!is_a($itip->getAttribute('SUMMARY'), 'PEAR_error')) {
            $itip_reply->setAttribute('SUMMARY', $itip->getAttribute('SUMMARY'));
            $summary = $itip->getAttribute('SUMMARY');
        }
        if (!is_a($itip->getAttribute('DESCRIPTION'), 'PEAR_error')) {
            $itip_reply->setAttribute('DESCRIPTION', $itip->getAttribute('DESCRIPTION'));
        }
        if (!is_a($itip->getAttribute('LOCATION'), 'PEAR_error')) {
            $itip_reply->setAttribute('LOCATION', $itip->getAttribute('LOCATION'));
        }
        $itip_reply->setAttribute('DTSTART', $itip->getAttribute('DTSTART'), array_pop($itip->getAttribute('DTSTART', true)));
        if (!is_a($itip->getAttribute('DTEND'), 'PEAR_error')) {
            $itip_reply->setAttribute('DTEND', $itip->getAttribute('DTEND'), array_pop($itip->getAttribute('DTEND', true)));
        } else {
            $itip_reply->setAttribute('DURATION', $itip->getAttribute('DURATION'), array_pop($itip->getAttribute('DURATION', true)));
        }
        if (!is_a($itip->getAttribute('SEQUENCE'), 'PEAR_error')) {
            $itip_reply->setAttribute('SEQUENCE', $itip->getAttribute('SEQUENCE'));
        } else {
            $itip_reply->setAttribute('SEQUENCE', 0);
        }
        $itip_reply->setAttribute('ORGANIZER', $itip->getAttribute('ORGANIZER'), array_pop($itip->getAttribute('ORGANIZER', true)));

        // Let's try and remove this code and just create
        // the ATTENDEE stuff in the reply from scratch
        //     $attendees = $itip->getAttribute( 'ATTENDEE' );
        //     if( !is_array( $attendees ) ) {
        //       $attendees = array( $attendees );
        //     }
        //     $params = $itip->getAttribute( 'ATTENDEE', true );
        //     for( $i = 0; $i < count($attendees); $i++ ) {
        //       $attendee = preg_replace('/^mailto:\s*/i', '', $attendees[$i]);
        //       if ($attendee != $resource) {
        //	continue;
        //       }
        //       $params = $params[$i];
        //       break;
        //     }

        $params = array();
        $params['CN'] = $cn;
        switch ($type) {
        case RM_ITIP_DECLINE:
            Horde::logMessage(sprintf('Sending DECLINE iTip reply to %s',
                                      $organiser),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $message = $is_update
                ? sprintf(_("%s has declined the update to the following event:"), $resource) . "\n\n" . $summary
                : sprintf(_("%s has declined the invitation to the following event:"), $resource) . "\n\n" . $summary;
            $subject = _("Declined: ") . $summary;
            $params['PARTSTAT'] = 'DECLINED';
            break;

        case RM_ITIP_ACCEPT:
            Horde::logMessage(sprintf('Sending ACCEPT iTip reply to %s', $organiser),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $message = $is_update
                ? sprintf(_("%s has accepted the update to the following event:"), $resource) . "\n\n" . $summary
                : sprintf(_("%s has accepted the invitation to the following event:"), $resource) . "\n\n" . $summary;
            $subject = _("Accepted: ") . $summary;
            $params['PARTSTAT'] = 'ACCEPTED';
            break;

        case RM_ITIP_TENTATIVE:
            Horde::logMessage(sprintf('Sending TENTATIVE iTip reply to %s', $organiser),
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
            $message = $is_update
                ? sprintf(_("%s has tentatively accepted the update to the following event:"), $resource) . "\n\n" . $summary
                : sprintf(_("%s has tentatively accepted the invitation to the following event:"), $resource) . "\n\n" . $summary;
            $subject = _("Tentative: ") . $summary;
            $params['PARTSTAT'] = 'TENTATIVE';
            break;

        default:
            Horde::logMessage(sprintf('Unknown iTip method (%s passed to sendITipReply())', $type),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        $itip_reply->setAttribute('ATTENDEE', 'MAILTO:' . $resource, $params);
        $vCal->addComponent($itip_reply);

        $ics = &new MIME_Part('text/calendar', $vCal->exportvCalendar(), 'UTF-8' );
        //$ics->setName('event-reply.ics');
        $ics->setContentTypeParameter('method', 'REPLY');

        //$mime->addPart($body);
        //$mime->addPart($ics);
        // The following was ::convertMimePart($mime). This was removed so that we
        // send out single-part MIME replies that have the iTip file as the body,
        // with the correct mime-type header set, etc. The reason we want to do this
        // is so that Outlook interprets the messages as it does Outlook-generated
        // responses, i.e. double-clicking a reply will automatically update your
        // meetings, showing different status icons in the UI, etc.
        $mime = &MIME_Message::convertMimePart($ics);
        $mime->setCharset('UTF-8');
        $mime->setTransferEncoding('quoted-printable');
        $mime->transferEncodeContents();

        // Build the reply headers.
        $msg_headers = &new MIME_Headers();
        $msg_headers->addHeader('Date', date('r'));
        $msg_headers->addHeader('From', "$cn <$resource>");
        $msg_headers->addHeader('To', $organiser);
        $msg_headers->addHeader('Subject', $subject);
        $msg_headers->addMIMEHeaders($mime);

        // Send the reply.
        static $mailer;

        if (!isset($mailer)) {
            require_once 'Mail.php';
            $mailer = &Mail::factory('SMTP', array('auth' => false));
        }

        $msg = $mime->toString();
        if (is_object($msg_headers)) {
            $headerArray = $mime->encode($msg_headers->toArray(), $mime->getCharset());
        } else {
            $headerArray = $mime->encode($msg_headers, $mime->getCharset());
        }

        /* Make sure the message has a trailing newline. */
        if (substr($msg, -1) != "\n") {
            $msg .= "\n";
        }

        $status = $mailer->send(MIME::encodeAddress($organiser), $headerArray, $msg);

        //$status = $mime->send($organiser, $msg_headers);
        if (is_a($status, 'PEAR_Error')) {
            Horde::logMessage('Unable to send iTip reply: %s' . $status->getMessage(),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            Horde::logMessage('Successfully sent iTip reply',
                              __FILE__, __LINE__, PEAR_LOG_DEBUG);
        }
    }


    /**
     * Clear information from a date array.
     *
     * @param array $ical_date  The array to clear.
     *
     * @return array The cleaned array.
     */
    function cleanArray($ical_date)
    {
        if (array_key_exists('hour', $ical_date)) {
            $temp['hour']   = array_key_exists('hour', $ical_date) ? $ical_date['hour'] :  '00';
            $temp['minute']   = array_key_exists('minute', $ical_date) ? $ical_date['minute'] :  '00';
            $temp['second']   = array_key_exists('second', $ical_date) ? $ical_date['second'] :  '00';
            $temp['zone']   = array_key_exists('zone', $ical_date) ? $ical_date['zone'] :  'UTC';
        } else {
            $temp['DATE'] = '1';
        }
        $temp['year']   = array_key_exists('year', $ical_date) ? $ical_date['year'] :  '0000';
        $temp['month']   = array_key_exists('month', $ical_date) ? $ical_date['month'] :  '00';
        $temp['mday']   = array_key_exists('mday', $ical_date) ? $ical_date['mday'] :  '00';

        return $temp;
    }

    /**
     * Conveert iCal dates to Kolab format.
     *
     * An all day event must have a dd--mm-yyyy notation and not a
     * yyyy-dd-mmT00:00:00z notation Otherwise the event is shown as a
     * 2-day event --> do not try to convert everything to epoch first
     *
     * @param array  $ical_date  The array to convert.
     * @param string $type       The type of the date to convert.
     *
     * @return string The converted date.
     */
    function iCalDate2Kolab($ical_date, $type= ' ')
    {
        Horde::logMessage(sprintf('Converting to kolab format %s',
                                  print_r($ical_date, true)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        // $ical_date should be a timestamp
        if (is_array($ical_date)) {
            // going to create date again
            $temp = $this->cleanArray($ical_date);
            if (array_key_exists('DATE', $temp)) {
                if ($type == 'ENDDATE') {
                    // substract a day (86400 seconds) using epochs to take number of days per month into account
                    $epoch= $this->convert2epoch($temp) - 86400;
                    $date = gmstrftime('%Y-%m-%d', $epoch);
                } else {
                    $date= sprintf('%04d-%02d-%02d', $temp['year'], $temp['month'], $temp['mday']);
                }
            } else {
                $time = sprintf('%02d:%02d:%02d', $temp['hour'], $temp['minute'], $temp['second']);
                if ($temp['zone'] == 'UTC') {
                    $time .= 'Z';
                }
                $date = sprintf('%04d-%02d-%02d', $temp['year'], $temp['month'], $temp['mday']) . 'T' . $time;
            }
        }  else {
            $date = gmstrftime('%Y-%m-%dT%H:%M:%SZ', $ical_date);
        }
        Horde::logMessage(sprintf('To <%s>', $date),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return $date;
    }

    /**
     * Convert a date to an epoch.
     *
     * @param array  $values  The array to convert.
     *
     * @return int Time.
     */
    function convert2epoch($values)
    {
        Horde::logMessage(sprintf('Converting to epoch %s',
                                  print_r($values, true)),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);

        if (is_array($values)) {
            $temp = $this->cleanArray($values);
            $epoch = gmmktime($temp['hour'], $temp['minute'], $temp['second'],
                              $temp['month'], $temp['mday'], $temp['year']);
        } else {
            $epoch=$values;
        }

        Horde::logMessage(sprintf('Converted <%s>', $epoch),
                          __FILE__, __LINE__, PEAR_LOG_DEBUG);
        return $epoch;
    }
}
