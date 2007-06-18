<?php
/**
 * $Horde: turba/test.php,v 1.8 2004/02/25 21:21:37 chuck Exp $
 *
 * Copyright 2000-2004 Brent J. Nordquist <bjn@horde.org>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

/* Include Horde's core.php file. */
include_once '../lib/core.php';

/* We should have loaded the String class, from the Horde_Util
 * package, in core.php. If String:: isn't defined, then we're not
 * finding some critical libraries. */
if (!class_exists('String')) {
    echo '<br /><span style="color: red; font-size: 18px; font-weight: bold;">The Horde_Util package was not found. If PHP\'s error_reporting setting is high enough, there should be error messages printed above that may help you in debugging the problem. If you are simply missing these files, then you need to get the <a href="http://cvs.horde.org/cvs.php/framework">framework</a> module from <a href="http://horde.org/source/">Horde CVS</a>, and install the packages in it with the install-packages.php script.</span>';
    exit;
}

/* Initialize the Horde_Test:: class. */
if (!(@is_readable('../lib/Test.php'))) {
    echo 'ERROR: You must install Horde before running this script.';
    exit;
}
require_once '../lib/Test.php';
$horde_test = &new Horde_Test;

/* Turba version. */
$module = 'Turba';
require_once './lib/version.php';
$module_version = TURBA_VERSION;

require TEST_TEMPLATES . 'header.inc';
require TEST_TEMPLATES . 'version.inc';

/* Display PHP Version information. */
$php_info = $horde_test->getPhpVersionInformation();
require TEST_TEMPLATES . 'php_version.inc';

/* PHP modules. */
$module_list = array(
    'mysql' => 'MySQL Support',
    'pgsql' => 'PostgreSQL Support',
    'mssql' => 'Microsoft SQL Support',
    'oci8' => 'Oracle Support',
    'odbc' => 'Unified ODBC Support',
    'ldap' => 'LDAP Support'
);

/* Get the status output now. */
$module_output = $horde_test->phpModuleCheck($module_list);

?>

<h1>PHP Module Capabilities</h1>
<ul>
    <?php echo $module_output ?>
</ul>

<h1>PHP LDAP Support Test</h1>
<?php

$server = isset($_POST['server']) ? $_POST['server'] : ''; // 'server.example.com';
$port = isset($_POST['port']) ? $_POST['port'] : ''; // '389';
$basedn = isset($_POST['basedn']) ? $_POST['basedn'] : ''; // 'dc=example,dc=com';
$user = isset($_POST['user']) ? $_POST['user'] : '';     // 'user';
$passwd = isset($_POST['passwd']) ? $_POST['passwd'] : ''; // 'password';
$filter = isset($_POST['filter']) ? $_POST['filter'] : ''; // 'cn=Babs Jensen';

if (!empty($server) && !empty($basedn) && !empty($filter)) {
    if (empty($port)) {
        $port = '389';
    }
    echo 'server="', $server, '" basedn="', $basedn, '" filter="', $filter, '"<br />';
    if ($user) {
        echo 'bind as user="', $user, '"<br />';
    } else {
        echo 'bind anonymously<br />';
    }
    $ldap = ldap_connect($server, $port);
    if ($ldap) {
        if (!empty($user) && !ldap_bind($ldap, $user, $passwd)) {
            echo "<p>unable to bind as $user to LDAP server</p>\n";
            ldap_close($ldap);
            $ldap = '';
        } elseif (empty($user) && !ldap_bind($ldap)) {
            echo "<p>unable to bind anonymously to LDAP server</p>\n";
            ldap_close($ldap);
            $ldap = '';
        }
        if ($ldap) {
            $result = ldap_search($ldap, $basedn, $filter);
            if ($result) {
                echo '<p>search returned ' . ldap_count_entries($ldap, $result) . " entries</p>\n";
                $info = ldap_get_entries($ldap, $result);
                for ($i = 0; $i < $info['count']; $i++) {
                    echo '<p>dn is: ' . $info[$i]['dn'] . '<br />';
                    echo 'first cn entry is: ' . $info[$i]['cn'][0] . '<br />';
                    echo 'first mail entry is: ' . $info[$i]['mail'][0] . '</p>';
                    if ($i >= 10) {
                        echo '<p>(only first 10 entries displayed)</p>';
                        break;
                    }
                }
            } else {
                echo '<p>unable to search LDAP server</p>';
            }
        }
    } else {
        echo '<p>unable to connect to LDAP server</p>';
    }
} else {
    ?>
<form name="form1" method="post" action="test.php">
<table>
<tr><td align="right">Server</td><td><input type="text" name="server" /></td></tr>
<tr><td align="right">Port</td><td><input type="text" name="port" /></td><td>(defaults to "389")</td></tr>
<tr><td align="right">Base DN</td><td><input type="text" name="basedn" /></td><td>(e.g. "dc=example,dc=com")</td></tr>
<tr><td align="right">User</td><td><input type="text" name="user" /></td><td>(leave blank for anonymous)</td></tr>
<tr><td align="right">Password</td><td><input type="password" name="passwd" /></td></tr>
<tr><td align="right">Filter</td><td><input type="text" name="filter" /></td><td>(e.g. "cn=Babs Jensen")</td></tr>
<tr><td></td><td><input type="submit" name="f_submit" value="Submit" /><input type="reset" name="f_reset" value="Reset" /></td></tr>
</table>
</form>
<?php } ?>

</td></tr>
</table>

<?php
require TEST_TEMPLATES . 'footer.inc';
