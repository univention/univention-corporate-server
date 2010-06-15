#!/usr/bin/php
<?php
/**
 * Copyright 1999 Mike Hardy
 * Copyright 2004 Jan Schneider <jan@horde.org>
 *
 * Licensed under GPL, please see the file COPYING for details on licensing.
 *
 * $Horde: horde/scripts/make-release.php,v 1.17 2004/04/07 14:43:44 chuck Exp $
 *
 * This is a short script to make an "official" Horde or application release
 *
 * This script relies on a few things.
 *
 * 1) The file containing the version string is:
 *         <module>/lib/version.php
 * 2) The tag to use in the source is:
 *         <module>_<major>_<minor>_<patch>[_<text>]
 * 3) The directory the source should be packaged from is:
 *         <module>-<major>.<minor>.<patch>[-<text>]
 * 4) The version to put into the version file in CVS when done is:
 *         <major>.<minor>.<patch+1>-cvs unless there was [-<text>],
 *         then just <major>.<minor>.<patch>-cvs
 * 5) It expects the version file's version line to look like this:
 *        <?php define('<MODULE>_VERSION', '<version>') ?>
 * 6) It expects that you have CVS all set up in the shell you're using.
 *         This includes all of the password stuff...
 * 7) The changelog file is:
 *         <module>/docs/CHANGES
 * 8) The release notes are in:
 *         <module>/docs/RELEASE_NOTES
 */

require 'Horde/Util.php';
require 'Horde/RPC.php';
require 'Horde/MIME/Message.php';

// Create a class instance
$tarball = &new Tarball();

// Get all the arguments from the command-line
$tarball->getArguments();

// Make sure they are sane
$tarball->checkArguments();

// Do testing (development only)
$tarball->test();

// Check for running as root, set umask, etc.
$tarball->checkSetSystem();

// Set all of the version strings we're going to need for tags, source, etc
$tarball->setVersionStrings();

// Check out the source we're going to release
$tarball->checkOutTag($tarball->options['branch'], $tarball->directoryName);

// Check out the framework module if necessary
$tarball->checkOutFramework($tarball->options['branch'], $tarball->directoryName);

// Update the version file with the release version
$tarball->updateVersionFile($tarball->directoryName, $tarball->sourceVersionString);

// Tag the source in the release directory with the correct versioned tag
$tarball->tagSource();

// Get version number of CHANGES file
$tarball->saveChangelog();

// Clean up all the non-tarball-bound directories so the package is clean
$tarball->cleanDirectories($tarball->directoryName);

if ($tarball->oldVersion) {

    // Check out the next-lowest-patch-level
    $tarball->checkOutTag($tarball->oldTagVersionString, $tarball->oldDirectoryName);

    // Get version number of CHANGES file
    $tarball->saveChangelog(true);

}

// If we have a lower patch-level on this tree, make a diff
if ($tarball->makeDiff) {

    // Clean all the non-tarball-bound directories out of it
    $tarball->cleanDirectories($tarball->oldDirectoryName);

    // Make a diff of the two cleaned releasable directories now
    $tarball->diff();

}

if ($tarball->oldVersion) {

    // Clean the directory out
    $tarball->deleteDirectory($tarball->oldDirectoryName);

}

// Make the tarball now
$tarball->makeTarball();

// Clean all the old directories out
$tarball->deleteDirectory($tarball->directoryName);

// Put tarball up on the server
$tarball->upload();

// Check the new source out again so we can change the string post-tarball
$tarball->checkOutTag($tarball->options['branch'], $tarball->directoryName);
$tarball->updateVersionFile($tarball->directoryName, $tarball->newSourceVersionString);
$tarball->updateSentinel();

// Clean this directory up now
$tarball->deleteDirectory($tarball->directoryName);

// Announce release on mailing lists and freshmeat.
$tarball->announce();

// Should be all done
exit;


/***************************************************************
*
*  There's no algorithmic logic below here, just implementation
*
***************************************************************/

class Tarball {

