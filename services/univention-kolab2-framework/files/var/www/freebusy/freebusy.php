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

require_once('/var/lib/univention-kolab2-framework/freebusy/freebusycache.class.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/freebusycollector.class.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/freebusyldap.class.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/misc.php');

require_once('/etc/kolab2/freebusy.conf');

logInit( 'freebusy' );

$user = trim($_REQUEST['uid']);
$imapuser     = $_SERVER['PHP_AUTH_USER'];
$imappw       = $_SERVER['PHP_AUTH_PW'];
$req_cache    = (bool)$_REQUEST['cache'];
$req_extended = (bool)$_REQUEST['extended'];

myLog("---FreeBusy Script starting (".$_SERVER['REQUEST_URI'].")---", RM_LOG_DEBUG );
myLog("user=$user, imapuser=$imapuser, req_cache=$req_cache, req_extended=$req_extended", RM_LOG_DEBUG );

$ldap =& new FreeBusyLDAP( $params['ldap_uri'], $params['base_dn'] );
if( !$ldap->bind( $params['bind_dn'], $params['bind_pw'] ) ) {
  notFound( "Bind failed: ".$ldap->error() );
  exit;
}

$imapuser = $ldap->mailForUid( $imapuser );
$user = $ldap->mailForUidOrAlias( $user );
$homeserver = $ldap->homeServer( $user );

if( $homeserver === false ) {
  notFound("Resource ".$_SERVER['REQUEST_URI']." (user=$user, req_extended=$req_extended, req_cache=$req_cache) not found");
}

if( $homeserver != $params['server'] ) {
  $redirect = 'https://'.$homeserver . $_SERVER['REQUEST_URI'];
  if ($params['redirect']) {
    header("Location: $redirect");
  } else {
    header("X-Redirect-To: $redirect");
    $redirect = 'https://' . urlencode($_SERVER['PHP_AUTH_USER']) . ':'
      . urlencode($_SERVER['PHP_AUTH_PW']) . '@' . $homeserver
      . $_SERVER['REQUEST_URI'];
    if (!@readfile($redirect)) {
      unauthorized("Unable to read free/busy information from ".removePassword($redirect));
    }
  }
  shutdown();
  exit;
}


$cache =& new FreeBusyCache( $params['kolab_prefix'].'/var/www/freebusy/cache', $req_extended );
$collector =& new FreeBusyCollector( $user );

$groups = $ldap->distlists( $ldap->dn( $user ) );
for( $i = 0; $i < count($groups); $i++ ) {
  $groups[$i] = $groups[$i].'@'.$params['email_domain'];
}
$pfbs = $cache->findAll( $user, $groups );
$ts = 0;
if( $pfbs === false ) {
  notFound($pfb->error);
}

if( $req_extended ) {
  // Get accessing users groups
  $imapgroups = $ldap->distlists( $ldap->dn( $imapuser ) );
}

foreach( $pfbs as $pfb ) {
  $fb = $cache->load( $pfb, $ts2, $acl );
  if( $fb ) myLog("Found fb for $pfb", RM_LOG_DEBUG);
  else myLog("No fb found for $pfb", RM_LOG_DEBUG);
  if( $acl && $req_extended ) {
    $r = $cache->getRights( $acl, $imapuser, $imapgroups );
    if( !$fb || !array_key_exists( 'r', $r ) ) {
      $cache->extended = false; // HACK!
      $fb = $cache->load( $pfb, $ts2, $acl );    
      $cache->extended = true;
      myLog("Falling back to non-extended fb", RM_LOG_DEBUG );
    }
  }
  $ts = max( $ts, $ts2 );
  if( $fb ) {
    if( $collector->addFreebusy( $fb ) == FB_TOO_OLD ) {
      $cache->delete( $pfb );
    }
  }
}
$vfb = $collector->exportvCalendar();

// And finally send it out, ensuring it doesn't get cached along the way
header('Cache-Control: no-store, no-cache, must-revalidate');
header('Cache-Control: post-check=0, pre-check=0', false);
header('Pragma: no-cache');
header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
header('Last-Modified: ' . gmdate("D, d M Y H:i:s",$ts) . ' GMT');
header('Pragma: public');
header('Content-Transfer-Encoding: none');
if ($params['send_content_type']) {
    header('Content-Type: text/calendar');
}
if ($params['send_content_length']) {
    header('Content-Length: ' . strlen($vfb));
}
if ($params['send_content_disposition']) {
    header('Content-Disposition: attachment; filename="' . $user . '.ifb"');
}

echo $vfb;
?>