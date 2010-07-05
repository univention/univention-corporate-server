--TEST--
Automatic webroot detection
--FILE--
<?php


function _detect_webroot()
{
    // $FILE and $DIRECTORY_SEPARATOR must be replaced with __FILE__ and
    // DIRECTORY_SEPARATOR in the real implementation in registry.php.
    global $FILE, $DIRECTORY_SEPARATOR;

    // Note for Windows users: the below assumes that your PHP_SELF variable
    // uses forward slashes. If it does not, you'll have to tweak this.
    if (isset($_SERVER['SCRIPT_URL']) || isset($_SERVER['SCRIPT_NAME'])) {
        $path = empty($_SERVER['SCRIPT_URL']) ?
            $_SERVER['SCRIPT_NAME'] :
            $_SERVER['SCRIPT_URL'];
        $hordedir = str_replace($DIRECTORY_SEPARATOR, '/', $FILE);
        $hordedir = basename(preg_replace(';/config/registry.php$;', '', $hordedir));
        if (preg_match(';/' . $hordedir . ';', $path)) {
            $webroot = preg_replace(';/' . $hordedir . '.*;', '/' . $hordedir, $path);
        } else {
            $webroot = '';
        }
    } elseif (isset($_SERVER['PHP_SELF'])) {
        $webroot = preg_split(';/;', $_SERVER['PHP_SELF'], 2, PREG_SPLIT_NO_EMPTY);
        $webroot = strstr(dirname($FILE), $DIRECTORY_SEPARATOR . array_shift($webroot));
        if ($webroot !== false) {
            $webroot = preg_replace(array('/\\\\/', ';/config$;'), array('/', ''), $webroot);
        } elseif ($webroot === false) {
            $webroot = '';
        } else {
            $webroot = '/horde';
        }
    } else {
        $webroot = '/horde';
    }

    return $webroot;
}

$DIRECTORY_SEPARATOR = '/';
$FILE = '/home/jan/horde/config/registry.php';
$_SERVER = array('SCRIPT_NAME' => '/horde/webroot.php');
var_dump(_detect_webroot());
$_SERVER = array('SCRIPT_URL' => '/horde/webroot.php');
var_dump(_detect_webroot());
$_SERVER = array('PHP_SELF' => '/horde/webroot.php');
var_dump(_detect_webroot());
$FILE = '/var/www/horde3/config/registry.php';
$_SERVER = array('SCRIPT_NAME' => '/webroot.php',
                 'PHP_SELF' => '/webroot.php');
var_dump(_detect_webroot());
$FILE = '/var/www/horde/config/registry.php';
var_dump(_detect_webroot());
$FILE = '/Users/foo/Sites/hordehead/config/registry.php';
$_SERVER = array('SCRIPT_URL' => '/~foo/hordehead/webroot.php',
                 'SCRIPT_NAME' => '/~foo/hordehead/webroot.php',
                 'PHP_SELF' => '/~foo/hordehead/webroot.php');
var_dump(_detect_webroot());
$FILE = '/var/www/html/config/registry.php';
$_SERVER = array('SCRIPT_URL' => '/webroot.php',
                 'SCRIPT_NAME' => '/webroot.php',
                 'PHP_SELF' => '/webroot.php');
var_dump(_detect_webroot());


// Windows tests
$DIRECTORY_SEPARATOR = '\\';
$FILE = 'c:\inetpub\wwwroot\horde\config\registry.php';
$_SERVER = array('SCRIPT_NAME' => '/horde/webroot.php',
                 'PHP_SELF' => '/horde/webroot.php');
var_dump(_detect_webroot());
$FILE = 'C:\Inetpub\vhosts\example.com\subdomain\webmail\config\registry.php';
$_SERVER = array('SCRIPT_NAME' => '/webroot.php',
                 'PHP_SELF' => '/webroot.php');
var_dump(_detect_webroot());

?>
--EXPECT--
string(6) "/horde"
string(6) "/horde"
string(6) "/horde"
string(0) ""
string(0) ""
string(15) "/~foo/hordehead"
string(0) ""
string(6) "/horde"
string(0) ""
