<?php
/*
 *  Copyright (c) 2004 Klaraelvdalens Datakonsult AB
 *
 *    Written by Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 *
 *  This  program is free  software; you can redistribute  it and/or
 *  modify it  under the terms of the GNU  General Public License as
 *  published by the  Free Software Foundation; either version 2, or
 *  (at your option) any later version.
 *
 *  This program is  distributed in the hope that it will be useful,
 *  but WITHOUT  ANY WARRANTY; without even the  implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *  General Public License for more details.
 *
 *  You can view the  GNU General Public License, online, at the GNU
 *  Project's homepage; see <http://www.gnu.org/licenses/gpl.html>.
 */

require_once '/var/lib/univention-kolab2-framework/freebusy/recurrence.class.php';
require_once '/var/lib/univention-kolab2-framework/freebusy/domxml-php4-to-php5.php';

class FreeBusyRecurrence extends Recurrence {
  function FreeBusyRecurrence( &$vfb, &$extra ) {
    $this->vfb =& $vfb;
    $this->extra =& $extra;
  }

  function setBusy( $start, $end, $duration ) {
    $this->vfb->addBusyPeriod('BUSY', $start, null, $duration, $this->extra);
  }

  var $vfb;
  var $extra;
};

class FreeBusy {
  function FreeBusy( $username, 
		     $password, 
		     $imaphost,
		     $fbfuture=60,
		     $fbpast=0 ) {
    $this->username = $username;
    $this->password = $password;
    $this->imaphost = $imaphost;
    $this->fbfuture = $fbfuture;
    $this->fbpast   = $fbpast;
  }

  function imapConnect() {
    require_once('Net/IMAP.php');
    $this->imap = &new Net_IMAP( $this->imaphost, $this->imapport );
    #$this->imap->setDebug(true);
    return $this->imap;
  }

  function imapDisconnect() {
    return $this->imap->disconnect();
  }

  function imapLogin() {
    myLog("imap login: ".$this->username."-".$this->password, RM_LOG_DEBUG);
    return $this->imap->login($this->username,$this->password, false, false);
  }

  function imapOpenMailbox($foldername = 'INBOX') {
    $this->foldername = $foldername;
    $rc = $this->imap->selectMailbox( $foldername );
    $a  = $this->imap->getAnnotation( '/vendor/kolab/folder-type', '*' );
    //myLog( "$folder has annotation: ".print_r($a,true), RM_LOG_DEBUG);
    return $rc;
  }

  function getACL() {
    return $this->imap->getACL();
  }

  function getRelevance() {
    $val = $this->imap->getAnnotation( '/vendor/kolab/incidences-for', 'value.shared' );
    if( PEAR::isError($val) || empty($val) ) {
      myLog("No /vendor/kolab/incidences-for found for ".$this->foldername, RM_LOG_DEBUG);
      return 'admins';
    } else {
      myLog("/vendor/kolab/incidences-for = ".print_r($val,true)." for ".$this->foldername, RM_LOG_DEBUG);
      return $val;
    }
  }

