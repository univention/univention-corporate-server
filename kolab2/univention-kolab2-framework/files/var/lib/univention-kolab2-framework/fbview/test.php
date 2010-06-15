<?php
/**
 * $Horde: horde/test.php,v 1.117 2004/04/23 16:46:04 slusarz Exp $
 *
 * Copyright 2002-2004 Brent J. Nordquist <bjn@horde.org>
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Register a session. */
session_start();
if (!isset($_SESSION['horde_test_count'])) {
    $_SESSION['horde_test_count'] = 0;
}

/* Include Horde's core.php file. */
include_once 'lib/core.php';

/* We should have loaded the String class, from the Horde_Util
 * package, in core.php. If String:: isn't defined, then we're not
 * finding some critical libraries. */
if (!class_exists('String')) {
    echo '<br /><span style="color: red; font-size: 18px; font-weight: bold;">The Horde_Util package was not found. If PHP\'s error_reporting setting is high enough, there should be error messages printed above that may help you in debugging the problem. If you are simply missing these files, then you need to get the <a href="http://cvs.horde.org/cvs.php/framework">framework</a> module from <a href="http://horde.org/source/">Horde CVS</a>, and install the packages in it with the install-packages.php script.</span>';
    exit;
}

/* Initialize the Horde_Test:: class. */
if (!include_once 'lib/Test.php') {
    /* Try and provide enough information to debug the missing
     * file. */
    echo '<br /><span style="color: red; font-size: 18px; font-weight: bold;">Unable to find horde/lib/Test.php. Your Horde installation may be missing critical files, or PHP may not have sufficient permissions to include files. There may be error messages printed above this message that will help you in debugging the problem.</span>';
    exit;
}

/* If we've gotten this far, we should have found enough of Horde to
 * run tests. Create the testing object. */
$horde_test = &new Horde_Test();

/* Horde definitions. */
$module = 'Horde';
require_once './lib/version.php';
$module_version = HORDE_VERSION;

/* PHP module capabilities. */
$module_list = array(
    'ctype' => 'Ctype Support',
    'domxml' => 'DOM XML Support',
    'ftp' => 'FTP Support',
    'gd' => 'GD Support',
    'gettext' => array(
        'descrip' => 'Gettext Support',
        'error' => 'Horde will not run without gettext support. Compile PHP with <code>--with-gettext</code> before continuing.',
        'fatal' => true
    ),
    'iconv' => 'Iconv Support',
    'imap' => 'IMAP Support',
    'ldap' => 'LDAP Support',
    'mbstring' => 'Mbstring Support',
    'mcal' => 'MCAL Support',
    'mcrypt' => 'Mcrypt Support',
    'fileinfo' => array(
        'descrip' => 'MIME Magic Support',
        'error' => 'The fileinfo PECL module is recommended for use with Horde as it will provide faster MIME Magic lookups. See horde/docs/INSTALL for information on how to install PECL extensions.'
    ),
    'mysql' => 'MySQL Support',
    'openssl' => 'OpenSSL Support',
    'pgsql' => 'PostgreSQL Support',
    'xml' => 'XML Support',
    'zlib' => array(
        'descrip' => 'Zlib Support',
        'error' => 'The zlib module is highly recommended for use with Horde.  It allows page compression and handling of ZIP and GZ data. Compile PHP with <code>--with-zlib</code> to activate.',
        'fatal' => false
    ),
);


/* PHP Settings. */
$setting_list = array(
    'magic_quotes_runtime' => array(
        'setting' => false,
        'error' => 'magic_quotes_runtime may cause problems with database inserts, etc. Turn it off.'
    ),
    'memory_limit' => array(
        'setting' => false,
        'error' => 'If PHP\'s internal memory limit is turned on and if not set high enough Horde will not be able to handle large data items (e.g. large mail attachments in IMP). If possible, you should disable the PHP memory limit by recompiling PHP <i>without</i> the "--enable-memory-limit" flag. If this is not possible, then you should set the value of memory_limit in php.ini to a sufficiently high value (Current value of memory_limit: ' . ini_get('memory_limit') . ').'
    ),
    'file_uploads' => array(
        'setting' => true,
        'error' => 'file_uploads must be enabled for some features like sending emails with IMP.'
    ), 
    'safe_mode' => array(
        'setting' => false,
        'error' => 'If safe_mode is enabled, Horde cannot set enviroment variables, which means Horde will be unable to translate the user interface into different languages.'
    ),
    'session.use_trans_sid' => array(
        'setting' => false,
        'error' => 'Horde will work with session.use_trans_sid turned on, but you may see double session-ids in your URLs, and if the session name in php.ini differs from the session name configured in Horde, you may get two session ids and see other odd behavior. The URL-rewriting that use_trans_sid does also tends to break XHTML compliance. In short, you should really disable this.'
    )
);


