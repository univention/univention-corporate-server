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

/*! To load/store partial freebusy lists
    and their ACLs */
class FreeBusyCache {
  function FreeBusyCache( $basedir, $extended = false ) {
    $this->basedir = $basedir;
    $this->extended = $extended;
  }

  function store( $filename, $fbdata, $acl, $relevance ) {
    if( ereg( '\.\.', $filename ) ) {
      $this->error = $filename._(' is not absolute');
      return false;
    }

    $fbfilename = $this->mkfbfilename($filename);
    myLog("FreeBusyCache::store( file=$fbfilename, acl=[ "
	  .str_replace("\n",", ",$this->aclToString($acl))
	  ."], relevance=$relevance )", RM_LOG_DEBUG);
    if( $fbdata === false ) {
      // false data means delete the pfb
      unlink($fbfilename);
      $oldacl = $this->loadACL( $filename );
      $db = dba_open( '/var/www/freebusy/cache/pfbcache.db', 'cd', 'gdbm' );
      if( $db === false ) return false;
      foreach( $oldacl as $ac ) {
	  if( dba_exists( $ac['USER'], $db ) ) {
	    $lst = dba_fetch( $ac['USER'], $db );
	    $lst = $this->decodeList( $lst );
	    $lst = array_diff( $lst, array($fbfilename));
	    myLog("(delete) dba_replace(".$uid.", \"".$this->encodeList($lst)."\")", RM_LOG_DEBUG);
	    dba_replace( $uid, $this->encodeList($lst), $db );
	  }
      }
      unlink($fbfilename.'.acl');
    } else {
      //myLog("Storing $filename with acl ".var_export($acl,true), RM_LOG_DEBUG);
      
      // Create directories if missing
      $fbdirname  = dirname( $fbfilename );
      if (!is_dir($fbdirname)) {
	if( !$this->mkdirhier($fbdirname) ) {
	  $this->error = _("Error creating dir $fbdirname");
	  return false;
	}
      }
      
      // Store the fb list
      $tmpn = tempnam($this->basedir, 'fb');
      $tmpf = fopen($tmpn, 'w');
      if( !$tmpf ) return false;
      fwrite($tmpf, $fbdata);
      if( !rename($tmpn, $fbfilename) ) {
	$this->error = _("Error renaming $tmpn to $fbfilename");
	return false;
      }
      fclose($tmpf);
      
      // Store the ACL
      $oldacl = $this->loadACL( $filename );
      if( !$this->storeACL( $filename, $acl ) ) return false;
      
      // Update overview db
      switch( $relevance ) {
      case 'admins':  $perm = 'a'; break;
      case 'readers': $perm = 'r'; break;
      case 'nobody':  $perm = 'false'; break;
      default: $perm = 'a';
      }

      $db = dba_open( '/var/www/freebusy/cache/pfbcache.db', 'cd', 'gdbm' );
      if( $db === false ) {
	myLog('Unable to open freebusy cache db '.'/var/www/freebusy/cache/pfbcache.db',
	      RM_LOG_ERROR );
	return false;
      }
      foreach( $acl as $ac ) {
	$uid = $ac['USER'];
	if( dba_exists( $uid, $db ) ) {
	  $lst = dba_fetch( $uid, $db );
	  $lst = $this->decodeList( $lst );
	  $lst = array_diff( $lst, array($filename));
	  dba_replace( $uid, $this->encodeList($lst), $db );
	}
      }
      if( $perm !== false ) {
	foreach( $acl as $ac ) {
	  if( strpos( $ac['RIGHTS'], $perm ) !== false ) {
	    if( dba_exists( $ac['USER'], $db ) ) {
	      $lst = dba_fetch( $ac['USER'], $db );
	      $lst = $this->decodeList( $lst );
	      $lst[] = $filename;
	      dba_replace( $ac['USER'], $this->encodeList(array_unique($lst)), $db );
	    } else {
	      dba_insert( $ac['USER'], $filename, $db );
	    }
	  }
	}
      }
      dba_close($db);
      return true;
    }
  }

  function load( $filename, &$ts, &$acl ) {
    myLog("FreeBusyCache::load( $filename )", RM_LOG_DEBUG);
    $fbfilename = $this->mkfbfilename($filename);
    if( file_exists($fbfilename) ) {
      if( !is_null($ts)) $ts = filectime($fbfilename);
      $acl = $this->loadACL($filename);
      myLog("FreeBusyCache::load(): ts=$ts acl=[ "
	    .str_replace("\n",", ",$this->aclToString($acl))
	    ."] )", RM_LOG_DEBUG);
      return file_get_contents($fbfilename);
    }
    return false;
  }

  function delete( $filename ) {
    $fbfilename = $this->mkfbfilename($filename);
    unlink($fbfilename);
    unlink($this->mkaclfilename($filename));    
    $db = dba_open( '/var/www/freebusy/cache/pfbcache.db', 'cd', 'gdbm' );
    if( $db === false ) return false;
    for( $uid = dba_firstkey($db); $uid !== false; $uid = dba_nextkey($db)) {
      $lst = dba_fetch( $uid, $db );
      $lst = $this->decodeList( $lst );
      $lst = array_diff( $lst, array($filename));
      myLog("(delete) dba_replace(".$uid.", \"".$this->encodeList($lst)."\")", RM_LOG_DEBUG);
      dba_replace( $uid, $this->encodeList($lst), $db );      
    }
    dba_close($db);
  }