    /**
     * Default options.
     * @var array $options
     */
    var $options = array('test' => false,
                         'nocommit' => false, 
                         'noftp' => false, 
                         'noannounce' => false);

    /**
     * Version number of release.
     * @var string $sourceVersionString
     */
    var $sourceVersionString;

    /**
     * Version number of previous release.
     * @var string $oldVersionString
     */
    var $oldSourceVersionString;

    /**
     * Version number of next release.
     * @var string $newSourceVersionString
     */
    var $newSourceVersionString;

    /**
     * CVS tag of release.
     * @var string $tagVersionString
     */
    var $tagVersionString;

    /**
     * CVS tag of previous release.
     * @var string $oldTagVersionString
     */
    var $oldTagVersionString;

    /**
     * Revision number of CHANGES file.
     * @var string $changelogVersion
     */
    var $changelogVersion;

    /**
     * Revision number of previous CHANGES file.
     * @var string $changelogVersion
     */
    var $oldChangelogVersion;

    /**
     * Directory name of unpacked tarball.
     * @var string $directoryName
     */
    var $directoryName;

    /**
     * Directory name of unpacked previous tarball.
     * @var string $oldDirectoryName
     */
    var $oldDirectoryName;

    /**
     * Filename of the tarball.
     * @var string $tarballName
     */
    var $tarballName;

    /**
     * MD5 sum of the tarball.
     * @var string $tarballMD5
     */
    var $tarballMD5;

    /**
     * Whether or not to create a patch file.
     * @var boolean $makeDiff
     */
    var $makeDiff = false;

    /**
     * Whether or not we have an old version to compare against.
     * @var boolean $oldVersion
     */
    var $oldVersion = false;

    /**
     * Filename of the gzip'ed patch file (without .gz extension).
     * @var string $patchName;
     */
    var $patchName;

    /**
     * MD5 sum of the patch file.
     * @var string $patchMD5
     */
    var $patchMD5;

    /**
     * Whether or not this is a final release version.
     * @var boolean $latest
     */
    var $latest = true;

    // Load the configuration
    function Tarball()
    {
        require dirname(__FILE__) . '/make-release-conf.php';
        $cvsroot = getenv('CVSROOT');
        if (empty($cvsroot)) {
            putenv('CVSROOT=:ext:' . $this->options['horde']['user'] . '@cvs.horde.org:/repository');
        }
    }


    // Delete the directory given as an argument
    function deleteDirectory($directory)
    {
        print "Deleting directory $directory\n";
        system("rm -rf $directory");
    }


    // tar and gzip the directory given as an argument
    function makeTarball()
    {
        print "Setting owner/group to 0/0\n";
        system("chown -R 0:0 $this->directoryName");

        print "Making tarball\n";
        $this->tarballName = $this->directoryName . '.tar.gz';
        if (file_exists($this->tarballName)) {
            unlink($this->tarballName);
        }
        system("tar -zcf $this->tarballName $this->directoryName");
        exec($this->options['md5'] . ' ' . $this->tarballName, $this->tarballMD5);
    }


    // Label all of the source here with the new label given as an argument
    function tagSource()
    {
        if (!$this->options['nocommit']) {
            print "Tagging source in $this->directoryName with tag {$this->tagVersionString}\n";
            system("cd {$this->directoryName};cvs tag -F $this->tagVersionString > /dev/null 2>&1");
        } else {
            print "NOT tagging source in $this->directoryName (would have been tag {$this->tagVersionString})\n";
        }
    }


    // Make a diff of the two directories given as arguments
    function diff()
    {
        $this->patchName = 'patch-' . $this->options['module'] . '-' . $this->oldSourceVersionString . '-' . $this->sourceVersionString;
        print "Making diff between $this->oldDirectoryName and $this->directoryName\n";
        system("diff -uNr $this->oldDirectoryName $this->directoryName > $this->patchName");
        system("gzip -9f $this->patchName");
        exec($this->options['md5'] . ' ' . $this->patchName . '.gz', $this->patchMD5);
    }


