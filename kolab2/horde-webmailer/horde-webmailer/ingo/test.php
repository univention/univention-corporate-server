<?php
/**
 * $Horde: ingo/test.php,v 1.16.12.7 2009-01-06 15:24:34 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Brent J. Nordquist <bjn@horde.org>
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

/* Include Horde's core.php file. */
include_once '../lib/core.php';

/* We should have loaded the String class, from the Horde_Util
 * package, in core.php. If String:: isn't defined, then we're not
 * finding some critical libraries. */
if (!class_exists('String')) {
    echo '<br /><h2 style="color:red">The Horde_Util package was not found. If PHP\'s error_reporting setting is high enough and display_errors is on, there should be error messages printed above that may help you in debugging the problem. If you are simply missing these files, then you need to get the <a href="http://cvs.horde.org/cvs.php/framework">framework</a> module from <a href="http://www.horde.org/source/">Horde CVS</a>, and install the packages in it with the install-packages.php script.</h2>';
    exit;
}

/* Initialize the Horde_Test:: class. */
if (!is_readable('../lib/Test.php')) {
    echo 'ERROR: You must install Horde before running this script.';
    exit;
}
require_once '../lib/Test.php';
$horde_test = new Horde_Test;

/* Ingo version. */
$module = 'Ingo';
require_once './lib/version.php';
$module_version = INGO_VERSION;

require TEST_TEMPLATES . 'header.inc';
require TEST_TEMPLATES . 'version.inc';

/* Display versions of other Horde applications. */
$app_list = array(
    'imp'  =>  array(
        'error' => 'IMP can be used to interface ingo with a mailserver.',
        'version' => '4.0'
    )
);
$app_output = $horde_test->requiredAppCheck($app_list);

?>
<h1>Other Horde Applications</h1>
<ul>
    <?php echo $app_output ?>
</ul>
<?php

/* PHP module capabilities. */
$module_list = array(
    'ftp' => array(
        'descrip' => 'FTP Support',
        'error' => 'If you will be using the VFS FTP driver for procmail scripts, PHP must have FTP support. Compile PHP <code>--with-ftp</code> before continuing.'
    ),
    'imap' => array(
        'descrip' => 'IMAP Support',
        'error' => 'If you will be using the IMAP client-side driver, PHP must have IMAP support built in. Compile PHP <code>--with-imap</code> before continuing.'
    ),
    'ssh2' => array(
        'descrip' => 'SSH2 Support',
        'error' => 'You need the SSH2 PECL module if you plan to use the SSH2 VFS driver to store procmail scripts on the mail server.'
    ),
);

/* Display PHP Version information. */
$php_info = $horde_test->getPhpVersionInformation();
require TEST_TEMPLATES . 'php_version.inc';

/* PEAR */
$pear_list = array(
    'Net_Socket' => array(
        'path' => 'Net/Socket.php',
        'error' => 'If you will be using Sieve scripts, make sure you are using a version of PEAR which includes the Net_Socket class, or that you have installed the Net_Socket package seperately.'
    ),
    'Net_Sieve' => array(
        'path' => 'Net/Sieve.php',
        'error' => 'If you will be using Sieve scripts, make sure you are using a version of PEAR which includes the Net_Sieve class, or that you have installed the Net_Sieve package seperately.'
    )
);

/* Get the status output now. */
$module_output = $horde_test->phpModuleCheck($module_list);

?>
<h1>PHP Module Capabilities</h1>
<ul>
    <?php echo $module_output ?>
</ul>

<h1>PEAR Modules</h1>
<ul>
    <?php echo $horde_test->PEARModuleCheck($pear_list) ?>
</ul>

<?php
require TEST_TEMPLATES . 'footer.inc';
