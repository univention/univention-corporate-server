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
// | Author: Damian Alejandro Fernandez Sosa <damlists@cnba.uba.ar>       |
// +----------------------------------------------------------------------+


/*

This sample shows the parsed returning of the IMAPProtocol methods
this is only useful for testing and to low level IMAP access example



*/




require_once('Net/IMAPProtocol.php');
error_reporting(E_ALL);





$user="user";
$passwd="password";
$host="localhost";
$port="143";


//you can create a file called passwords.php and store your $user,$pass,$host and $port values in it
// or you can modify this script
@require_once("../passwords.php");

$a= new  Net_IMAPProtocol();

$a->setDebug(true);
//$a->setUnparsedResponse(true);
//$a->setUnparsedResponse(false);

$aaa=$a->cmdConnect($host,$port);


//Choose your auth method...
//$aaa=$a->cmdAuthenticate($user,$passwd);
//$aaa=$a->cmdAuthenticate($user,$passwd, "CRAM-MD5");
$aaa=$a->cmdLogin($user,$passwd);
//$aaa=$a->login($user,$passwd);


//$aaa=$a->cmdSelect("user.damian");
$aaa=$a->cmdSelect("inbox");



$str="inbox.peteáá";

//$str="inbox.inbox3aaa &4eE-";
//$str="inbox.&AOEA4QDh-";

echo "Method cmdCreate()\n";
print_r($aaa=$a->cmdCreate($str));


echo "Method cmdList()\n";
print_r($aaa=$a->cmdList("","*"));




//Returns the Auth Methods the IMAP server Has
//print_r($aaa=$a->getServerAuthMethods());
//print_r($aaa=$a->cmdFetch("4","(BODY[1.1])"));
//print_r($aaa=$a->cmdFetch("4","(BODY[1])"));
print_r($aaa=$a->cmdFetch("4","(RFC822.TEXT)"));





print_r($aaa=$a->cmdFetch("1","(BODY[HEADER] BODY[TEXT])"));
print_r($aaa=$a->cmdFetch("1","BODY[HEADER]"));





print_r($aaa=$a->cmdFetch("15","FULL"));
print_r($aaa=$a->cmdFetch("1:3","(FLAGS RFC822.SIZE UID ENVELOPE INTERNALDATE)"));


//print_r($aaa=$a->cmdFetch("1:3","(FLAGS RFC822.SIZE UID INTERNALDATE)"));


//$aaa=$a->cmdFetch("1","(FLAGS RFC822.SIZE UID ENVELOPE INTERNALDATE)");
//print_r($aaa=$a->cmdFetch("1","(FLAGS RFC822.SIZE UID INTERNALDATE)"));
//$aaa=$a->cmdFetch("1:3","BODY[HEADER.FIELDS (References)]");
//$aaa=$a->cmdFetch("1","(UID RFC822.SIZE)");
//$aaa=$a->cmdFetch("1:10","RFC822.SIZE");
//$aaa=$a->cmdFetch("1:10","INTERNALDATE");
//$aaa=$a->cmdFetch("2:6","BODY[TEXT]");
//$aaa=$a->cmdFetch("1:3","(FLAGS)");
//$aaa=$a->cmdFetch("26:32","BODY");
//$aaa=$a->cmdFetch("26:29","BODY");
//$aaa=$a->cmdFetch("1","RFC822");
$aaa=$a->cmdFetch("28","BODY");
//$aaa=$a->cmdFetch("1","BODYSTRUCTURE");
//$aaa=$a->cmdFetch("27","BODYSTRUCTURE");
//$aaa=$a->cmdFetch("1:100","BODYSTRUCTURE");
$aaa=$a->cmdFetch("2:10","(RFC822.SIZE FLAGS INTERNALDATE)");
//$aaa=$a->cmdFetch("1:10","INTERNALDATE");
$aaa=$a->cmdFetch("1","ENVELOPE");
$aaa=$a->cmdFetch("10,9:16","FLAGS");
//$aaa=$a->cmdFetch("10","BODY[TEXT]");
//$aaa=$a->cmdFetch("10","RFC822.HEADER");
//$aaa=$a->cmdFetch("10","RFC822.TEXT");
//$aaa=$a->cmdFetch("10","BODYSTRUCTURE");
//$aaa=$a->cmdFetch("10","RFC822.HEADER");
$aaa=$a->cmdFetch("1:4","(BODY[HEADER] FLAGS RFC822.SIZE INTERNALDATE)");
//$aaa=$a->cmdFetch("1:4","(FLAGS RFC822.SIZE INTERNALDATE)");
//$aaa=$a->cmdFetch("10","BODY[1]");
//$aaa=$a->cmdFetch("1","RFC822.SIZE");
//$aaa=$a->cmdFetch("10","ENVELOPE");
//$aaa=$a->cmdFetch("10","RFC822");
//$aaa=$a->cmdFetch("10","ENVELOPE");
//$aaa=$a->cmdFetch("1:30","(RFC822.SIZE FLAGS)");
//$aaa=$a->cmdFetch("1:30","FLAGS");
//print_r($aaa=$a->cmdFetch(32,"FLAGS"));
//print_r($aaa=$a->cmdFetch("1:3","(FLAGS RFC822.SIZE UID ENVELOPE INTERNALDATE)"));
//print_r($aaa=$a->cmdFetch("1","(FLAGS RFC822.SIZE UID ENVELOPE INTERNALDATE)"));
//print_r($aaa=$a->cmdFetch("10","ENVELOPE"));
//print_r($aaa=$a->cmdFetch("10","FLAGS"));
//$aaa=$a->cmdUidFetch("1","FLAGS");