    // Change the version file for the module in the directory specified to the version specified
    function updateVersionFile($directory, $version_string)
    {
        $module = $this->options['module'];
        $all_caps_module = strtoupper($module);
        print "Updating version file for $module\n";

        // construct the filenames
        $filename_only = 'version.php';
        $filename = $directory . '/lib/' . $filename_only;
        $newfilename = $filename . '.new';

        $oldfp = fopen($filename, 'r');
        $newfp = fopen($newfilename, 'w');
        while ($line = fgets($oldfp)) {
            if (strstr($line, 'VERSION')) {
                fwrite($newfp, "<?php define('{$all_caps_module}_VERSION', '$version_string') ?>\n");
            } else {
                fwrite($newfp, $line);
            }
        }
        fclose($oldfp);
        fclose($newfp);

        system("mv -f $newfilename $filename");
        if (!$this->options['nocommit']) {
            system("cd $directory/lib/; cvs commit -f -m \"Tarball script: building new $module release - $version_string\" $filename_only > /dev/null 2>&1");
        }
    }


    // Update the CHANGES file with the new version number
    function updateSentinel()
    {
        $module = $this->options['module'];
        $all_caps_module = strtoupper($module);
        print "Updating sentinel file for $module\n";

        // construct the filenames
        $filename_only = 'CHANGES';
        $filename = $this->directoryName . '/docs/' . $filename_only;
        $newfilename = $filename . '.new';

        $version = 'v' . substr($this->newSourceVersionString, 0, strpos($this->newSourceVersionString, '-'));

        $oldfp = fopen($filename, 'r');
        $newfp = fopen($newfilename, 'w');
        fwrite($newfp, str_repeat('-', strlen($version)) . "\n$version\n" .
               str_repeat('-', strlen($version)) . "\n\n\n");
        while ($line = fgets($oldfp)) {
            fwrite($newfp, $line);
        }
        fclose($oldfp);
        fclose($newfp);

        system("mv -f $newfilename $filename");
        if (!$this->options['nocommit']) {
            system("cd {$this->directoryName}/docs/; cvs commit -f -m \"Tarball script: building new $module release - {$this->newSourceVersionString}\" $filename_only > /dev/null 2>&1");
        }
    }


    // get and save the revision number of the CHANGES file
    function saveChangelog($old = false)
    {
        if ($old) {
            $directory = $this->oldDirectoryName;
        } else {
            $directory = $this->directoryName;
            @include "./$directory/docs/RELEASE_NOTES";
        }
        exec("cd $directory/docs/; cvs status CHANGES", $output);
        foreach ($output as $line) {
            if (preg_match('/Repository revision:\s+([\d.]+)/', $line, $matches)) {
                if ($old) {
                    $this->oldChangelogVersion = $matches[1];
                } else {
                    $this->changelogVersion = $matches[1];
                }
                break;
            }
        }
    }


    // work through the source directory given, cleaning things up by removing
    // directories and files we don't want in the tarball
    function cleanDirectories($directory)
    {
        print "Cleaning source tree\n";
        $directories = explode("\n", `find $directory -type d \\( -name CVS -o -name packaging \\) -print | sort -r`);
        foreach ($directories as $dir) {
            system("rm -rf $dir");
        }
        $cvsignores = explode("\n", `find $directory -name .cvsignore -print`);
        foreach ($cvsignores as $file) {
            if (!empty($file)) {
                unlink($file);
            }
        }
    }


    // Check out the tag we've been given to work with and move it to the directory name given
    function checkOutTag($mod_version, $directory)
    {
        $module = $this->options['module'];

        // Use CVS to check the source out
        if ($mod_version == 'HEAD') {
            print "Checking out HEAD for $module\n";
            system("cvs co -P $module > /dev/null 2>&1");
        } elseif ($mod_version == 'IMP_2_2_7') {
            print "Checking out tag $mod_version for $module (by date)\n";
            system("cvs co -P -rSTABLE_2_2 -D'2001-11-11' $module > /dev/null 2>&1");
            system("cd $module/lib/; cvs up -r1.1.2.13 version.php > /dev/null 2>&1");
        } else {
            print "Checking out tag $mod_version for $module\n";
            system("cvs co -P -r$mod_version $module > /dev/null 2>&1");
        }

        // Move the source into the directory specified
        print "Moving $module to $directory\n";
        if (@is_dir($directory)) {
            system("rm -rf $directory");
        }
        system("mv -f $module $directory");
    }


