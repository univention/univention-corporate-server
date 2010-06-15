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
// $Id: group.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
?>
<html>
<head>
    <title>NNTP news.php.net</title>
</head>
<body>
<?php
require_once "Net/NNTP/Realtime.php";

$nntp = new Net_NNTP_Realtime;

$ret = $nntp->connect("news.php.net");
if( PEAR::isError($ret)) {
 echo '<font color="red">No connection to newsserver!</font><br>' ;
 echo $ret->getMessage();
} else {
    if(isset($_GET['group'])) {
        $msgdata = $nntp->selectGroup($_GET['group']);
        if(PEAR::isError($msgdata)) {
            echo '<font color="red">'.$msgdata->getMessage().'</font><br>' ;        
        } else {
            $msgcount = $msgdata['last']-$msgdata['first'];
            echo '<h1>'.$_GET['group'].'</h1>';
            echo "<b>Message count:</b>&nbsp;".$msgcount;
            echo "<br><b>Posting allowed:</b>&nbsp;";
            switch( $_GET['writable']) {
                case 'y' :
                    echo 'yes';
                    break;
                case 'n' :
                    echo 'no';
                    break;
                case 'm' :
                    echo 'moderated';
                    break;         
                default:
                    echo 'n/a';                       
            }
            echo "<hr>";
            echo "<h2>last 10 messages</h2>";
                
            $msgs = array_reverse($nntp->getOverview( $msgcount-9, $msgcount));
            foreach($msgs as $msgid => $msgheader) {
                echo '<a href="read.php?msgid='.urlencode($msgid).
                    '&group='.urlencode($_GET['group']).
                    '"><b>'.$msgheader["Subject"].'</b></a><br>';
                echo 'from:&nbsp;'.$msgheader["From"]."<br>";
                echo $msgheader["Date"].'<br><br>';
            }        
        }
    } else {
        echo '<font color="red">No newsgroup choosed!</font><br>' ;    
    }
    $nntp->quit();
}    
?>
</body>
</html>