//print_r($aaa=$a->cmdCapability());

//print_r($aaa=$a->cmdStore("1:2","+FLAGS","\Deleted"));







echo "Method cmdCheck()\n";
print_r($aaa=$a->cmdCheck());

//print_r($aaa=$a->cmdClose());
echo "Method cmdNoop()\n";
print_r($aaa=$a->cmdNoop());

echo "Method cmdRename()\n";
print_r($aaa=$a->cmdRename("inbox.test2","inbox.test3"));

echo "Method cmdSubscribe()\n";
print_r($aaa=$a->cmdSubscribe("inbox.test1"));








echo "Method cmdStatus()\n";
print_r($aaa=$a->cmdStatus("inbox","MESSAGES UNSEEN"));




echo "Method cmdUnsubscribe()\n";
print_r($aaa=$a->cmdUnsubscribe("inbox.test1"));

echo "Method cmdList()\n";
print_r($aaa=$a->cmdList("","*"));

echo "Method cmdLsub()\n";
print_r($aaa=$a->cmdLsub("*","*"));
echo "Method cmdSearch()\n";
print_r($aaa=$a->cmdSearch("ALL"));

echo "Method cmdUidSearch()\n";
print_r($aaa=$a->cmdUidSearch("ALL"));

echo "Method cmdCopy()\n";
print_r($aaa=$a->cmdCopy("1","inbox.test1"));




echo "Method cmdGetQuota()\n";
print_r($aaa=$a->cmdGetQuota("user.montoto"));


echo "Method cmdMyRights()\n";
print_r($aaa=$a->cmdMyRights("inbox"));


echo "Method cmdListRights()\n";
print_r($aaa=$a->cmdListRights("inbox","montoto"));

echo "Method cmdGetACL()\n";
print_r($aaa=$a->cmdGetACL("user.montoto"));

echo "Method cmdSetQuota()\n";
print_r($aaa=$a->cmdSetQuota("user.montoto","500000"));


echo "Method cmdCheck()\n";
print_r($aaa=$a->cmdCheck());


echo "Method cmdCreate()\n";
print_r($aaa=$a->cmdCreate("inbox.inbox3"));

echo "Method cmdStatus()\n";
print_r($a->cmdStatus("inbox","MESSAGES UNSEEN"));

print_r($a->_serverSupportedCapabilities);

echo "Method cmdExamine()\n";
print_r($aaa=$a->cmdExamine("inbox"));

echo "Method cmdStore()\n";
print_r($aaa=$a->cmdStore("1:2","+FLAGS","\Deleted"));

echo "Method cmdExpunge()\n";
print_r($a->cmdExpunge());


echo "Check if the server has ANNOTATEMORE Support\n";
if( $a->hasAnnotateMoreSupport() ){
    echo "Yes the server has ANNOTATEMORE Support\n";
    //print_r( $a->cmdGetAnnotation("inbox" , array("test"), "algo") );

    print_r( $a->cmdSetAnnotation("INBOX" , "/comment",array("value.priv"=>"My comment" ) ) );
    print_r( $a->cmdGetAnnotation("INBOX" , "/comment","value.priv" ) );
}
else{
    echo "The server has NOT ANNOTATEMORE Support\n";

}



//print_r($aaa);
$aaa=$a->cmdLogout();
//print_r($aaa);

?>