    // Checkout and install framework
    function checkOutFramework($mod_version, $directory)
    {
        if ($this->options['module'] == 'horde' &&
            ($mod_version == 'HEAD' || strstr($mod_version, 'FRAMEWORK'))) {
            if ($mod_version == 'HEAD') {
                print "Checking out HEAD for framework\n";
            } else {
                print "Checking out tag $mod_version for framework\n";
            }
            system("cd $directory; cvs co -P -r$mod_version framework > /dev/null 2>&1; cd ..");
            print "Installing framework packages\n";
            $dir = dirname(__FILE__);
            system("php $dir/create-symlinks.php --copy --src=$directory/framework --dest=$directory/lib; rm -r $directory/framework");

            print "Setting HORDE_LIBS\n";
            $filename = $directory . '/lib/core.php';
            $newfilename = $filename . '.new';
            $oldfp = fopen($filename, 'r');
            $newfp = fopen($newfilename, 'w');
            while ($line = fgets($oldfp)) {
                fwrite($newfp, str_replace('define(\'HORDE_LIBS\', \'\')', 'define(\'HORDE_LIBS\', dirname(__FILE__) . \'/\')', $line));
            }
            fclose($oldfp);
            fclose($newfp);
            system("mv -f $newfilename $filename");
        }
    }


    // Upload tarball to the FTP server
    function upload()
    {
        $module = $this->options['module'];
        $user = $this->options['horde']['user'];
        $cmd = "chmod 664 /horde/ftp/$module/$this->tarballName;";
        if ($this->makeDiff) {
            $cmd .= " chmod 664 /horde/ftp/$module/patches/$this->patchName.gz;";
        }
        if ($this->latest) {
            $cmd .= " ln -sf $this->tarballName /horde/ftp/$module/$module-latest.tar.gz;";
        }

        if (!$this->options['noftp']) {
            print "Uploading $this->tarballName to $user@dev.horde.org:/horde/ftp/$module/\n";
            system("scp $this->tarballName $user@dev.horde.org:/horde/ftp/$module/");
            if ($this->makeDiff) {
                print "Uploading $this->patchName.gz to $user@dev.horde.org:/horde/ftp/$module/patches/\n";
                system("scp $this->patchName.gz $user@dev.horde.org:/horde/ftp/$module/patches/");
            }
            print "Executing $cmd\n";
            system("ssh -l $user dev.horde.org '$cmd'");
        } else {
            print "NOT uploading $this->tarballName to dev.horde.org:/horde/ftp/$module/\n";
            if ($this->makeDiff) {
                print "NOT uploading $this->patchName.gz to $user@dev.horde.org:/horde/ftp/$module/patches/\n";
            }
            print "NOT executing $cmd\n";
        }
    }


    // check if freshmeat announcement was successful.
    function _fmVerify($fm)
    {
        if (is_a($fm, 'PEAR_Error')) {
            print $fm->getMessage() . "\n";
            return false;
        } elseif (!is_array($fm)) {
            var_dump($fm);
            return false;
        }
        return true;
    }