/* PEAR */
$pear_list = array(
    'Mail_RFC822' => array(
        'path' => 'Mail/RFC822.php',
        'error' => 'Make sure you are using a recent version of PEAR which includes the Mail_RFC822 class.'
    ),
    'Mail_Mime' => array(
        'path' => 'Mail/mimeDecode.php',
        'error' => 'You do not have the Mail_Mime package installed on your system. See the INSTALL file for instructions on how to install the package.',
        'required' => true
    ),
    'Log' => array(
        'path' => 'Log.php',
        'error' => 'Make sure you are using a version of PEAR which includes the Log classes, or that you have installed the Log package seperately. See the INSTALL file for instructions on installing Log.',
        'required' => true
    ),
    'DB' => array(
        'path' => 'DB.php',
        'error' => 'You will need DB if you are using SQL drivers for preferences, contacts (Turba), etc.',
        'function' => '_check_pear_db_version'
    ),
    'Net_Socket' => array(
        'path' => 'Net/Socket.php',
        'error' => 'Make sure you are using a version of PEAR which includes the Net_Socket class, or that you have installed the Net_Socket package seperately. See the INSTALL file for instructions on installing Net_Socket.'
    ),
    'Date' => array(
        'path' => 'Date/Calc.php',
        'error' => 'Horde requires the Date_Calc class for Kronolith to calculate dates.'
    ),
    'Auth_SASL' => array(
        'path' => 'Auth/SASL.php',
        'error' => 'Horde will work without the Auth_SASL class, but if you use Access Control Lists in IMP you should be aware that without this class passwords will be sent to the IMAP server in plain text when retrieving ACLs.'
    ),
    'HTTP_Request' => array(
        'path' => 'HTTP/Request.php',
        'error' => 'Parts of Horde (Jonah, the XML-RPC client/server) use the HTTP_Request library to retrieve URLs and do other HTTP requests.'
    ),
    'File' => array(
        'path' => 'File/CSV.php',
        'error' => 'Horde will work without the File_CSV class, but there may be errors when importing some CSV files.'
    ),
    'Net_SMTP' => array(
        'path' => 'Net/SMTP.php',
        'error' => 'Make sure you are using the Net_SMTP module if you want "smtp" to work as a mailer option.'
    ),
    'VFS' => array(
        'path' => 'VFS.php',
        'error' => 'Many Horde appliations use VFS to provide access to file storage.',
        'required' => true
    ),
    'XML_SVG' => array(
        'path' => 'XML/SVG.php',
        'error' => 'XML_SVG is used by several Horde applications to generate graphs and other SVG diagrams.'
    ),
    'Services_Weather' => array(
        'path' => 'Services/Weather.php',
        'error' => 'Services_Weather is used by the weather applet/block on the portal page.'
    )
);

/**
 * Additional check for PEAR DB module for its version.
 */
function _check_pear_db_version()
{
    $peardbversion = '0';
    $peardbversion = @DB::apiVersion();
    if ($peardbversion < 2) {
        return 'Your version of DB (' . $peardbversion . ') is not recent enough.';
    }
}

/* There is a version of the File.php that wants a PEAR::registerShutdownFunc
   which is what newpear tests for.  This function seems to only have existed
   for a little while, but the PEAR group hasn't fixed this yet, so some
   people get an error if they have a certain (release) version of PEAR.
   We test for it here.  If it's a safe version, test as normal, otherwise
   try a less effective but non-erroring test for File::CSV. */
