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

class FreeBusyLDAP {
  function FreeBusyLDAP( $uri, $base ) {
    $this->is_bound = false;
    $this->uri = $uri;
    $this->base = $base;
    return $this->connection=ldap_connect($uri);    
  }

  function error() {
    return ldap_error( $this->connection );
  }

  function close() {
    $rc = ldap_close( $this->connection );
    $this->connection = false;
    return $rc;
  }

  function bind( $dn = false , $pw = '' ) {
    if( $dn ) return $this->is_bound = ldap_bind( $this->connection, $dn, $pw );
    else return $this->is_bound = ldap_bind( $this->connection);
  }

  function freeBusyPast() {
    $result = ldap_read( $this->connection, $this->base, 
			 '(&(objectClass=kolab)(k=kolab))',
			   array( 'kolabFreeBusyPast' ) );
    if( $result ) {
      $entries = ldap_get_entries( $this->connection, $result );
      if( $entries['count'] > 0 && !empty($entries[0]['kolabfreebusypast'][0]) ) {
	ldap_free_result($result);
	return $entries[0]['kolabfreebusypast'][0];
      }
    }
    return 0; // Default
  }

  // Return a hash of info about a user
  function userInfo( $uid ) {
	  $result = ldap_search( $this->connection, $this->base, 
			  '(&(objectClass=kolabInetOrgPerson)(|(uid='.
						  $this->escape($uid).')(mailPrimaryAddress='.$this->escape($uid).')))',
			  array( 'dn','mailPrimaryAddress','uid','kolabHomeServer', 'kolabFreeBusyFuture' ) );
	  if( $result ) {
		  $entries = ldap_get_entries( $this->connection, $result );
		  if( $entries['count'] > 0 ) {
			  $hash = array();
			  $hash['DN'] = $this->readLdapAttr( $entries[0], 'dn' );
			  $hash['UID'] = $this->readLdapAttr( $entries[0], 'uid' );
			  $hash['MAIL'] = $this->readLdapAttr( $entries[0], 'mailPrimaryAddress', $uid );
			  $hash['HOMESERVER'] = $this->readLdapAttr( $entries[0], 'kolabhomeserver' );
			  $hash['FBFUTURE'] = (int)($this->readLdapAttr( $entries[0], 'kolabfreebusyfuture', 60 ));
			  ldap_free_result( $result );
			  return $hash;
		  }
		  ldap_free_result( $result );
	  }
	  return false;
  }

  function mailForUid( $uid ) {
    return $this->_internalLookupMail('(&(objectClass=kolabInetOrgPerson)(uid='.$uid.'))',$uid);
  }

  function mailForUidOrAlias( $uid ) {
    return $this->_internalLookupMail('(&(objectClass=kolabInetOrgPerson)(|(uid='.$uid.')(alias='.$uid.')))',$uid);
  }

  function homeServer( $uid ) {
    $result = ldap_search( $this->connection, $this->base, 
			   '(&(objectClass=kolabInetOrgPerson)(|(uid='.$uid.')(mailPrimaryAddress='.$uid.')))',
			   array( 'kolabhomeserver' ) );
    if( $result ) {
      $entries = ldap_get_entries( $this->connection, $result );
      if( $entries['count'] > 0 && !empty($entries[0]['kolabhomeserver'][0]) ) 
	return $entries[0]['kolabhomeserver'][0];
    }
    return false;
  }

  function dn( $uid ) {
    $result = ldap_search( $this->connection, $this->base, 
			   '(&(objectClass=kolabInetOrgPerson)(|(uid='.$uid.')(mailPrimaryAddress='.$uid.')))',
			   array( 'dn' ) );
    if( $result ) {
      $entries = ldap_get_entries( $this->connection, $result );
      if( $entries['count'] > 0 ) { 
	return $entries[0]['dn'];
      }
    }
    return false;    
  }
  function distlists( $dn ) {
    $result = ldap_search( $this->connection, $this->base, 
			   '(&(objectClass=kolabGroupOfNames)(member='.FreeBusyLDAP::escape($dn).'))',
			   array( 'cn' ) );
    if( $result ) {
      $entries = ldap_get_entries( $this->connection, $result );
      $lst = array();
      for( $i = 0; $i < $entries['count']; $i++ ) {
	$lst[] = $entries[$i]['cn'][0];
      }
      myLog( "FreeBusyLDAP::distlists( $dn ) found ".count($lst)." entries", 
	     RM_LOG_DEBUG );
      return $lst;
    }
    myLog( "FreeBusyLDAP::distlists( $dn ) found nothing", 
	   RM_LOG_DEBUG );
    return false;
  }

  /**********/
  function escape( $str ) {
    /*
      From RFC-2254:

      If a value should contain any of the following characters

      Character       ASCII value
      ---------------------------
      *               0x2a
      (               0x28
      )               0x29
      \               0x5c
      NUL             0x00

     the character must be encoded as the backslash '\' character (ASCII
     0x5c) followed by the two hexadecimal digits representing the ASCII
     value of the encoded character. The case of the two hexadecimal
     digits is not significant.
     */
    $str = str_replace( '\\', '\\5c', $str );
    $str = str_replace( '*',  '\\2a', $str );
    $str = str_replace( '(',  '\\28', $str );
    $str = str_replace( ')',  '\\29', $str );
    $str = str_replace( '\0', '\\00', $str );
    return $str;
  }

  function readLdapAttr( $entry, $attrname, $default = false ) {
    $val = $default;
    if( !array_key_exists( $attrname, $entry ) ) return $default;
    else if( is_array( $entry[$attrname] ) ) {
      $val = $entry[$attrname][0];
    } else {
      $val = $entry[$attrname];
    }
    if( $val == '' ) $val = $default;
    return $val;
  }

  function _internalLookupMail( $filter, $default ) {
    if( !isset( $default ) ) return false;
    $result = ldap_search( $this->connection, $this->base, $filter,
			   array( 'mailPrimaryAddress' ) );
    if( $result ) {
      $entries = ldap_get_entries( $this->connection, $result );
      if( $entries['count'] > 0 && !empty($entries[0]['mailPrimaryAddress'][0]) ) return $entries[0]['mailPrimaryAddress'][0];
    }
    return $default;
  }

  var $connection;
  var $is_bound;
  var $uri;
  var $base;
};

?>
