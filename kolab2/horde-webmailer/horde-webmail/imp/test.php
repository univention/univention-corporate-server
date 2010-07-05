<?php
/**
 * $Horde: imp/test.php,v 1.33.6.20 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
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

/* IMP version. */
$module = 'IMP';
require_once './lib/version.php';
$module_version = IMP_VERSION;

require TEST_TEMPLATES . 'header.inc';
require TEST_TEMPLATES . 'version.inc';

/* Display versions of other Horde applications. */
$app_list = array(
    'dimp' => array(
        'error' => 'DIMP provides an alternate display view using JavaScript.',
        'version' => '1.0'
    ),
    'gollem' => array(
        'error' => 'Gollem provides access to local VFS filesystems to attach files.',
        'version' => '1.0'
    ),
    'ingo' => array(
        'error' => 'Ingo provides basic mail filtering capabilities to IMP.',
        'version' => '1.0'
    ),
    'mimp' => array(
        'error' => 'MIMP provides an alternate display view suitable for mobile browsers or very slow connections.',
        'version' => '1.0'
    ),
    'nag' => array(
        'error' => 'Nag allows tasks to be directly created from e-mail data.',
        'version' => '2.0'
    ),
    'turba' => array(
        'error' => 'Turba provides addressbook/contacts capabilities to IMP.',
        'version' => '2.0'
    )
);
$app_output = $horde_test->requiredAppCheck($app_list);

?>
<h1>Other Horde Applications</h1>
<ul>
    <?php echo $app_output ?>
</ul>
<?php

/* Display PHP Version information. */
$php_info = $horde_test->getPhpVersionInformation();
require TEST_TEMPLATES . 'php_version.inc';

/* PHP modules. */
$module_list = array(
    'idn' => array(
        'descrip' => 'Internationalized Domain Names Support',
        'error' => 'IMP requires the idn module (installed via PECL) in order to handle Internationalized Domain Names.',
        'fatal' => false
    ),
    'imap' => array(
        'descrip' => 'IMAP Support',
        'error' => 'IMP requires the imap module to interact with the mail server.  It is required for either IMAP or POP3 access.',
        'fatal' => true
    ),
    'openssl' => array(
        'descrip' => 'OpenSSL Support',
        'error' => 'The openssl module is required to use S/MIME in IMP. Compile PHP with <code>--with-openssl</code> to activate.',
        'fatal' => false
    ),
    'tidy' => array(
        'descrip' => 'Tidy support',
        'error' => 'If the tidy PHP extension is available, IMP can use it to sanitize the output of HTML messages before displaying to the user, and to clean outgoing HTML messages created in the HTML composition mode. See <code>imp/docs/INSTALL</code> for more information.',
        'fatal' => false,
    )
);

/* PHP settings. */
$setting_list = array(
    'file_uploads'  =>  array(
        'setting' => true,
        'error' => 'file_uploads must be enabled to use various features of IMP. See the INSTALL file for more information.'
    )
);

/* IMP configuration files. */
$file_list = array(
    'config/conf.php' => 'The file <code>./config/conf.php</code> appears to be missing. You must generate this file as an administrator via Horde.  See horde/docs/INSTALL.',
    'config/mime_drivers.php' => null,
    'config/prefs.php' => null,
    'config/servers.php' => null
);

/* PEAR/PECL modules. */
$pear_list = array(
    'Auth_SASL' => array(
        'path' => 'Auth/SASL.php',
        'error' => 'If your IMAP server uses CRAM-MD5 or DIGEST-MD5 authentication, this module is required.'
    ),
    'HTTP_Request' => array(
        'path' => 'HTTP/Request.php',
        'error' => 'The HTML composition mode requires HTTP_Request.'
    )
);

/* Get the status output now. */
$module_output = $horde_test->phpModuleCheck($module_list);
$setting_output = $horde_test->phpSettingCheck($setting_list);
$file_output = $horde_test->requiredFileCheck($file_list);
$pear_output = $horde_test->PEARModuleCheck($pear_list);

?>

<h1>PHP Module Capabilities</h1>
<ul>
    <?php echo $module_output ?>
</ul>

<h1>Miscellaneous PHP Settings</h1>
<ul>
    <?php echo $setting_output ?>
</ul>

<h1>Required IMP Configuration Files</h1>
<ul>
    <?php echo $file_output ?>
</ul>

<h1>PEAR</h1>
<ul>
    <?php echo $pear_output ?>
</ul>

<h1>PHP Mail Server Support Test</h1>
<?php

$server = isset($_POST['server']) ? $_POST['server'] : '';
$port = isset($_POST['port']) ? $_POST['port'] : '';
$user = isset($_POST['user']) ? $_POST['user'] : '';
$passwd = isset($_POST['passwd']) ? $_POST['passwd'] : '';
$type = isset($_POST['server_type']) ? $_POST['server_type'] : '';

