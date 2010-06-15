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

define( 'FB_OK', 0 );
define( 'FB_TOO_OLD', 1 );
define( 'FB_PARSE_ERROR', 2 );

class FreeBusyCollector {

  function FreeBusyCollector( $organizer ) {
    $this->organizer = $organizer;
    $this->init();
  }

  function init() {
    require_once 'PEAR.php';
    require_once 'Horde/iCalendar.php';
    require_once 'Horde/MIME.php';
    require_once 'Horde/MIME/Message.php';
    require_once 'Horde/MIME/Structure.php';

    // Create the new iCalendar.
    $this->vCal = &new Horde_iCalendar();
    $this->vCal->setAttribute('PRODID', '-//proko2//freebusy 1.0//EN');
    $this->vCal->setAttribute('METHOD', 'PUBLISH');
  
    // Create new vFreebusy.
    $vFb = &Horde_iCalendar::newComponent('vfreebusy', $this->vCal);
    $vFb->setAttribute('ORGANIZER', 'MAILTO:' . $this->organizer);
  
    $vFb->setAttribute('DTSTAMP', time());
    //$vFb->setAttribute('DTSTART', $startstamp);
    //$vFb->setAttribute('DTEND', $endstamp);
    $vFb->setAttribute('URL', 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI']);
    $this->vCal->addComponent($vFb);
  }

  function addFreebusy( $text ) {
    $vCal = &new Horde_iCalendar();
    if( !$vCal->parsevCalendar($text) ) {
      trigger_error("Could not parse ical", E_USER_ERROR);
      return FB_PARSE_ERROR;
    }
    $vFb1 = &$this->vCal->findComponent( 'vfreebusy' );
    $vFb2 = &$vCal->findComponent( 'vfreebusy' );
    if( !$vFb2 ) {
      trigger_error("Could not find freebusy info in ical", E_USER_ERROR);      
      return FB_PARSE_ERROR;
    }

    if( $ets = $vFb2->getAttributeDefault( 'DTEND', false ) !== false ) {
      // PENDING(steffen): Make value configurable
      if( $ets < time() ) {
	// Not relevant anymore
	return FB_TOO_OLD;
      }
    }
    
    if( ($sts = $vFb1->getAttributeDefault('DTSTART', false)) === false ) {
      $vFb1->setAttribute('DTSTART', $vFb2->getAttribute('DTSTART'), array(), false );
    } else {
      $vFb1->setAttribute('DTSTART', min( $sts, $vFb2->getAttribute('DTSTART') ), array(), false );
    }
    if( ($ets = $vFb1->getAttributeDefault('DTEND', false)) === false ) {
      $vFb1->setAttribute('DTEND', $vFb2->getAttribute('DTEND'), array(), false );
    } else {
      $vFb1->setAttribute('DTEND', max( $ets, $vFb2->getAttribute('DTEND')), array(), false );
    }
    
    $vFb1->merge( $vFb2 );
    return FB_OK;
  }

  function exportvCalendar() {
    //$vFb->setAttribute('URL', 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['REQUEST_URI']);
    $vFb = &$this->vCal->findComponent( 'vfreebusy' );
    if( !(boolean)$vFb->getBusyPeriods() ) {
      /* No busy periods in fb list. We have to add a
       * dummy one to be standards compliant
       */
      $vFb->setAttribute('DTSTART', 0, array(), false );
      $vFb->setAttribute('DTEND', 0, array(), false );
      $vFb->setAttribute('COMMENT', 'This is a dummy vfreebusy that indicates an empty calendar');
      $vFb->addBusyPeriod( 'BUSY', 0,0, null );
    }
    return $this->vCal->exportvCalendar();
  }

  function collect( $user, &$cache ) {
    
  }

  var $organizer;
  var $vCal;
};

?>