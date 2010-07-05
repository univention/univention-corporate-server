<?php
/**
 * $Horde: turba/test.php,v 1.9.10.11 2009-03-25 23:06:04 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Brent J. Nordquist <bjn@horde.org>
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

/* PEAR packages. */
$pear_list = array(
    'Net_LDAP' => array(
        'path' => 'Net/LDAP.php',
        'error' => 'Net_LDAP is required when doing schema checks with LDAP address books.',
    ),
);

/* Get the status output now. */
$module_output = $horde_test->phpModuleCheck($module_list);
$pear_output = $horde_test->PEARModuleCheck($pear_list);

?>

<h1>PHP Module Capabilities</h1>
<ul>
 <?php echo $module_output ?>
</ul>

<h1>PEAR</h1>
<ul>
 <?php echo $pear_output ?>
</ul>

<h1>PHP LDAP Support Test</h1>
<?php

$server = isset($_POST['server']) ? $_POST['server'] : ''; // 'server.example.com';
$port = isset($_POST['port']) ? $_POST['port'] : ''; // '389';
$basedn = isset($_POST['basedn']) ? $_POST['basedn'] : ''; // 'dc=example,dc=com';
$user = isset($_POST['user']) ? $_POST['user'] : '';     // 'user';
$passwd = isset($_POST['passwd']) ? $_POST['passwd'] : ''; // 'password';
$filter = isset($_POST['filter']) ? $_POST['filter'] : ''; // 'cn=Babs Jensen';
$proto = isset($_POST['version']) ? $_POST['version'] : ''; // 'LDAPv3';

if (!empty($server) && !empty($basedn) && !empty($filter)) {
    if (empty($port)) {
        $port = '389';
    }
    echo 'server="', htmlspecialchars($server), '" basedn="', htmlspecialchars($basedn), '" filter="', htmlspecialchars($filter), '"<br />';
    if ($user) {
        echo 'bind as user="', htmlspecialchars($user), '"<br />';
    } else {
        echo 'bind anonymously<br />';
    }
    $ldap = ldap_connect($server, $port);
    if ($ldap) {
        if (!empty($proto) && ($proto == '3')) {
            ldap_set_option($ldap, LDAP_OPT_PROTOCOL_VERSION, 3);
        }
        if (!empty($user) && !ldap_bind($ldap, $user, $passwd)) {
            echo '<p>unable to bind as ' . htmlspecialchars($user) . ' to LDAP server</p>';
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
<tr><td align="right"><label for="server">Server</label></td><td><input type="text" id="server" name="server" /></td></tr>
<tr><td align="right"><label for="port">Port</label></td><td><input type="text" id="port" name="port" /></td><td>(defaults to "389")</td></tr>
<tr><td align="right"><label for="basedn">Base DN</label></td><td><input type="text" id="basedn" name="basedn" /></td><td>(e.g. "dc=example,dc=com")</td></tr>
<tr><td align="right"><label for="user">User</label></td><td><input type="text" id="user" name="user" /></td><td>(leave blank for anonymous)</td></tr>
<tr><td align="right"><label for="passwd">Password</label></td><td><input type="password" id="passwd" name="passwd" /></td></tr>
<tr><td align="right"><label for="filter">Filter</label></td><td><input type="text" id="filter" name="filter" /></td><td>(e.g. "cn=Babs Jensen")</td></tr>
<tr><td align="right"><label for="proto">Protocol</label></td><td><select id="version" name="version"><option value="2">LDAPv2 (Deprecated)</option><option value="3" selected="selected">LDAPv3</option></td><td>(LDAP protocol version)</select></td></tr>
<tr><td></td><td><input type="submit" name="f_submit" value="Submit" /><input type="reset" name="f_reset" value="Reset" /></td></tr>
</table>
</form>
<?php } ?>

<?php
require TEST_TEMPLATES . 'footer.inc';