  function &generateFreeBusy($startstamp = NULL, $endstamp = NULL ) {
  
    require_once 'PEAR.php';
    require_once 'Horde/iCalendar.php';
    require_once 'Horde/MIME.php';
    require_once 'Horde/MIME/Message.php';
    require_once 'Horde/MIME/Structure.php';
  
    // Default the start date to today.
    if (is_null($startstamp)) {
      $month = date('n');
      $year = date('Y');
      $day = date('j');
    
      $startstamp = strtotime( '-'.$this->fbpast.' days', mktime(0, 0, 0, $month, $day, $year) );
    }
  
    // Default the end date to the start date + freebusy_days.
    if (is_null($endstamp) || $endstamp < $startstamp) {
      $endstamp = strtotime( '+'.$this->fbfuture.' days', $startstamp );
    }

    myLog("Creating pfb from $startstamp to $endstamp", RM_LOG_DEBUG);
  
    // Create the new iCalendar.
    $vCal = &new Horde_iCalendar();
    $vCal->setAttribute('PRODID', '-//proko2//freebusy 1.0//EN');
    $vCal->setAttribute('METHOD', 'PUBLISH');
  
    // Create new vFreebusy.
    $vFb = &Horde_iCalendar::newComponent('vfreebusy', $vCal);
    $vFb->setAttribute('ORGANIZER', 'MAILTO:' . $this->username);
  
    $vFb->setAttribute('DTSTAMP', time());
    $vFb->setAttribute('DTSTART', $startstamp);
    $vFb->setAttribute('DTEND', $endstamp);
    // URL is not required, so out it goes...
    //$vFb->setAttribute('URL', 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI']);
  
    if( $this->imap->getNumberOfMessages() == 0 ) {
      $vFb->setAttribute('DTSTART', 0, array(), false );
      $vFb->setAttribute('DTEND', 0, array(), false );
      $vFb->setAttribute('COMMENT', 'This is a dummy vfreebusy that indicates an empty calendar');
      /* It seems to be a bad idea to put bogus values in pfbs
       * so we accept that they are not completely in line 
       * with the rfc and take care of the problem when merging 
       * pfbs to ifbs later 
       */
      //$vFb->addBusyPeriod( 'BUSY', 0,0, null );
      $vCal->addComponent($vFb);
      return array($vCal->exportvCalendar(),$vCal->exportvCalendar());
    }
	myLog("Reading messagelist", RM_LOG_DEBUG);
	$getMessages_start = microtime_float();
	$msglist = &$this->imap->getMessagesList();
	//$msglist = &$this->imap->getMessages();
	myLog("FreeBusy::imap->getMessagesList() took ".(microtime_float()-$getMessages_start)." secs.", RM_LOG_DEBUG);
    if( PEAR::isError( $msglist ) ) return array( $msglist, null);
	foreach ($msglist as $msginfo) {
	  //myLog("Reading message ".$msginfo['msg_id'], RM_LOG_DEBUG);
	  $textmsg = &$this->imap->getMsg($msginfo['msg_id']);
      $mimemsg = &MIME_Structure::parseTextMIMEMessage($textmsg);
    
      // Read in a Kolab event object, if one exists
      $parts = $mimemsg->contentTypeMap();
      $event = false;
      foreach ($parts as $mimeid => $conttype) {
	if ($conttype == 'application/x-vnd.kolab.event') {
	  $part = $mimemsg->getPart($mimeid);
	  $part->transferDecodeContents();
	  $event = $this->getEventHash($part->getContents());
	  if ($event === false) {
	    myLog("No x-vnd.kolab.event in ".$part->getContents(), RM_LOG_DEBUG);
	    continue;
	  }
	}
      }
    
      if ($event === false) {
	myLog("No x-vnd.kolab.events at all ", RM_LOG_DEBUG);
	continue;
      }
      
      $uid = $event['uid'];
      /*
      // See if we need to ignore this event
      if (isset($params['ignore'][$uid])) {
	trigger_error("Ignoring event with uid=$uid", E_USER_NOTICE);
	continue;
      }
      */

      if( array_key_exists( 'show-time-as', $event ) && 
	  strtolower(trim($event['show-time-as'])) == 'free' ) {
	continue;
      }
    
      $summary = ($event['sensitivity'] == 'public' ? $event['summary'] : '');
    
      //myLog("Looking at message with uid=$uid and summary=$summary", RM_LOG_DEBUG);
    
      // Get the events initial start
      $initial_start = $event['start-date'];
      $initial_end = $event['end-date'];
      if( $event['allday'] ) {
	$initial_end = strtotime( '+1 day', $initial_start );
	myLog("Detected all-day event $uid", RM_LOG_DEBUG);
      }
      $extra = array( 'X-UID'     => base64_encode($uid) );
      if (!empty($summary)) {
	$extra['X-SUMMARY'] = base64_encode($summary);
      }
      if( !empty($event['scheduling-id']) ) {
	$extra['X-SID'] = base64_encode($event['scheduling-id']);
      }

      if( array_key_exists( 'recurrence', $event ) ) {	
	myLog("Detected recurring event $uid", RM_LOG_DEBUG);
	$rec = $event['recurrence'];
	$recurrence =& new FreeBusyRecurrence( $vFb, $extra );
	$recurrence->setStartDate( $initial_start );
	$recurrence->setEndDate( $initial_end );
	$recurrence->setCycletype( $rec['cycle'] );
	if( isset($rec['type']) ) $recurrence->setType( $rec['type'] );
	if( isset($rec['interval']) ) $recurrence->setInterval( (int)$rec['interval'] );
	if( isset($rec['daynumber']) ) $recurrence->setDaynumber( $rec['daynumber'] );
	if( isset($rec['day']) ) $recurrence->setDay( $rec['day'] );
	if( isset($rec['month']) ) $recurrence->setMonth( $rec['month'] );
	if( isset($rec['exclusion'] ) ) $recurrence->setExclusionDates( $rec['exclusion'] );
	$rangetype = $rec['rangetype'];
	if( $rangetype == 'number' ) {
	  $range = (int)$rec['range'];
	} else if( $rangetype == 'date' ) {
	  $range = $this->parseDateTime( $rec['range'] );
	} else {
	  $range = false;
	}
	$recurrence->setRangetype( $rangetype );
	$recurrence->setRange( $range );
	$recurrence->expand( $startstamp, $endstamp );
      } else {
	// Normal event
    
	// Don't bother adding the initial event if it's outside our free/busy window
	if ($initial_start < $startstamp || $initial_end > $endstamp) {
	  continue;
	}
		
	$vFb->addBusyPeriod('BUSY', $initial_start/* + FreeBusy::tzOffset($initial_start)*/, 
			    $initial_end/* + FreeBusy::tzOffset($initial_end)*/, null, $extra);
      }
    }
  
    $xvCal = $vCal;
    $xvCal->addComponent($vFb);
    $vCal->addComponent($this->clearExtra($vFb));
  
    // Generate the vCal file.
    // return array( $vCal->exportvCalendar(), $xvCal->exportvCalendar() );
    $ret = array( $vCal->exportvCalendar(), $xvCal->exportvCalendar() );
    return $ret;
  }