  function findAll( $uid, $groups ) {
    $lst = array();
    $db = dba_open( '/var/www/freebusy/cache/pfbcache.db', 'rd', 'gdbm' );
    if( $db === false ) return false;
    $uids = $groups;
    for( $i = 0; $i < count($uids); $i++ ) $uids[$i] = 'group:'.$uids[$i];
    $uids[] = $uid;
    foreach( $uids as $uid ) {
      if( dba_exists( $uid, $db ) ) {
	$tmplst = dba_fetch( $uid, $db );
	myLog("Found ".$uid." := $tmplst", RM_LOG_DEBUG);
	$lst = array_merge( $lst, $this->decodeList( $tmplst ) );
      } else {
	myLog("$uid not found", RM_LOG_DEBUG);	
      }
    }
    dba_close($db);
    $lst = array_unique($lst);
    myLog( "FreeBusyCache::findAll( $uid, [".join(', ', $groups).'] ) = ['.join(', ',$lst).']',
	   RM_LOG_DEBUG );
    return $lst;
  }

  /*************** Private API below this line *************/
  function mkdirhier( $dirname ) {
    $base = substr($dirname,0,strrpos($dirname,'/'));
    if( !empty( $base ) && !is_dir( $base ) ) {
      if( !$this->mkdirhier( $base ) ) return false;
    }
    if( !file_exists( $dirname ) ) return mkdir( $dirname, 0755 );
    return true;
  }

  function mkfbfilename( $fbfilename ) {
    $fbfilename = str_replace( '..', '', $fbfilename );
    $fbfilename = str_replace( "\0", '', $fbfilename );    
    return $this->basedir.'/'.$fbfilename.($this->extended?'.xpfb':'.pfb');
  }

  function mkaclfilename( $fbfilename ) {
    $fbfilename = str_replace( '..', '', $fbfilename );
    $fbfilename = str_replace( "\0", '', $fbfilename );    
    return $this->basedir.'/'.$fbfilename.($this->extended?'.xpfb':'.pfb').'.acl';
  }

  function aclToString( $acl ) {
    $aclstr = '';
    foreach( $acl as $ac ) {
      $aclstr .= $ac['USER'].' '.$ac['RIGHTS']."\n";
    }
    return $aclstr;
  }

  function aclFromString( $aclstr ) {
    $acl = array();
    foreach( split("\n", $aclstr ) as $ac ) {
      if( ereg("(.*) (.*)", $ac, $regs ) ) {
	$acl[] = array('USER' => $regs[1], 'RIGHTS' => $regs[2] );
      }
    }
    return $acl;
  }

  function loadACL( $filename ) {
    return $this->aclFromString( @file_get_contents($this->mkaclfilename($filename)) );    
  }

  function storeACL( $filename, $acl ) {
    $tmpn = tempnam($this->basedir, 'acl');
    $tmpf = fopen($tmpn, 'w');
    if( !$tmpf ) return false;
    fwrite($tmpf, $this->aclToString($acl) );

    $aclfilename = $this->mkaclfilename($filename);
    if( !rename($tmpn, $aclfilename) ) {
      $this->error = _("Error renaming $tmpn to $fbfilename");
      return false;
    }
    fclose($tmpf);    
    return true;
  }

  function aclDiff( $oldacl, $newacl ) {
    $newuids = array();
    foreach( $newacl as $ac ) {
      if( strpos( $ac['RIGHTS'], 'r' ) !== false ) {
	$newuids[$ac['USER']] = true;
      }
    }
    $deleteduids = array();
    foreach( $oldacl as $ac ) {
      if( !$newuids[$ac['USER']] ) $deleteduids[] = $ac['USER'];
    }
    return $deleteduids;
  }

  /** Returns an array with cyrus permission chars (lrsp...) as keys */
  function getRights( $acl, $uid, $groups ) {
    if( !isset($uid) ) return false;
    if( is_array( $groups ) ) $uids = $groups;
    else $uids = array();
    for( $i = 0; $i < count($uids); $i++ ) $uids[$i] = 'group:'.$uids[$i];
    $uids[] = $uid;
    $rights = array();
    $negacl = array();

    // Calc positive rights
    foreach( $acl as $ac ) {
      $r = $ac['RIGHTS'];
      $u = $ac['USER'];
      if( $r{0} == '-' ) {
	$negacl[] = array( 'USER' => $u, 'RIGHTS' => $r );
	continue;
      }
      if( in_array( $u, $uids ) ) {
	for( $i = 0; $i < strlen($r); $i++ ) {
	  $rights[$r{$i}] = true;
	}
      }
    }
    
    // Remove negative rights
    foreach( $negacl as $ac ) {
      $r = $ac['RIGHTS'];
      $u = $ac['USER'];
      if( in_array( $u, $uids ) ) {
	for( $i = 1; $i < strlen($r); $i++ ) {
	  unset($rights[$r{$i}]);
	}
      }
    }
    return $rights;
  }

  function decodeList( $str ) {
    return split( ',', $str );
  }
  function encodeList( $lst ) {
    return join(',',$lst);
  }

  function recursivedir( $dir ) {
    $dh = opendir( $dir );
    if( $dh === false ) return false;
    $dirs = array();
    while (($file = readdir($dh)) !== false) {
      if( is_dir($dir.'/'.$file) ) {
	if($file=='.' || $file=='..') continue;
	if( !ereg( ($this->extended?'/.*\.xpfb$/':'/.*\.pfb$/'), $file ) ) continue;
	$tmp = $this->recursivedir( $dir.'/'.$file );
	if( $tmp !== false ) $dirs = array_merge( $dirs, $tmp );
      } else if( is_file($dir.'/'.$file) ) {
	$dirs[] = $dir.'/'.$file;
      }
    }
    closedir( $dh );
    return $dirs;
  }

  var $basedir;
  var $error;
};

?>