    // announce release to mailing lists and freshmeat.
    function announce()
    {
        $module = $this->options['module'];
        if (!isset($this->notes)) {
            print "NOT announcing release, RELEASE_NOTES missing.\n";
            return;
        }
        if (!empty($this->options['noannounce'])) {
            print "NOT announcing release on freshmeat.net\n";
        } else {
            print "Announcing release on freshmeat.net\n";
        }
        $fm = Horde_RPC::request(
            'xmlrpc',
            'http://freshmeat.net/xmlrpc/',
            'login',
            array('username' => $this->options['fm']['user'],
                  'password' => $this->options['fm']['password']));
        $announcement = array('SID' => $fm['SID'],
                              'project_name' => $this->notes['fm']['project'],
                              'branch_name' => $this->notes['fm']['branch'],
                              'version' => $this->sourceVersionString,
                              'changes' => $this->notes['fm']['changes'],
                              'release_focus' => (int)$this->notes['fm']['focus'],
                              'url_changelog' => ($this->oldVersion ? "http://cvs.horde.org/diff.php/$module/docs/CHANGES?r1={$this->oldChangelogVersion}&r2={$this->changelogVersion}&ty=h" : ''),
                              'url_tgz' => "ftp://ftp.horde.org/pub/$module/{$this->tarballName}");
        if ($this->_fmVerify($fm)) {
            if (!empty($this->options['noannounce'])) {
                print "Announcement data:\n";
                print_r($announcement);
            } else {
                $fm = Horde_RPC::request(
                    'xmlrpc',
                    'http://freshmeat.net/xmlrpc/',
                    'publish_release',
                    $announcement);
                $this->_fmVerify($fm);
            }
        }

        $ml = $module;
        if ($ml == 'accounts' || $ml == 'forwards' ||
            $ml == 'passwd' || $ml == 'vacation') {
            $ml = 'sork';
        }
        $to = "announce@lists.horde.org, $ml@lists.horde.org";
        if (!$this->latest) {
            $to .= ', i18n@lists.horde.org';
        }

        if (!empty($this->options['noannounce'])) {
            print "NOT announcing release on $to\n";
        } else {
            print "Announcing release to $to\n";
        }

        // Building headers
        $subject = $this->notes['name'] . ' ' . $this->sourceVersionString;
        if ($this->latest) {
            $subject .= ' (final)';
        }
        $headers = array('From' => $this->options['ml']['from'],
                         'To' => $to,
                         'Subject' => $subject);

        // Building message text
        $body = $this->notes['ml']['changes'];
        if ($this->oldVersion) {
            $body .= "\n\n" .
                sprintf('The full list of changes (from version %s) can be viewed here:', $this->oldSourceVersionString) .
                "\n\n" .
                sprintf('http://cvs.horde.org/diff.php/%s/docs/CHANGES?r1=%s&r2=%s&ty=h', $module, $this->oldChangelogVersion, $this->changelogVersion);
        }
        $body .= "\n\n" .
            sprintf('The %s %s distribution is available from the following locations:', $this->notes['name'], $this->sourceVersionString) .
            "\n\n" .
            sprintf('    ftp://ftp.horde.org/pub/%s/%s', $module, $this->tarballName) . "\n" .
            sprintf('    http://ftp.horde.org/pub/%s/%s', $module, $this->tarballName);
        if ($this->makeDiff) {
            $body .= "\n\n" .
                sprintf('Patches against version %s are available at:', $this->oldSourceVersionString) .
                "\n\n" .
                sprintf('    ftp://ftp.horde.org/pub/%s/patches/%s.gz', $module, $this->patchName) . "\n" .
                sprintf('    http://ftp.horde.org/pub/%s/patches/%s.gz', $module, $this->patchName);
        }
        $body .= "\n\n" .
            'Or, for quicker access, download from your nearest mirror:' .
            "\n\n" .
            '    http://www.horde.org/mirrors.php' .
            "\n\n" .
            'MD5 sums for the packages are as follows:' .
            "\n\n" .
            '    ' . $this->tarballMD5[0] . "\n" .
            '    ' . $this->patchMD5[0] .
            "\n\n" .
            'Have fun!' .
            "\n\n" .
            'The Horde Team.';

        if (!empty($this->options['noannounce'])) {
            print "Message headers:\n";
            print_r($headers);
            print "Message body:\n$body\n";
            return;
        }

        // Building and sending message
        $message = &new MIME_Message('lists.horde.org');
        $part = &new MIME_Part('text/plain',
                               $body,
                               'iso-8859-1');
        $message->addPart($part);
        $headers = $message->encode($headers, 'iso-8859-1');

        $msg = $message->toString();
        if (substr($msg, -1) != "\n") {
            $msg .= "\n";
        }

        require_once 'Mail.php';
        $mailer = &Mail::factory($this->options['mailer']['type'], $this->options['mailer']['params']);
        $result = $mailer->send(MIME::encodeAddress($to), $headers, $msg);
        if (is_a($result, 'PEAR_Error')) {
            print $result->getMessage() . "\n";
        }
    }


