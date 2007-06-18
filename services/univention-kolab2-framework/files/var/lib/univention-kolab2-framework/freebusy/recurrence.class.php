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

/**
 * Class for recurring event calculation
 *
 * Usage: Subclass and implement setBusy(...),
 *        Instantiate, call setter methods to fill
 *        in data, then call expand() to expand the
 *        recurrence. This will cause setBusy() to be 
 *        called for each busy period
 */
/*abstract*/ class Recurrence {

  /* public: */

  function Recurrence() {}
  function setStartDate( $ts ) { $this->initial_start = $ts; }
  function setEndDate( $ts ) { $this->initial_end = $ts; }

  function setCycletype( $ctype ) { $this->cycle_type = $ctype; }
  function setType( $type ) { $this->type = $type; }
  function setInterval( $interval ) { $this->interval = $interval; }
  function setDaynumber( $num ) { $this->daynumber = is_array($num)?$num:array($num); }
  function setDay( $day ) { $this->day = is_array($day)?$day:array($day); }
  function setMonth( $month ) { $this->month = is_array($month)?$month:array($month); }
  function setExclusionDates( $ex ) { 
    // Prescale dates for easy comparison
    $this->exclusion_dates = array();
    foreach( $ex as $e ) {
      $e = explode('-',$e);
      $e = intval(sprintf('%04d%02d%02d', $e[0],$e[1],$e[2]));
      $this->exclusion_dates[] = $e;
    } 
  }
  
  function setRangetype( $type ) { $this->range_type = $type; }
  function setRange( $range ) { $this->range = $range; }

  function ts2string($ts) {
    return gmdate("D, M d Y H:i:s",$ts).'Z';
  }
  
  function expand( $startstamp, $endstamp ) {
    myLog( 'Recurrence::expand( '.Recurrence::ts2string($startstamp).", "
	   .Recurrence::ts2string($endstamp).' ), cycletype='.$this->cycle_type, 
	   RM_LOG_DEBUG);
    switch( $this->cycle_type ) {
    case 'daily':
      $this->expand_daily( $startstamp, $endstamp );
      break;
    case 'weekly':
      $this->expand_weekly( $startstamp, $endstamp );
      break;
    case 'monthly':
      $this->expand_monthly( $startstamp, $endstamp );
      break;
    case 'yearly':
      $this->expand_yearly( $startstamp, $endstamp );
      break;
    default:
      myLog('Unknown cycletype '.$this->cycle_type, RM_LOG_ERROR);
    }
  }

  /* Abstract function, please override */
  function setBusy( $start, $end, $duration ) {
    mylog( "Warning: Abstract method Recurrence::setBusy( $start, $end, $duration ) called", RM_LOG_ERROR);
  }

  /* private: */

  function expand_daily( $startstamp, $endstamp ) {
    // Daily recurrence, every 'interval' days
    $duration = $this->initial_end-$this->initial_start;
    $count = 0;
    if( !$this->interval ) $this->interval = 1;
    for( $t = $this->initial_start; $t < $endstamp; $t = strtotime( '+'.$this->interval.' days',$t) ) {
      //myLog("Adding recurrence $t -> ".($t+$duration), RM_LOG_DEBUG );
      if( !$this->isExcluded( $t, $t+$duration) ) $this->setBusy( $t, null, $duration );
      $count++;
      if( $this->range_type == 'number' && $count > $this->range ) {
	break;
      } else if( $this->range_type == 'date' && $t > strtotime( '+1 day',$this->range ) ) {
	break;
      }
    }
  }

  function expand_weekly( $startstamp, $endstamp ) {
    // Weekly recurrence, every 'interval' weeks on 'day' days
    $duration = $this->initial_end-$this->initial_start;
    if( !$this->interval ) $this->interval = 1;
    $count = 0;
    $delta_days = (int)gmdate('w',$this->initial_start);
    for( $t =  strtotime("-$delta_days days", $this->initial_start); $t < $endstamp; 
	 $t = strtotime( '+'.$this->interval.' weeks', $t) ) {
      //myLog("t=".gmdate("D, M d Y H:i:s",$t), RM_LOG_DEBUG);
      foreach( $this->day as $day ) {
	$tmp = strtotime( '+'.$this->dayname2number($day).' days', $t);
	if( $tmp >= $this->initial_start && $tmp < $endstamp &&
	    !$this->isExcluded( $tmp, $tmp+$duration) ) {
	  myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp)." -> "
		.gmdate("D, M d Y H:i:s",$tmp+$duration), RM_LOG_DEBUG );
	  $this->setBusy( $tmp, null, $duration );
	} else {
	  break;
	}
      }
      $count++;
      if( $this->range_type == 'number' && $count > $this->range ) {
	break;
      } else if( $this->range_type == 'date' && $t > strtotime( '+1 day',$this->range ) ) {
	break;
      }	    
    }
  }

  function expand_monthly( $startstamp, $endstamp ) {
    // Weekly recurrence, every 'interval' weeks
    $duration = $this->initial_end-$this->initial_start;
    if( !$this->interval ) $this->interval = 1;
    $count = 0;
    $delta_days = (int)gmdate('d',$this->initial_start);
    myLog("initial_start=".Recurrence::ts2string($this->initial_start), RM_LOG_DEBUG);
    $offset = 0;
    $first_of_month = gmdate("M 1 Y H:i:s+0000", $this->initial_start); 
    for( $t = strtotime( $first_of_month ); 
	 $t < $endstamp; $t = strtotime( '+'.$this->interval.' months', $t)) {
      if( $this->type == 'daynumber') {
	// On numbered days
	myLog('t = '.gmdate('M d Y H:i:s',$t), RM_LOG_DEBUG);
	foreach( $this->daynumber as $dayno ) {
	  $t_month = gmdate('m',strtotime("-$offset days", $t)); 
	  $tmp = strtotime( '+'.($dayno-$offset-1).' days', $t);
	  myLog('tmp = '.gmdate('M d Y H:i:s',$tmp), RM_LOG_DEBUG);
	  $tmp_month = gmdate('m',$tmp); // make sure same month
	  if( $tmp >= $this->initial_start && $tmp < $endstamp &&
	      $t_month == $tmp_month &&
	      !$this->isExcluded( $tmp, $tmp+$duration) ) {
	    myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp)." -> "
		  .gmdate("D, M d Y H:i:s",$tmp+$duration), RM_LOG_DEBUG );
	    $this->setBusy( $tmp, null, $duration );
	  } else {
	    break;
	  }
	}
	$count++;
      } else if( $this->type == 'weekday' ) {
	// On named weekdays
	// Find beginning of first week
	$tmp = strtotime("-$offset days",$t);
	$firstday = (int)gmdate('w',$tmp);
	for( $i = 0; $i < count($this->day); $i++ ) {
	  $dayno = $this->daynumber[$i];
	  $wday  = $this->dayname2number($this->day[$i]);
	  $tmp_month = gmdate('m',$tmp); // make sure same month
	  if( $wday < $firstday ) $tmp2 = strtotime( '+'.($dayno*7+$wday-$firstday).' days', $tmp);
	  else $tmp2 = strtotime( '+'.(($dayno-1)*7+$wday-$firstday).' days', $tmp);
	  $tmp2_month = gmdate('m',$tmp2); // make sure same month
	  if( $tmp_month == $tmp2_month && $tmp2 >= $this->initial_start && $tmp2 < $endstamp 
	      && !$this->isExcluded( $tmp2, $tmp2+$duration) ) {
	    myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp2)." -> "
		  .gmdate("D, M d Y H:i:s",$tmp2+$duration), RM_LOG_DEBUG );
	    $this->setBusy( $tmp2, null, $duration );
	  } else if($tmp2 >= $endstamp ) {
	    break;
	  }
	}
	$count++;
      }
      if( $this->range_type == 'number' && $count > $this->range ) {
	break;
      } else if( $this->range_type == 'date' 
		 && strtotime('-$offset days',$t) > strtotime( '+1 day',$this->range ) ) {
	break;
      }
    }
  }

  function expand_yearly( $startstamp, $endstamp ) {
    $duration = $this->initial_end-$this->initial_start;
    if( !$this->interval ) $this->interval = 1;
    $count = 0;
    $delta_days = (int)gmdate('z',$this->initial_start);
    for( $t = strtotime( "-$delta_days days", $this->initial_start ); $t < $endstamp; 
	 $t = strtotime( '+'.$this->interval.' years', $t) ) {
      //myLog("t= ".gmdate("M d Y H:i:s",$t), RM_LOG_DEBUG );
      if( $this->type == 'yearday') {
	foreach( $this->daynumber as $dayno ) {
	  $tmp = strtotime( '+'.($dayno-1).' days', $t);
	  if( $this->initial_start <= $tmp && $tmp < $endstamp
	      && !$this->isExcluded( $tmp, $tmp+$duration) ) {
	    myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp)." -> "
		  .gmdate("D, M d Y H:i:s",$tmp+$duration), RM_LOG_DEBUG );
	    $this->setBusy( $tmp, null, $duration );
	  } else if($tmp >= $endstamp ) {
	    break;
	  }
	}
	$count++;
      } else if( $this->type == 'monthday' ) {
	for( $i = 0; $i < count($this->daynumber); $i++ ) {
	  $dayno = $this->daynumber[$i];
	  $month = $this->monthname2number($this->month[$i]);
	  $year = gmdate('Y', $t );
	  $time = gmdate('H:i:s', $t);
	  //myLog("setting tmp to $year-$month-$dayno $time+0000", RM_LOG_DEBUG );
	  $tmp =  strtotime( "$year-$month-$dayno $time+0000");
	  //myLog("tmp= ".gmdate("M d Y H:i:s",$tmp), RM_LOG_DEBUG );
	  if( $this->initial_start <= $tmp && $tmp < $endstamp 
	      && !$this->isExcluded( $tmp, $tmp+$duration) ) {
	    myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp)." -> "
		  .gmdate("D, M d Y H:i:s",$tmp+$duration), RM_LOG_DEBUG );
	    $this->setBusy( $tmp, null, $duration );	      
	  } else {
	    break;
	  }
	}
	$count++;	      
      } else if( $this->type == 'weekday' ) {
	for( $i = 0; $i < count($this->daynumber); $i++ ) {
	  $dayno = $this->daynumber[$i];
	  $wday  = $this->day[$i];
	  $month = $this->month[$i];
	  $year  = gmdate('Y',$t);
	  $time  = gmdate('H:i:s',$t);
	  $tmp = strtotime( "$dayno $wday", strtotime( "1 $month $year") );
	  $tmp = strtotime( gmdate('Y-m-d',$tmp)." $time+0000");
	  if( $this->initial_start <= $tmp && $tmp < $endstamp 
	      && !$this->isExcluded( $tmp, $tmp+$duration) ) {
	    myLog("Adding recurrence ".gmdate("D, M d Y H:i:s",$tmp)." -> "
		  .gmdate("D, M d Y H:i:s",$tmp+$duration), RM_LOG_DEBUG );
	    $this->setBusy( $tmp, null, $duration );	      
	  } else {
	    break;
	  }
	}
	$count++;
      } 
      if( $this->range_type == 'number' && $count > $this->range ) {
	break;
      } else if( $this->range_type == 'date' && $t > strtotime( '+1 day',$this->range ) ) {
	break;
      }
    }
  }

  function dayname2number( $day ) {
    switch( strtolower($day) ) {
    case 'sunday': return 0;
    case 'monday': return 1;
    case 'tuesday': return 2;
    case 'wednesday': return 3;
    case 'thursday': return 4;
    case 'friday': return 5;
    case 'saturday': return 6;
    default:
      myLog("Recurrence::dayname2number($day): Invalid day", RM_LOG_ERROR);
      return -1;
    }
  }

  function monthname2number( $month ) {
    switch( $month ) {
    case 'january':  return 1;
    case 'february': return 2;
    case 'march':    return 3;
    case 'april':    return 4;
    case 'may':      return 5;
    case 'june':     return 6;
    case 'july':     return 7;
    case 'august':   return 8;
    case 'september':return 9;
    case 'october':  return 10;
    case 'november': return 11;
    case 'december': return 12;
    default:
      myLog("Recurrence::monthname2number($month): Invalid month", RM_LOG_ERROR);
      return -1;
    }
  }

  function isExcluded( $start, $end ) {
    $start = explode(' ', gmdate('Y m d', $start));
    $start = intval($start[0].$start[1].$start[2]);

    $end = explode(' ', gmdate('Y m d', $end));
    $end = intval($end[0].$end[1].$end[2]);
    
    foreach( $this->exclusion_dates as $e ) {
      if( $start <= $e && $end >= $e ) {
	myLog("$start-$end excluded!", RM_LOG_DEBUG);	
	return true;
      }
    }
    return false;
  }

  var $initial_start   = NULL; // timestamp
  var $initial_end     = NULL; // timestamp
  var $cycle_type      = NULL; // string { 'daily', 'weekly', 'monthly', 'yearly' }
  var $type            = NULL; // string { 'daynumber', 'weekday', 'monthday', 'yearday' }
  var $interval        = NULL; // int
  var $daynumber       = NULL; // array(int)
  var $day             = NULL; // array(string)
  var $month           = NULL; // array(int)

  var $range_type      = NULL; // string { 'number', 'date' }
  var $range           = NULL; // int or timestamp

  var $exclusion_dates = array();

};
?>