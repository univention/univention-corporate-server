<?php
/*
 *  Copyright (c) 2005 Klaraelvdalens Datakonsult AB
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

class KolabMailTransport {
  function KolabMailTransport( $host = '127.0.0.1', $port = 2003, $uid='', $pass='', $mech='PLAIN' ) {
    $this->host = $host;
    $this->port = $port;
    $this->uid = $uid;
    $this->pass = $pass;
    $this->mech = $mech;
    $this->transport = false;
  }

  /*abstract*/ function createTransport() { 
    myLog("Abstract method KolabMailTransport::createTransport() called!", RM_LOG_ERROR);
  }

  function start($sender,$recips) {
    $this->createTransport();
    $myclass = get_class($this->transport);
    $this->got_newline = true;

    if (!$this->transport) {
      return new PEAR_Error('Failed to connect to $myclass: ' . $error->getMessage(), 421);
    }
    if (PEAR::isError($error = $this->transport->connect())) {
      return new PEAR_Error('Failed to connect to $myclass: ' . $error->getMessage(), 421);
    }
    if ($this->uid != '' ) {
    if (PEAR::isError($error = $this->transport->auth($this->uid, $this->pass, $this->mech))) {
      return new PEAR_Error("Failed to connect to $myclass: " . $error->getMessage(), 421);
    }
    }

    if (PEAR::isError($error = $this->transport->mailFrom($sender))) {
      $resp = $this->transport->getResponse();
      return new PEAR_Error('Failed to set sender: ' . $resp[1], $resp[0] );
    }
    
    if( !is_array( $recips ) ) $recips = array($recips);

    $reciperrors = array();
    foreach( $recips as $recip ) {
      if (PEAR::isError($error = $this->transport->rcptTo($recip))) {
	$resp = $this->transport->getResponse();
	$msg = "Failed to set recipient $recip: " .$resp[1]. ", code=".$resp[0];
        myLog($msg, RM_LOG_ERROR);
        $reciperrors[] = new PEAR_Error('Failed to set recipient: '.$resp[1], $resp[0]);
      }
    }
	if( count($reciperrors) == count($recips) ) {
	  // OK, all failed, just give up
	  if( count($reciperrors) == 1 ) {
		// Only one failure, just return that
		return $reciperrors[0];
	  }
	  // Multiple errors
	  return $this->createErrorObject( $reciperrors, 'Delivery to all recipients failed' );
	}

    if (PEAR::isError($error = $this->transport->_put('DATA'))) {      
      return $error;
    }
    if (PEAR::isError($error = $this->transport->_parseResponse(354))) {
      return $error;
    }
    return true;
  }

  // Encapsulate multiple errors in one
  function createErrorObject( $reciperrors, $msg = null ) {
	// Return the lowest errorcode to not bounce more
	// than we have to
	if($msg == null) $msg = 'Delivery to recipients failed.';
	$code = 1000;
	foreach( $reciperrors as $err ) {
	  if( $err->code < $code ) $code = $err->code;
	}
	return new PEAR_Error( $msg, $code, null, null, $reciperrors);	
  }

  /* Modified implementation from Net_SMTP that supports
   * dotstuffing even when getting the mail line-by line */
  function quotedataline(&$data) {
    /*
     * Change Unix (\n) and Mac (\r) linefeeds into Internet-standard CRLF
     * (\r\n) linefeeds.
     */
    $data = preg_replace(array('/(?<!\r)\n/','/\r(?!\n)/'), "\r\n", $data);
    
    /*
     * Because a single leading period (.) signifies an end to the data,
     * legitimate leading periods need to be "doubled" (e.g. '..').
     */
    if( $this->got_newline && $data[0] == '.' ) $data = '.'.$data;
    $data = str_replace("\n.", "\n..", $data);
    $len = strlen($data);
    if( $len > 0 )
        $this->got_newline = ( $data[$len-1] == "\n" );
  }

  function data( $data) {
    $this->quotedataline($data);
    if (PEAR::isError($this->transport->_send($data))) {
      return new PEAR_Error('write to socket failed');
    }
    return true;
  }

  function end() {
    if ($this->got_newline) 
    	$dot = ".\r\n";
    else
    	$dot = "\r\n.\r\n";

    if (PEAR::isError($this->transport->_send($dot))) {
      return new PEAR_Error('write to socket failed');
    }
    if (PEAR::isError($error = $this->transport->_parseResponse(250))) {
      return $error;
    }
    $this->transport->disconnect();
    $this->transport = false;
    return true;
  }

  var $host;
  var $port;
  var $transport;
  var $got_newline;
};

class KolabLMTP extends KolabMailTransport {
  function KolabLMTP( $host = '127.0.0.1', $port = 2003, $uid='', $pass='', $mech='PLAIN' ) {
    $this->KolabMailTransport($host,$port, $uid, $pass, $mech);
  }

  function createTransport() {
    require_once 'Net/LMTP.php';
    $this->transport = &new Net_LMTP($this->host, $this->port);    
  }
};

class KolabSMTP extends KolabMailTransport {
  function KolabSMTP( $host = '127.0.0.1', $port = 25, $uid='', $pass='', $mech='PLAIN' ) {
    $this->KolabMailTransport($host,$port, $uid, $pass, $mech);
  }

  function createTransport() {
    require_once 'Net/SMTP.php';
    $this->transport = &new Net_SMTP($this->host, $this->port);    
  }
};

?>