  /********************** Private API below this line ********************/

  function tzOffset( $ts ) {
    $dstr = date('O',$ts);
    return 3600 * substr( $dstr, 0, 3) + 60 * substr( $dstr, 3, 2);
  }

  // static function to compute foldername for imap
  function imapFolderName( $user, $owner, $folder = false, $default_domain = false ) {
    $userdom = false;
    $ownerdom = false;
    if( ereg( '(.*)@(.*)', $user, $regs ) ) {
      // Regular user
      $user = $regs[1];
      $userdom  = $regs[2];
    } else {
      // Domainless user (ie. manager)
    }

    if( ereg( '(.*)@(.*)', $owner, $regs ) ) {      
      $owner = $regs[1];
      $ownerdom = $regs[2];
    } else {
    }

    $fldrcomp = array('user',$owner );
    if( $folder ) $fldrcomp[] = $folder;
    $fldr = join('/', $fldrcomp );
    if( $ownerdom && !$userdom ) $fldr .= '@'.$ownerdom;
    return $fldr;
  }

  // Date/Time value parsing, courtesy of the Horde iCalendar library
  function parseTime($text) {
    // There must be a trailing 'Z' on a time
    if (strlen($text) != 9) {
      return false;
    }

    $time['hour']  = intval(substr($text, 0, 2));
    $time['minute'] = intval(substr($text, 3, 2));
    $time['second']  = intval(substr($text, 6, 2));
    return $time;
  }

  function parseDate($text) {
    if (strlen($text) != 10) {
      return false;
    }
    
    $date['year']  = intval(substr($text, 0, 4));
    $date['month'] = intval(substr($text, 5, 2));
    $date['mday']  = intval(substr($text, 8, 2));
    
    return $date;
  }

