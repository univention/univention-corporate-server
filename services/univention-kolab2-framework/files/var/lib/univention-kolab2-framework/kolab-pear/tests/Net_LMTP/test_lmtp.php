<?
//
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Chuck Hagenbuch <chuck@horde.org>                           |
// |          Jon Parise <jon@php.net>                                    |
// |          Damian Alejandro Fernandez Sosa <damlists@cnba.uba.ar>      |
// +----------------------------------------------------------------------+


require_once('Net/LMTP.php');



// The LMTP server
$host="localhost";
// The default LMTP port
$port="2003";
// The username to authenticate to the LMTP server
$user="cyrus";
// The password to authenticate to the LMTP server
$pwd="password";


//you can create a file called passwords.php and store your $user,$pass,$host and $port values in it
// or you can modify this script
@require_once("./passwords.php");



// The name we send to initiate the LMTP dialog
$localhost="localhost";

// The email as we send the email in the LMTP dialog
$from="damian@cnba.uba.ar";
// The email to send the email in the LMTP dialog
//$to="damian@fernandezsosa.com.ar";
$to="damian@1aaafernandezsosa.com.ar";
//$to="damian";

// The email text (RFC822 format)
$email="From:damian@cnba.uba.ar\r\nTo:damian@cnba.uba.ar\r\nDate: Wed, 12 Feb 2004 21:07:35 -300\r\nSubject: testing LMTP\r\n\r\nthis is a test email\r\n";



// We create the Net_LMTP instance
$lmtp_conn= new Net_LMTP( $host ,  $port , $localhost);

$lmtp_conn->setDebug(true);
// Connect to the LMTP server
if (PEAR::isError( $error = $lmtp_conn->connect())) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}
// Authenticates against the LMTP server using PLAIN method.
if (PEAR::isError( $error = $lmtp_conn->auth($user,$pwd,'PLAIN'))) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}
// Send the MAIL FROM: LMTP command
if (PEAR::isError( $error = $lmtp_conn->mailFrom($from))) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}

// Send the RCPT TO: LMTP command
if (PEAR::isError( $error = $lmtp_conn->rcptTo($to))) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}

// Send the DATA: LMTP command (we send the email RFC822 encoded)
if (PEAR::isError( $error = $lmtp_conn->data($email))) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}
// now the email was accepted by the LMTP server, so we close
// the connection


// Send the QUIT LMTP command and disconnect from the LMTP server
if (PEAR::isError( $error = $lmtp_conn->disconnect())) {
    echo "ERROR:" . $error->getMessage() . "\n";
    exit();
}


?>
