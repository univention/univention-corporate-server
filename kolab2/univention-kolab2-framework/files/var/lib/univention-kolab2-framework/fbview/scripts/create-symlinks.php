#!/usr/bin/php
<?php

// Find the base file path of Horde.
@define('HORDE_BASE', dirname(__FILE__) . '/..');

// Configuration.
// Enter directories without trailing slashes.

// The directory with the CVS checkout.
$srcDir = HORDE_BASE . '/framework';

// The directory where the softlinks are created.
// This is also the directory which you should put in your include path
// after creating the links.
$destDir = HORDE_BASE . '/libs';

/**
 * This script creates softlinks to the library files you retrieved from
 * the CVS "framework" module.
 *
 * It creates the same directory structure the packages would have if they
 * were installed with "pear install package.xml".
 * For creating this structure it uses the information given in the
 * package.xml files inside each package directory.
 *
 * $Horde: horde/scripts/create-symlinks.php,v 1.10 2004/02/14 02:00:17 chuck Exp $
 *
 * Copyright 2002 Wolfram Kriesing <wolfram@kriesing.de>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Wolfram Kriesing <wolfram@kriesing.de>
 * @author Jan Schneider <jan@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since Horde 3.0
 */

// Do CLI checks and environment setup first.
require_once $srcDir . '/CLI/CLI.php';

// Make sure no one runs this from the web.
if (!Horde_CLI::runningFromCLI()) {
    exit("Must be run from the command line\n");
}

// Load the CLI environment - make sure there's no time limit, init
// some variables, etc.
Horde_CLI::init();

require_once 'Tree/Tree.php';

$copy = false;
if (isset($argv)) {
    while ($arg = array_shift($argv)) {
        if ($arg == '--copy') {
            $copy = true;
        } elseif (strstr($arg, '--src')) {
            list(,$srcDir) = explode('=', $arg);
        } elseif (strstr($arg, '--dest')) {
            list(,$destDir) = explode('=', $arg);
        }
    }
 }

$linker = &new Linker($copy);
if ($handle = opendir($srcDir)) {
    while ($file = readdir($handle)) {
        if ($file != '.' &&
            $file != '..' &&
            $file != 'CVS' &&
            is_dir("$srcDir/$file")) {
            $linker->process("$srcDir/$file", $destDir);
        }
    }
    closedir($handle);
 }

echo "\n";

//  possible xml-structs
//  <filelist>
//      <dir name="/" baseinstalldir="XML">
//          <file role="php">Parser.php</file>
//          <file role="php" name="RSS.php" />
//      </dir>
//  </filelist>
//
//  <filelist>
//      <file role="php" baseinstalldir="/">DB.php</file>
//      <dir name="DB">
//          <file role="php">common.php</file>
//      </dir>
//  </filelist>
class Linker {

    var $_srcDir;

    var $_baseInstallDir;

    var $_fileroles = array('php');

    var $_role;

    var $_copy;

    function Linker($copy = false)
    {
        $this->_copy = $copy;
    }

    function process($srcDir, $destDir)
    {
        $this->_srcDir = $srcDir;
        $packageFile = $this->_srcDir . '/package.xml';
        $cli = &Horde_CLI::singleton();

        if (!is_file($packageFile)) {
            $cli->message('No package.xml in ' . $this->_srcDir, 'cli.warning');
            return false;
        }

        $tree = Tree::setupMemory('XML', $packageFile);
        $tree->setup();

        // read package name
        $packageName = trim($tree->getElementContent('/package/name', 'cdata'));
        $cli->writeln("Processing package $packageName.");

        // look for filelist in '/package/release/filelist'
        $filelist = $tree->getElementByPath('/package/release/filelist');

        if ($filelist) {
            // do this better, make the tree class work case insensitive
            $baseInstallDir = $filelist['child']['attributes']['baseinstalldir'];

            $this->_baseInstallDir = $destDir;
            if ($baseInstallDir != '/') {
                $this->_baseInstallDir .= '/' . $baseInstallDir;
            }

            if (!is_dir($this->_baseInstallDir)) {
                require_once 'System.php';
                System::mkdir('-p ' . $this->_baseInstallDir);
            }

            $this->_handleFilelistTag($filelist);
        } else {
            $cli->message('No filelist tag found inside: ' . $packageFile, 'cli.warning');
        }
    }

    function _handleFilelistTag($element, $curDir = '')
    {
        foreach ($element['children'] as $child) {
            switch ($child['name']) {
            case 'file':
                $this->_handleFileTag($child, $curDir);
                break;
            case 'dir':
                $this->_handleDirTag($child, $curDir);
                break;
            default:
                $cli = &Horde_CLI::singleton();
                $cli->message('Got no handler for tag: ' . $child['name'], 'cli-warning');
                break;
            }
        }

    }

    function _handleDirTag($element, $curDir)
    {
        if ($element['attributes']['name'] != '/') {
            if (substr($curDir, -1) != '/') {
                $curDir = $curDir . '/';
            }
            $curDir = $curDir . $element['attributes']['name'];
        }

        if (!empty($element['attributes']['role'])) {
            $this->_role = $element['attributes']['role'];
        }

        if (!is_dir($this->_baseInstallDir . $curDir)) {
            require_once 'System.php';
            System::mkdir('-p ' . $this->_baseInstallDir . $curDir);
        }

        $this->_handleFilelistTag($element, $curDir);
    }

    function _handleFileTag($element, $dir)
    {
        if (!empty($element['attributes']['role'])) {
            $this->_role = $element['attributes']['role'];
        }

        if (!in_array($this->_role, $this->_fileroles)) {
            return;
        }

        if (!empty($element['attributes']['name'])) {
            $filename = $element['attributes']['name'];
        } else {
            $filename = $element['cdata'];
        }
        $filename = trim($filename);

        if ($this->_copy) {
            $cmd = "cp {$this->_srcDir}$dir/$filename {$this->_baseInstallDir}$dir/$filename";
        } else {
            $cmd = "ln -sf {$this->_srcDir}$dir/$filename {$this->_baseInstallDir}$dir/$filename";
        }
        exec($cmd);
    }

}
