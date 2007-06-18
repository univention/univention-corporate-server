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

  // Profiling
function microtime_float() {
    list($usec, $sec) = explode(" ", microtime());
    return ((float)$usec + (float)$sec);
}
$start_time = microtime_float();


error_reporting(E_ALL);
$max_execution_time = ini_get('max_execution_time');
if( $max_execution_time < 200 ) ini_set('max_execution_time', '200');

require_once('/var/lib/univention-kolab2-framework/freebusy/freebusycache.class.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/freebusyldap.class.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/misc.php');
require_once('/var/lib/univention-kolab2-framework/freebusy/freebusy.class.php');

require_once('/etc/kolab2/freebusy.conf');

logInit('pfb');

$imapuser     = isset($_SERVER['PHP_AUTH_USER'])?$_SERVER['PHP_AUTH_USER']:false;
$imappw       = isset($_SERVER['PHP_AUTH_PW'])?$_SERVER['PHP_AUTH_PW']:false;
$req_cache    = isset($_REQUEST['cache'])?(bool)$_REQUEST['cache']:false;
$req_folder   = isset($_REQUEST['folder'])?$_REQUEST['folder']:false;
$req_extended = isset($_REQUEST['extended'])?(bool)$_REQUEST['extended']:false;

myLog("pfb.php starting up: user=$imapuser, folder=$req_folder, extended=$req_extended", 
      RM_LOG_DEBUG);

$ldap =& new FreeBusyLDAP( $params['ldap_uri'], $params['base_dn'] );
if( !$ldap->bind() ) {
  notFound( "Bind failed: ".$ldap->error() );
  exit;
}

$userinfo = $ldap->userInfo( $imapuser );
if( $userinfo ) {
  if( $userinfo['MAIL'] ) $imapuser = $userinfo['MAIL'];
  //$homeserver = $userinfo['HOMESERVER'];  
}

$folder = array_values(array_filter(explode('/', $req_folder )));
if( count($folder) < 1 ) {
  // error
  notFound( _('No such folder ').htmlentities($req_folder) );
}
$uinfo = $ldap->userInfo($folder[0]);
$owner = $uinfo['MAIL'];
$homeserver = $uinfo['HOMESERVER'];  
if( empty($owner) || false===strpos($owner,'@')) {
    // try guessing the domain
  $idx = strpos( $imapuser, '@' );
  if( $idx !== false ) {
    $domain = substr( $imapuser, $idx+1 );
    myLog("Trying to append $domain to ".$folder[0], RM_LOG_DEBUG);
    $uinfo = $ldap->userInfo($folder[0].'@'.$domain);
    $owner = $uinfo['MAIL'];
  }
}

if( $homeserver && $homeserver != $params['server'] ) {
  $redirect = 'https://'.$homeserver . $_SERVER['REQUEST_URI'];
  myLog("Found remote user, redirecting to $homeserver", RM_LOG_DEBUG);
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

$cache =& new FreeBusyCache( $params['kolab_prefix'].'/var/www/freebusy/cache',
			     false );
$xcache =& new FreeBusyCache( $params['kolab_prefix'].'/var/www/freebusy/cache',
			     true );

if( $req_cache ) {
  $acl = false;
  if( $req_extended ) {
    $vfb = $xcache->load( $req_folder, $ts, $acl );
  } else {
    $vfb = $cache->load( $req_folder, $ts, $acl );
  }
  if( $acl && $req_extended ) {
    // Check access
    $distlists = $ldap->distlists( $userinfo['DN'] );
    if( $distlists === false ) unauthorized( $req_folder.($req_extended?'.xpfb':'.pfb' ) );
    for( $i = 0; $i < count($distlists); $i++ ) {
      $distlists[$i] = $distlists[$i].'@'.$params['email_domain'];
    }
    $rights = $xcache->getRights( $acl, $imapuser, $distlists );
    if( !$req_extended || $rights['r'] ) {
      // All OK
    } else {
      // Nope
      unauthorized( $req_folder.($req_extended?'.xpfb':'.pfb' ) );
    }
  }
  if( !$vfb ) notFound( $req_folder.($req_extended?'.xpfb':'.pfb').' not found in cache');
} else {
  if( empty($imapuser) ) {
    // Here we really need an authenticated user!
    unauthorized("Please authenticate");
  }

  if( empty($owner) ) {
    notFound( _('No such account ').htmlentities($folder[0]));
    return false;
  }
  unset($folder[0]);
  $folder = join('/', $folder);
  $fbpast = $ldap->freeBusyPast();
  $fb =& new FreeBusy( $imapuser, $imappw, 'localhost', $uinfo['FBFUTURE'], $fbpast );
  $fb->freebusy_days = $params['freebusy_days'];
  $fb->default_domain = $params['email_domain'];
  $rc = $fb->imapConnect();
  if( PEAR::isError( $rc ) ) {
    unauthorized($rc->toString());
    return false;
  }
  $rc = $fb->imapLogin();
  if( PEAR::isError( $rc ) ) {
    unauthorized("Access denied for user $imapuser: ".$rc->toString());
    return false;
  }
  $rc = $fb->imapOpenMailbox(FreeBusy::imapFolderName( $imapuser, $owner, 
						       $folder, $params['email_domain']));
  if( PEAR::isError( $rc ) ) {
    notfound( "Folder: ".$fb->foldername.', '.$rc->toString());
    return false;
  }
  $relevance = $fb->getRelevance();
  list($vfb,$xvfb) = $fb->generateFreeBusy();
  $ts = mktime();
  if( PEAR::isError( $vfb ) ) {
    unauthorized($vfb->toString());
    return false;
  }

  $acl = $fb->getACL();
  if( !$cache->store( $owner.'/'.$folder, $vfb, $acl, $relevance ) ) {
    trigger_error('Could not store pfb in cache file '.$owner.'/'.$folder
		  .'.pfb: '.$cache->error, E_USER_WARNING);
  }
  if( !$xcache->store( $owner.'/'.$folder, $xvfb, $acl, $relevance ) ) {
    trigger_error('Could not store xpfb in cache file '.$owner.'/'.$folder
		  .'.xpfb: '.$cache->error, E_USER_WARNING);
  }

  if( $req_extended ) $vfb = $xvfb;
  unset($xvfb);
}

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
    header('Content-Disposition: attachment; filename="' . $user . '.vfb"');
}

#print "folder=$req_folder, cache=$req_cache, extended=$req_extended";
echo $vfb;
#print_r($acl);

// Finish up
myLog("pfb.php complete, execution time was ".(microtime_float()-$start_time)." secs.", RM_LOG_DEBUG);
shutdown();
?>
