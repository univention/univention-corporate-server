<?php
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Alexander Merz <alexmerz@php.net>                           |
// |          Heino H. Gehlsen <heino@gehlsen.dk>                         |
// +----------------------------------------------------------------------+
//
// $Id: read.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
?>
<html>
<head>
    <title>NNTP news.php.net</title>
</head>
<body>
<h1>Message</h1>
<?php
require_once "Net/NNTP/Realtime.php";

$nntp = new Net_NNTP_Realtime;

$ret = $nntp->connect("news.php.net");
if( PEAR::isError($ret)) {
 echo '<font color="red">No connection to newsserver!</font><br>' ;
 echo $ret->getMessage();
} else {
    if(isset($_GET['msgid']) and isset($_GET['group'])){
        $msgdata = $nntp->selectGroup($_GET['group']);
        if(PEAR::isError($msgdata)) {
            echo '<font color="red">'.$msgdata->getMessage().'</font><br>' ;        
        } else {
            $header = $nntp->getHeader($_GET['msgid']);
            echo '<hr>';
            echo '<h2>Header</h2>';
            echo '<pre>';
            foreach( $header->getFieldsArray() as $line) {
                echo $line.'<br>';
            }              
            echo '</pre>';
            echo '<hr>';
            echo '<h2>Body</h2>';
            echo '<form><textarea wrap="off" cols="79", rows="25">'.
                    $nntp->getBodyRaw($_GET['msgid'], true).
                '</textarea></form>';           
        }        
    } else {
        echo '<font color="red">No message choosed!</font><br>' ;    
    }
    $nntp->quit();
}    
?>
</body>
</html>