    // Do testing (development only)
    function test()
    {
        if (!$this->options['test']) {
            return;
        }

        print "options['version']={$this->options['version']}\n";
        print "options['oldversion']={$this->options['oldversion']}\n";
        print "options['module']={$this->options['module']}\n";

        $this->setVersionStrings();

        print "makeDiff={$this->makeDiff}\n";
        print "oldVersion={$this->oldVersion}\n";
        print "directoryName={$this->directoryName}\n";
        if ($this->oldVersion) {
            print "oldDirectoryName={$this->oldDirectoryName}\n";
        }
        print "tagVersionString={$this->tagVersionString}\n";
        if ($this->oldVersion) {
            print "oldTagVersionString={$this->oldTagVersionString}\n";
        }
        print "sourceVersionString={$this->sourceVersionString}\n";
        if ($this->oldVersion) {
            print "oldSourceVersionString={$this->oldSourceVersionString}\n";
        }
        print "newSourceVersionString={$this->newSourceVersionString}\n";
        exit(0);
    }


    // Set the version strings to use given the arguments
    function setVersionStrings() {
        $ver = explode('.', $this->options['version']);
        if (preg_match('/(\d+)\-(.*)/', $ver[count($ver) - 1], $matches)) {
            $ver[count($ver) - 1] = $matches[1];
            $plus = $matches[2];
        }
        if (count($ver) > 2 && $ver[count($ver) - 1] == '0') {
            die("version {$this->options['version']} should not have the trailing 3rd-level .0\n");
        }
        
        // check if --oldversion is empty or 0
        if (!empty($this->options['oldversion'])) {
            $this->oldVersion = true;
        }
        $oldver = explode('.', $this->options['oldversion']);

        // set the string to use as the tag name in CVS
        $this->tagVersionString = strtoupper($this->options['module'] . '_' . implode('_', $ver));
        if (isset($plus)) {
            $this->tagVersionString .= '_' . $plus;
        }

        // create patches only if not a major version change
        if ($ver[0] == $oldver[0]) {
            $this->makeDiff = true;
        }

        // is this really a production release?
        if (isset($plus) && !preg_match('/^pl\d/', $plus)) {
            $this->latest = false;
            $this->makeDiff = false;
        }

        // set the string to insert into the source version file
        $this->sourceVersionString = implode('.', $ver);
        if (isset($plus)) {
            $this->sourceVersionString .= '-' . $plus;
        }

        // set the string to be used for the directory to package from
        $this->directoryName = $this->options['module'] . '-' . $this->sourceVersionString;

        if ($this->oldVersion) {
            $this->oldSourceVersionString = implode('.', $oldver);
            $this->oldTagVersionString = strtoupper($this->options['module'] . '_' . implode('_', $oldver));
            $this->oldDirectoryName = $this->options['module'] . '-' . $this->oldSourceVersionString;
        }

        // set the name of the string to put into the source version file when done
        if (!isset($plus)) {
            while (count($ver) < 3) {
                array_push($ver, '0');
            }
            $ver[count($ver) - 1] += 1;
        }
        $this->newSourceVersionString = implode('.', $ver) . '-cvs';
    }


