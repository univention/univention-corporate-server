#!/kolab/bin/php
<?php
/**
 * $Horde: framework/install-packages.php,v 1.13 2004/04/07 17:43:41 chuck Exp $
 *
 * This script iterates each directory and forces an install from the
 * package.xml file for each package.
 *
 * @package Horde_Framework
 */

/* Don't die if time limit exceeded. */
set_time_limit(0);

/* Get any arguments. */
require_once 'Console/Getopt.php';
$args = Console_Getopt::readPHPArgv();
$options = Console_Getopt::getopt($args, 'd:c:', array('install-dir=', 'config='));
if (PEAR::isError($options)) {
    echo "Bad option\n";
    exit;
}

/* Set these options to empty by default. */
$install_dir = '';
$config_file = '';
foreach ($options[0] as $option) {
    switch ($option[0]) {
    case 'd':
    case '--install-dir':
        /* Alternate install directory requested. */
        $install_dir = ' -d php_dir=' . $option[1] .
                       ' -d test_dir=' . $option[1] . '/tests' .
                       ' -d doc_dir=' . $option[1] . '/doc' .
                       ' -d data_dir=' . $option[1] . '/data' .
                       ' -d bin_dir=' . $option[1] . '/bin';
        break;
    case 'c':
    case '--config':
        /* Alternate config file requested. */
        $config_file = ' -c ' . $option[1];
    }
}

/* Overwrite old files, ignore dependancies (for ease of ordering),
 * upgrade if already installed, etc. */
$pear = '/kolab/bin/pear' . $config_file . $install_dir . ' install --force --nodeps';

$dir = dirname(__FILE__);
$dh = opendir($dir);
while (($entry = readdir($dh)) !== false) {
    if ($entry == '.' || $entry == '..' || !is_dir($dir . '/' . $entry)) {
        continue;
    }

    $package = $dir . '/' . $entry . '/' . 'package.xml';
    if (file_exists($package)) {
        echo "Installing $entry:\n";
	#echo "$pear \"$package\"\n";
        system("$pear \"$package\"");
        echo "\n\n";
    }
}
closedir($dh);