if (!$horde_test->isRecentPEAR()) {
    $path = ini_get('include_path');
    if (empty($path)) {
        $path = '.';
    }
    $pear_list['File_CSV']['path'] = 'XXXXXX.php';
    foreach (explode(':', $path) as $dir) {
        if (substr($dir, -1) != '/') {
            $dir .= '/';
        }
        $file1 = $dir . 'File/CSV.php';
        $file2 = $dir . 'File.php';
        $file3 = $dir . 'PEAR.php';
        if (file_exists($file1) && file_exists($file2) && file_exists($file3)) {
            /* Change the filename to something we know will be found. */
            $pear_list['File_CSV']['path'] = 'PEAR.php';
            break;
        }
    }
}

/* Required configuration files. */
$file_list = array(
    'config/conf.php' => null,
    'config/html.php' => 'The file <code>./config/html.php</code> appears to be missing. You probably just forgot to copy <code>./config/html.php.dist</code> over.',
    'config/mime_drivers.php' => null,
    'config/nls.php' => null,
    'config/prefs.php' => null,
    'config/registry.php' => null
);


/* Get the status output now. */
$module_output = $horde_test->phpModuleCheck($module_list);
$setting_output = $horde_test->phpSettingCheck($setting_list);
$pear_output = $horde_test->PEARModuleCheck($pear_list);
$config_output = $horde_test->requiredFileCheck($file_list);


/* Handle special modes. */
if (!empty($_GET['mode'])) {
    $url = !empty($_GET['url']) ? $_GET['url'] : 'test.php';
    echo '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "DTD/xhtml1-transitional.dtd">';
    switch ($_GET['mode']) {
    case 'extensions':
        require TEST_TEMPLATES . 'extensions.inc';
        exit;
        break;

    case 'phpinfo':
        echo '<a href="' . $url . '?mode=test">&lt;&lt; Back to test.php</a>';
        phpinfo();
        exit;
        break;

    case 'filetest':
        echo '<a href="' . $url . '?mode=test">&lt;&lt; Back to test.php</a>';
        ?>
        <html>
        <body bgcolor="white" text="black">
        <p><font face="Helvetica, Arial, sans-serif" size="2">
        There are some versions of PEAR that were released at times that
        did not contain a function that File.php expects.  This does not
        seem to have caused problems for anyone except when running our
        test script, but you need to be aware of it.  If you see a fatal
        error in File.php listed below this text, you have one of the
        combinations of problem files.  Make sure you have the latest
        PEAR and File packages available (<a href="http://pear.php.net/">
        see http://pear.php.net</a>).  If you do not get the error, you are
        in fine shape.</p>
        <?php include_once 'File/CSV.php';
        exit;
        break;

    case 'unregister':
        unset($_SESSION['horde_test_count']);
        ?>
        <html>
        <body bgcolor="white" text="black">
        <font face="Helvetica, Arial, sans-serif" size="2">
        The test session has been unregistered.<br>
        <a href="test.php">Go back</a> to the test.php page.<br>
        <?php
        exit;
        break;
    }
}

require TEST_TEMPLATES . 'header.inc';
require TEST_TEMPLATES . 'version.inc';

?>

<h1>Horde Applications</h1>
<ul>
<?php

/* Get Horde module version information. */
$modules = $horde_test->applicationList();
foreach ($modules as $app => $val) {
    $app = ucfirst($app);
    echo '<li>' . $app . ': ' . $val->version;
    if (isset($val->test)) {
        echo ' (<a href="' . $val->test . '">run ' . $app . ' tests</a>)';
    }
    echo "</li>\n";
}

?>
</ul>

<?php

/* Display PHP Version information. */
$php_info = $horde_test->getPhpVersionInformation();
require TEST_TEMPLATES . 'php_version.inc';

?>

<h1>PHP Module Capabilities</h1>
<ul>
    <?php echo $module_output ?>
</ul>

<h1>Miscellaneous PHP Settings</h1>
<ul>
    <?php echo $setting_output ?>
</ul>

<h1>Required Horde Configuration Files</h1>
<ul>
    <?php echo $config_output ?>
</ul>

<h1>PHP Sessions</h1>
<?php $_SESSION['horde_test_count']++; ?>
<ul>
    <li>Session counter: <?php echo $_SESSION['horde_test_count']; ?></li>
    <li>To unregister the session: <a href="test.php?mode=unregister">click here</a></li>
</ul>

<h1>PEAR</h1>
<ul>
    <?php echo $pear_output ?>
</ul>

<?php
require TEST_TEMPLATES . 'footer.inc'; 