    // Get all of the command-line arguments from the user
    function getArguments() {
        global $argv;

        // Parse the command-line arguments
        foreach ($argv as $arg) {
            // Skip script name
            if (basename($arg) == basename(__FILE__)) {
                continue;
            }

            // Check to see if they gave us a module
            if (preg_match('/--module=(.*)/', $arg, $matches)) {
                $this->options['module'] = $matches[1];

            // Check to see if they tell us the version of the tarball to make
            } elseif (preg_match('/--version=(.*)/', $arg, $matches)) {
                $this->options['version']= $matches[1];

            // Check to see if they tell us the last release version
            } elseif (preg_match('/--oldversion=(.*)/', $arg, $matches)) {
                $this->options['oldversion']= $matches[1];

            // Check to see if they tell us which branch to work with
            } elseif (preg_match('/--branch=(.*)/', $arg, $matches)) {
                $this->options['branch']= $matches[1];

            // Check to see if they tell us not to commit or tag
            } elseif (strstr($arg, '--nocommit')) {
                $this->options['nocommit']= true;

            // Check to see if they tell us not to upload
            } elseif (strstr($arg, '--noftp')) {
                $this->options['noftp']= true;

            // Check to see if they tell us not to announce
            } elseif (strstr($arg, '--noannounce')) {
                $this->options['noannounce']= true;

            // Check to see if they tell us to test (for development only)
            } elseif (strstr($arg, '--test')) {
                $this->options['test']= true;
                // safety first
                $this->options['nocommit'] = true;
                $this->options['noftp'] = true;
                $this->options['noannounce'] = true;

            // We have no idea what this is
            } else {
                $this->print_usage('You have used unknown arguments: ' . $arg);
                exit;
            }
        }
    }


    // Check the command-line arguments and set some internal defaults
    function checkArguments() {
        // Make sure that we have a module defined
        if (!isset($this->options['module'])) {
            $this->print_usage('You must define which module to package.');
            exit;
        }

        // Let's make sure that there are valid version strings in here...
        if (!isset($this->options['version'])) {
            $this->print_usage('You must define which version to package.');
            exit;
        }
        if (!preg_match('/\d+\.\d+.*/', $this->options['version'])) {
            $this->print_usage('Incorrect version string.');
            exit;
        }
        if (!isset($this->options['oldversion'])) {
            $this->print_usage('You must define last release\'s version.');
            exit;
        }
        if (!preg_match('/\d+(\.\d+.*)?/', $this->options['oldversion'])) {
            $this->print_usage('Incorrect old version string.');
            exit;
        }

        // Make sure we have a horde.org user
        if (empty($this->options['horde']['user'])) {
            $this->print_usage('You must define a horde.org user.');
            exit;
        }

        // If there is no branch defined, we're using the tip revisions.
        // These releases are always developmental, and should use the HEAD "branch" name.
        if (!isset($this->options['branch'])) {
            $this->options['branch'] = 'HEAD';
        }
    }


    // Check the command-line arguments and set some internal defaults
    function checkSetSystem() {

        // Set umask
        umask(022);

        // Make sure we're running as root (so we can chown/chmod)
        if (posix_getuid() != 0) {
            die('This script must run be as root');
        }

    }


    // Show people how to use the damned thing
    function print_usage($message) {

        print "\n***  ERROR: $message  ***\n";

        print <<<USAGE

make-tarball.php: Horde release generator.

   This script takes as arguments the module to make a release of, the
   version of the release, and the branch:

      ./make-tarball.php --module=<name> --version=xx.yy[.zz[-<string>]]
                         --oldversion=xx[.yy[.zz[-<string>]]]
                         [--branch=<branchname>] [--nocommit] [--noftp]

   If you omit the branch, it will implicitly work with the HEAD branch.
   If you release a new major version use the --oldversion=0 option.
   Use the --nocommit option to do a test build (without touching the CVS
   repository). Use the --noftp option to not upload any files on the FTP
   server. Use the --noannounce option to not send any release announcements.

   Some examples would be:

   To make a new development release of Horde:
      ./make-tarball.php --module=horde --version=2.1-dev --oldversion=2.0

   To make a new stable release of IMP:
      ./make-tarball.php --module=imp --version=3.0 --oldversion=2.3.7 \
        --branch=RELENG_3

   To make a brand new alpha relase of Luxor:
      ./make-tarball.php --module=luxor --version=1.0-alpha1 --oldversion=0

USAGE;
    }

}