  function parseDateTime($text) {
    $dateParts = split('T', $text);
    if (count($dateParts) != 2 && !empty($text)) {
      // Not a datetime field but may be just a date field.
      if (!$date = FreeBusy::parseDate($text)) {
	return $date;
      }
      return @gmmktime(0, 0, 0, $date['month'], $date['mday'], $date['year']);
    }
    
    if (!$date = FreeBusy::parseDate($dateParts[0])) {
      return $date;
    }
    if (!$time = FreeBusy::parseTime($dateParts[1])) {
      return $time;
    }
    
    return @gmmktime($time['hour'], $time['minute'], $time['second'],
                     $date['month'], $date['mday'], $date['year']);
  }

  function getEventHash($xml_text) {
    $xmldoc = @domxml_open_mem($xml_text, DOMXML_LOAD_PARSING +
			       DOMXML_LOAD_COMPLETE_ATTRS + DOMXML_LOAD_SUBSTITUTE_ENTITIES +
			       DOMXML_LOAD_DONT_KEEP_BLANKS, $error);
    
    if (!empty($error)) {
      // There were errors parsing the XML data - abort
      myLog( "Error parsing \"$xml_txt\": $error", RM_LOG_ERROR);
      return false;
    }
    
    $noderoot = $xmldoc->document_element();
    $childnodes = $noderoot->child_nodes();
    
    $event_hash = array();
    
    // Build the event hash
    foreach ($childnodes as $value) {
      //myLog("Looking at tag ".($value->tagname), RM_LOG_DEBUG);
      if( $value->tagname == 'recurrence' ) {
	$rhash = array();
	$attrs = $value->attributes();
	foreach( $attrs as $attr ) {
	  //myLog("getEventHash setting rhash[".$attr->name."] = ".$attr->value, RM_LOG_DEBUG);
	  $rhash[$attr->name] = $attr->value;
	}
	foreach( $value->child_nodes() as $v ) {
	  if( $v->tagname == 'day' || $v->tagname == 'exclusion' ) {
	    $rhash[$v->tagname][] = $v->get_content();
	  } else {
	    $rhash[$v->tagname] = $v->get_content();
	    if( $v->tagname == 'range' && $v->has_attribute('type') ) {
	      $rhash['rangetype'] = $v->get_attribute('type');
	    }
	  }
	}	
	$event_hash[$value->tagname] = $rhash;
      } else {
	$event_hash[$value->tagname] = $value->get_content();
      }
    }
    
    //myLog("RAW Event: ".print_r($event_hash, true), RM_LOG_DEBUG);

    // Perform some sanity checks on the event
    if (
        empty($event_hash['uid']) ||
        empty($event_hash['start-date']) ||
        empty($event_hash['end-date'])
	) {
      return false;
    }
    

    if (empty($event_hash['sensitivity'])) {
      $event_hash['sensitivity'] = 'public';
    }
    
    // Set the summary if it's not present, so we don't get PHP warnings
    // about accessing non-present keys
    if (empty($event_hash['summary'])) {
      $event_hash['summary'] = '';
    }
    
    // Convert our date-time values to timestamps
    if( strpos( $event_hash['start-date'], 'T' ) === false &&
	strpos( $event_hash['end-date'], 'T' ) === false &&
	$event_hash['start-date'] == $event_hash['end-date'] ) {
      $event_hash['allday'] = true;
    } else {
      $event_hash['allday'] = false;      
    }
    $event_hash['start-date'] = FreeBusy::parseDateTime($event_hash['start-date']);
    $event_hash['end-date'] = FreeBusy::parseDateTime($event_hash['end-date']);
    
    return $event_hash;
  }

  function clearExtra( $vFb ) {
    $vFb->_extraParams = array();
    return $vFb;
  }
 
  var $username;
  var $password;
  var $imaphost;
  var $imapport = 143;
  var $foldername;

  // Settings
  var $fbfuture;
  var $fbpast;
  var $default_domain = 'foo';
  var $week_starts_on_sunday = false;

  var $imap;
};

?>