if (!empty($server) && strlen($user) && strlen($passwd) && !empty($type)) {
    if ($type == 'pop') {
        $conn = array(
            'pop3/notls' => 110,
            'pop3/ssl' => 995,
            'pop3/ssl/novalidate-cert' => 995,
            'pop3/tls/novalidate-cert' => 110
        );
    } else {
        $conn = array(
            'imap/notls' => 143,
            'imap/ssl' => 993,
            'imap/ssl/novalidate-cert' => 993,
            'imap/tls/novalidate-cert' => 143
        );
    }

    $success = array();

    echo "<strong>Attempting to automatically determine the correct connection parameters for your server:</strong>\n";

    foreach ($conn as $key => $val) {
        $server_port = !empty($port) ? htmlspecialchars($port) : $val;
        $mbname = '{' . $server . ':' . $server_port . '/' . $key . '}INBOX';
        echo "<ul><li><em>Trying protocol <tt>" . $key . "</tt>, Port <tt>" . $server_port . "</tt>:</em>\n<blockquote>\n";
        $mbox = @imap_open($mbname, $user, $passwd);
        if ($mbox) {
            $minfo = @imap_mailboxmsginfo($mbox);
            if ($minfo) {
                echo '<span style="color:green">SUCCESS</span> - INBOX has ', $minfo->Nmsgs, ' messages (' . $minfo->Unread, ' new ', $minfo->Recent, ' recent)';
                $success[] = array('server' => $server, 'protocol' => $key, 'port' => $server_port);
            } else {
                echo '<span style="color:red">ERROR</span> - The server returned the following error message:' . "\n" . '<pre>';
                foreach (imap_errors() as $error) {
                    echo htmlspecialchars(wordwrap($error));
                }
                echo '</pre>';
            }
            @imap_close($mbox);
        } else {
            echo '<span style="color:red">ERROR</span> - The server returned the following error message:' . "\n" . '<pre>';
            foreach (imap_errors() as $error) {
                echo htmlspecialchars(wordwrap($error));
            }
            echo '</pre>';
        }
        echo "</blockquote>\n</li></ul>\n";
    }

    if (!empty($success)) {
        echo "<strong>The following configurations were successful and may be used in your imp/config/servers.php file:</strong>\n";
        $i = 1;
        foreach ($success as $val) {
            echo "<blockquote><em>Configuration " . $i++ . "</em><blockquote><pre>";
            foreach ($val as $key => $entry) {
                echo "'" . $key . "' => '" . htmlspecialchars($entry) . "'\n";
            }
            echo "</pre></blockquote></blockquote>\n";
        }

        if ($type == 'imap') {
            echo "<strong>The following IMAP server information was discovered from the remote server:</strong>\n";
            $config = reset($success);
            require_once './lib/IMAP/Client.php';
            $imapclient = new IMP_IMAPClient($config['server'], $config['port'], $config['protocol']);
            $use_tls = $imapclient->useTLS();
            if (!is_a($use_tls, 'PEAR_Error')) {
                $res = $imapclient->login($user, $passwd);
            }
            if (isset($res) && !is_a($res, 'PEAR_Error')) {
                echo "<blockquote><em>Namespace Information</em><blockquote><pre>";
                $namespace = $imapclient->getNamespace();
                if (!is_a($namespace, 'PEAR_Error')) {
                    foreach ($namespace as $val) {
                        echo "NAMESPACE: \"" . $val['name'] . "\"\n";
                        echo "DELIMITER: " . $val['delimiter'] . "\n";
                        echo "TYPE: " . $val['type'] . "\n\n";
                    }
                } else {
                    echo "Could not retrieve namespace information from IMAP server.\n";
                }
                echo "</pre></blockquote></blockquote>\n";

                echo "<blockquote><em>IMAP server capabilities:</em><blockquote><pre>";
                print_r($imapclient->queryCapability(null));
                echo "</pre></blockquote></blockquote>\n";

                echo "<blockquote><em>IMAP Charset Search Support:</em><blockquote><pre>";
                $charset = NLS::getCharset();
                if ($imapclient->searchCharset($charset)) {
                    echo "Server supports searching with the $charset character set.\n";
                } else {
                    echo "Server does not support searching with the $charset character set.\n";
                }
                echo "</pre></blockquote></blockquote>\n";
            } else {
                echo "<blockquote><em>Could not retrieve IMAP information from the remote server.</em></blockquote>";
            }
        }
    } else {
        echo "<strong>Could not determine a successful connection protocol.  Make sure your mail server is running and you have specified the correct port.</strong>\n";
    }
} else {
    ?>
<form name="form1" method="post" action="test.php">
<table>
<tr><td align="right"><label for="server">Server:</label></td><td><input type="text" id="server" name="server" /></td></tr>
<tr><td align="right"><label for="port">Port:</label></td><td><input type="text" id="port" name="port" /></td><td>(If non-standard port; leave blank to auto-detect using standard ports)</td></tr>
<tr><td align="right"><label for="user">User:</label></td><td><input type="text" id="user" name="user" /></td></tr>
<tr><td align="right"><label for="passwd">Password:</label></td><td><input type="password" id="passwd" name="passwd" /></td></tr>
<tr><td align="right"><label for="server_type">Server Type:</label></td><td><select id="server_type" name="server_type"><option value="imap">IMAP</option><option value="pop">POP</option></select></td></tr>
<tr><td></td><td><input type="submit" name="f_submit" value="Submit" /><input type="reset" name="f_reset" value="Reset" /></td></tr>
</table>
</form>
<?php } ?>

<?php
require TEST_TEMPLATES . 'footer.inc';
