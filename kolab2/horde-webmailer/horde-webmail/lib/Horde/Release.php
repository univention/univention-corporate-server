<?php
/**
 * Class to make an "official" Horde or application release.
 *
 * $Horde: framework/Horde/Horde/Release.php,v 1.27.2.12 2009-07-06 18:56:57 chuck Exp $
 *
 * Copyright 1999 Mike Hardy
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Hardy
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Framework
 */
class Horde_Release {

    /**
     * Default options.
     *
     * @var array
     */
    var $options = array(
        'test' => false,
        'nocommit' => false,
        'noftp' => false,
        'noannounce' => false,
        'nofreshmeat' => false,
        'nowhups' => false,
    );

    /**
     * Version number of release.
     *
     * @var string
     */
    var $sourceVersionString;

    /**
     * Version number of previous release.
     *
     * @var string
     */
    var $oldSourceVersionString;

    /**
     * Version number of next release.
     *
     * @var string
     */
    var $newSourceVersionString;

    /**
     * Version number of next release for docs/CHANGES.
     *
     * @var string
     */
    var $newSourceVersionStringPlain;

    /**
     * Major version number of Horde compatible to this release.
     *
     * @var string
     */
    var $hordeVersionString;

    /**
     * Major version number of Horde compatible to the previous release.
     *
     * @var string
     */
    var $oldHordeVersionString;

    /**
     * CVS tag of release.
     *
     * @var string
     */
    var $tagVersionString;

    /**
     * CVS tag of previous release.
     *
     * @var string
     */
    var $oldTagVersionString;

    /**
     * Revision number of CHANGES file.
     *
     * @var string
     */
    var $changelogVersion;

    /**
     * Revision number of previous CHANGES file.
     *
     * @var string
     */
    var $oldChangelogVersion;

    /**
     * Version string to use in Whups
     */
    var $ticketVersion;

    /**
     * Version description to use in Whups
     */
    var $ticketVersionDesc = '';

    /**
     * Directory name of unpacked tarball.
     *
     * @var string
     */
    var $directoryName;

    /**
     * Directory name of unpacked previous tarball.
     *
     * @var string
     */
    var $oldDirectoryName;

    /**
     * Filename of the tarball.
     *
     * @var string
     */
    var $tarballName;

    /**
     * MD5 sum of the tarball.
     *
     * @var string
     */
    var $tarballMD5;

    /**
     * Whether or not to create a patch file.
     *
     * @var boolean
     */
    var $makeDiff = false;

    /**
     * The list of binary diffs.
     *
     * @var array
     */
    var $binaryDiffs = array();

    /**
     * Whether or not we have an old version to compare against.
     *
     * @var boolean
     */
    var $oldVersion = false;

    /**
     * Filename of the gzip'ed patch file (without .gz extension).
     *
     * @var string
     */
    var $patchName;

    /**
     * MD5 sum of the patch file.
     *
     * @var string
     */
    var $patchMD5;

    /**
     * Whether or not this is a final release version.
     *
     * @var boolean
     */
    var $latest = true;

    /**
     * Load the configuration
     */
    function Horde_Release($options = array())
    {
        $this->options = array_merge($this->options, $options);
        $cvsroot = getenv('CVSROOT');
        if (empty($cvsroot)) {
            putenv('CVSROOT=:ext:' . $this->options['horde']['user'] . '@cvs.horde.org:/repository');
        }
        print 'CVSROOT ' . getenv('CVSROOT') . "\n";
        if (!empty($this->options['cvs']['cvs_rsh'])) {
            putenv('CVS_RSH=' . $this->options['cvs']['cvs_rsh']);
        }
        print 'CVS_RSH ' . getenv('CVS_RSH') . "\n";
    }

    /**
     * Delete the directory given as an argument
     */
    function deleteDirectory($directory)
    {
        print "Deleting directory $directory\n";
        system("sudo rm -rf $directory");
    }

    /**
     * tar and gzip the directory given as an argument
     */
    function makeTarball()
    {
        print "Setting owner/group to 0/0\n";
        system("sudo chown -R 0:0 $this->directoryName");

        print "Making tarball\n";
        $this->tarballName = $this->directoryName . '.tar.gz';
        if (file_exists($this->tarballName)) {
            unlink($this->tarballName);
        }
        system("tar -zcf $this->tarballName $this->directoryName");
        exec($this->options['md5'] . ' ' . $this->tarballName, $this->tarballMD5);
    }

    /**
     * Label all of the source here with the new label given as an argument
     */
    function tagSource($directory = null, $version = null)
    {
        if (empty($directory)) {
            $directory = $this->directoryName;
        }
        if (empty($version)) {
            $version = $this->tagVersionString;
        }
        if (!$this->options['nocommit']) {
            print "Tagging source in $directory with tag $version\n";
            system("cd $directory;cvs tag -F $version > /dev/null 2>&1");
        } else {
            print "NOT tagging source in $directory (would have been tag $version)\n";
        }
    }

    /**
     * Make a diff of the two directories given as arguments
     */
    function diff()
    {
        $this->patchName = 'patch-' . $this->oldDirectoryName . str_replace($this->options['module'], '', $this->directoryName);
        print "Making diff between $this->oldDirectoryName and $this->directoryName\n";
        system("diff -uNr $this->oldDirectoryName $this->directoryName > $this->patchName");

        // Search for binary diffs
        $this->binaryDiffs = array();
        $handle = fopen($this->patchName, 'r');
        if ($handle) {
            while (!feof($handle)) {
                // GNU diff reports binary diffs as the following:
                // Binary files ./locale/de_DE/LC_MESSAGES/imp.mo and ../../horde/imp/locale/de_DE/LC_MESSAGES/imp.mo differ
                if (preg_match("/^Binary files (.+) and (.+) differ$/i", rtrim(fgets($handle)), $matches)) {
                    // [1] = oldname, [2] = newname
                    $this->binaryDiffs[] = ltrim(str_replace($this->oldDirectoryName . '/', '', $matches[1]));
                }
            }
            fclose($handle);
        }
        system("gzip -9f $this->patchName");
        exec($this->options['md5'] . ' ' . $this->patchName . '.gz', $this->patchMD5);
    }

    /**
     * Change the version file for the module in the directory specified to
     * the version specified
     */
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

    /**
     * Update the CHANGES file with the new version number
     */
    function updateSentinel()
    {
        $module = $this->options['module'];
        $all_caps_module = strtoupper($module);
        print "Updating CHANGES file for $module\n";

        // construct the filenames
        $filename_only = 'CHANGES';
        $filename = $this->directoryName . '/docs/' . $filename_only;
        $newfilename = $filename . '.new';

        $version = 'v' . substr($this->newSourceVersionStringPlain, 0, strpos($this->newSourceVersionString, '-'));

        $oldfp = fopen($filename, 'r');
        $newfp = fopen($newfilename, 'w');
        fwrite($newfp, str_repeat('-', strlen($version)) . "\n$version\n" .
               str_repeat('-', strlen($version)) . "\n\n\n\n\n");
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

    /**
     * get and save the revision number of the CHANGES file
     */
    function saveChangelog($old = false, $directory = null)
    {
        if (empty($directory)) {
            if ($old) {
                $directory = './' . $this->oldDirectoryName . '/docs';
            } else {
                $directory = './' . $this->directoryName . '/docs';
            }
        }
        if (!$old) {
            include "$directory/RELEASE_NOTES";
            if (strlen(htmlspecialchars($this->notes['fm']['changes'])) > 600) {
                print "WARNING: freshmeat release notes are longer than 600 characters!\n";
            }
        }
        exec("cd $directory; cvs status CHANGES", $output);
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

    /**
     * work through the source directory given, cleaning things up by removing
     * directories and files we don't want in the tarball
     */
    function cleanDirectories($directory)
    {
        print "Cleaning source tree\n";
        $directories = explode("\n", `find $directory -type d \\( -name CVS -o -name packaging -o -name framework \\) -print | sort -r`);
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

    /**
     * Check out the tag we've been given to work with and move it to the
     * directory name given
     */
    function checkOutTag($mod_version, $directory, $module = null)
    {
        if (empty($module)) {
            $module = $this->options['module'];
        }

        if (@is_dir($module)) {
            system("rm -rf $module");
        }

        // Use CVS to check the source out
        if ($mod_version == 'HEAD') {
            print "Checking out HEAD for $module\n";
            $cmd = "cvs -q co -P $module > /dev/null";
            system($cmd, $status);
        } else {
            print "Checking out tag $mod_version for $module\n";
            $cmd = "cvs -q co -P -r$mod_version $module > /dev/null";
            system($cmd, $status);
        }
        if ($status) {
            die("\nThere was an error running the command\n$cmd\n");
        }

        // Move the source into the directory specified
        print "Moving $module to $directory\n";
        if (@is_dir($directory)) {
            system("rm -rf $directory");
        }
        system("mv -f $module $directory");
    }

    /**
     * Checkout and install framework
     */
    function checkOutFramework($mod_version, $directory)
    {
        if ($this->options['module'] == 'horde' &&
            ($this->options['branch'] == 'HEAD' ||
             strstr($this->options['branch'], 'FRAMEWORK'))) {
            if ($this->options['branch'] == 'HEAD') {
                print "Checking out HEAD for framework\n";
            } else {
                print "Checking out tag $mod_version for framework\n";
            }
            $cmd = "cd $directory; cvs co -P -r$mod_version framework > /dev/null 2>&1; cd ..";
            system($cmd, $status);
            if ($status) {
                die("\nThere was an error running the command\n$cmd\n");
            }
            print "Installing framework packages\n";
            if (file_exists("./$directory/scripts/create-symlinks.php")) {
                system("php ./$directory/scripts/create-symlinks.php --copy --src=./$directory/framework --dest=./$directory/lib");
            } else {
                system("horde-fw-symlinks.php --copy --src ./$directory/framework --dest ./$directory/lib");
            }

            print "Setting include path\n";
            $filename = $directory . '/lib/core.php';
            $newfilename = $filename . '.new';
            $oldfp = fopen($filename, 'r');
            $newfp = fopen($newfilename, 'w');
            while ($line = fgets($oldfp)) {
                fwrite($newfp, str_replace('// ini_set(\'include_path\'', 'ini_set(\'include_path\'', $line));
            }
            fclose($oldfp);
            fclose($newfp);
            system("mv -f $newfilename $filename");
        }
    }

    /**
     * Upload tarball to the FTP server
     */
    function upload()
    {
        $module = $this->options['module'];
        $user = $this->options['horde']['user'];
        $identity = empty($this->options['ssh']['identity']) ? '' : ' -i ' . $this->options['ssh']['identity'];
        $chmod = "chmod 664 /horde/ftp/pub/$module/$this->tarballName;";
        if ($this->makeDiff) {
            $chmod .= " chmod 664 /horde/ftp/pub/$module/patches/$this->patchName.gz;";
        }
        if ($this->latest &&
            strpos($this->options['branch'], 'RELENG') !== 0) {
            $chmod .= " ln -sf $this->tarballName /horde/ftp/pub/$module/$module-latest.tar.gz;";
        }

        if (!$this->options['noftp']) {
            print "Uploading $this->tarballName to $user@ftp.horde.org:/horde/ftp/pub/$module/\n";
            system("scp -P 35$identity $this->tarballName $user@ftp.horde.org:/horde/ftp/pub/$module/");
            if ($this->makeDiff) {
                print "Uploading $this->patchName.gz to $user@ftp.horde.org:/horde/ftp/pub/$module/patches/\n";
                system("scp -P 35$identity $this->patchName.gz $user@ftp.horde.org:/horde/ftp/pub/$module/patches/");
            }
            print "Executing $chmod\n";
            system("ssh -p 35 -l $user$identity ftp.horde.org '$chmod'");
        } else {
            print "NOT uploading $this->tarballName to ftp.horde.org:/horde/ftp/pub/$module/\n";
            if ($this->makeDiff) {
                print "NOT uploading $this->patchName.gz to $user@ftp.horde.org:/horde/ftp/pub/$module/patches/\n";
            }
            print "NOT executing $chmod\n";
        }
    }

    /**
     * check if freshmeat announcement was successful.
     */
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

    /**
     * announce release to mailing lists and freshmeat.
     */
    function announce($doc_dir = null)
    {
        $module = $this->options['module'];
        if (!isset($this->notes)) {
            print "NOT announcing release, RELEASE_NOTES missing.\n";
            return;
        }
        if (!empty($this->options['noannounce']) ||
            !empty($this->options['nofreshmeat'])) {
            print "NOT announcing release on freshmeat.net\n";
        } else {
            print "Announcing release on freshmeat.net\n";
        }

        if (empty($this->options['nofreshmeat'])) {
            $fm = Horde_RPC::request(
                'xmlrpc',
                'http://freshmeat.net/xmlrpc/',
                'login',
                array('username' => $this->options['fm']['user'],
                      'password' => $this->options['fm']['password']));
        } else {
            $fm = array('SID' => null);
        }
        if (empty($doc_dir)) {
            $doc_dir = $module . '/docs';
        }

        $url_changelog = $this->oldVersion
            ? "http://cvs.horde.org/diff.php/$doc_dir/CHANGES?r1={$this->oldChangelogVersion}&r2={$this->changelogVersion}&ty=h"
            : '';

        if (is_a($fm, 'PEAR_Error')) {
            print $fm->getMessage() . "\n";
        } else {
            $announcement = array('SID' => $fm['SID'],
                                  'project_name' => $this->notes['fm']['project'],
                                  'branch_name' => $this->notes['fm']['branch'],
                                  'version' => $this->sourceVersionString,
                                  'changes' => htmlspecialchars($this->notes['fm']['changes']),
                                  'release_focus' => (int)$this->notes['fm']['focus'],
                                  'url_changelog' => $url_changelog,
                                  'url_tgz' => "ftp://ftp.horde.org/pub/$module/{$this->tarballName}");
            if ($this->_fmVerify($fm)) {
                if (!empty($this->options['noannounce']) ||
                    !empty($this->options['nofreshmeat'])) {
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
        }

        $ml = (!empty($this->notes['list'])) ? $this->notes['list'] : $module;
        if (substr($ml, 0, 6) == 'horde-') {
            $ml = 'horde';
        }

        $to = "announce@lists.horde.org, vendor@lists.horde.org, $ml@lists.horde.org";
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
        if ($this->notes['fm']['focus'] == 9) {
            $subject = '[SECURITY] ' . $subject;
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
                $url_changelog;
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

            if (!empty($this->binaryDiffs)) {
                $body .= "\n\n" .
                    'NOTE: Patches do not contain differences between files containing binary data.' . "\n" .
                    'These files will need to be updated via the distribution files:' . "\n\n    " .
                    implode("\n    ", $this->binaryDiffs);
            }
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
        require_once 'Horde/MIME/Mail.php';
        $mail = new MIME_Mail();
        $mail->setBody($body, 'iso-8859-1', false);
        $mail->addHeaders($headers);
        $result = $mail->send($this->options['mailer']['type'], $this->options['mailer']['params']);
        if (is_a($result, 'PEAR_Error')) {
            print $result->getMessage() . "\n";
        }
    }

    /**
     * Do testing (development only)
     */
    function test()
    {
        if (!$this->options['test']) {
            return;
        }

        print "options['version']={$this->options['version']}\n";
        print "options['oldversion']={$this->options['oldversion']}\n";
        print "options['module']={$this->options['module']}\n";
        print "options['branch']={$this->options['branch']}\n";

        $this->setVersionStrings();

        print "hordeVersionString={$this->hordeVersionString}\n";
        print "oldHordeVersionString={$this->oldHordeVersionString}\n";
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
        print "newSourceVersionStringPlain={$this->newSourceVersionStringPlain}\n";
        print "ticketVersion={$this->ticketVersion}\n";
        print "ticketVersionDesc=MODULE{$this->ticketVersionDesc}\n";
        if ($this->latest) {
            print "This is a production release\n";
        }
        exit(0);
    }

    /**
     * Add the new version to bugs.horde.org
     */
    function addWhupsVersion()
    {
        if (!isset($this->notes)) {
            print "\nNOT updating bugs.horde.org, RELEASE_NOTES missing.\n";
            return;
        }
        $this->ticketVersionDesc = $this->notes['name'] . $this->ticketVersionDesc;

        $params = array('url' => 'https://dev.horde.org/horde/rpc.php',
                        'user' => $this->options['horde']['user'],
                        'pass' => $this->options['horde']['pass']);
        $whups = new Horde_Release_Whups($params);

        if (!$this->options['nowhups']) {
            print "Adding new versions to bugs.horde.org: ";
            /* Set the new version in the queue */
            $res = $whups->addNewVersion($this->options['module'], $this->ticketVersion,
                                         $this->ticketVersionDesc);
            if (is_a($res, 'PEAR_Error')) {
                print "Failed:\n";
                print $res->getMessage() . "\n";
            } else {
                print "OK\n";
            }
        } else {
            print "NOT updating bugs.horde.org:\n";
            print "New ticket version WOULD have been {$this->ticketVersion}\n";
            print "New ticket version description WOULD have been {$this->ticketVersionDesc}\n";

            /* Perform some sanity checks on bugs.horde.org */
            $queue = $whups->getQueueId($this->options['module']);
            if (is_a($queue, 'PEAR_Error')) {
                print "Will be UNABLE to update bugs.horde.org:\n";
                print $queue->getMessage() . "\n";
            } elseif ($queue === false) {
                print"Was UNABLE to locate the queue id for {$this->options['module']}\n";
            } else {
                print "The queue id on bugs.horde.org is $queue \n";
            }
        }
    }

    /**
     * Set the version strings to use given the arguments
     */
    function setVersionStrings()
    {
        $ver = explode('.', $this->options['version']);
        if (preg_match('/(\d+)\-(.*)/', $ver[count($ver) - 1], $matches)) {
            $ver[count($ver) - 1] = $matches[1];
            $plus = $matches[2];
        }
        if (preg_match('/(H\d)-(\d+)/', $ver[0], $matches)) {
            $ver[0] = $matches[2];
            $this->hordeVersionString = $matches[1];
        }
        if (count($ver) > 2 && $ver[count($ver) - 1] == '0') {
            die("version {$this->options['version']} should not have the trailing 3rd-level .0\n");
        }

        // check if --oldversion is empty or 0
        if (!empty($this->options['oldversion'])) {
            $this->oldVersion = true;
        }
        $oldver = explode('.', $this->options['oldversion']);
        if (preg_match('/(\d+)\-(.*)/', $oldver[count($oldver) - 1], $matches)) {
            $oldver[count($oldver) - 1] = $matches[1];
            $oldplus = $matches[2];
        }
        if (preg_match('/(H\d)-(\d+)/', $oldver[0], $matches)) {
            $oldver[0] = $matches[2];
            $this->oldHordeVersionString = $matches[1];
        }

        // set the string to use as the tag name in CVS
        $this->tagVersionString = strtoupper($this->options['module'] . '_' . preg_replace('/\W/', '_', implode('_', $ver)));
        if (isset($plus)) {
            $this->tagVersionString .= '_' . $plus;
        }

        // create patches only if not a major version change
        if ($this->options['oldversion'] && $ver[0] == $oldver[0]) {
            $this->makeDiff = true;
        }

        // is this really a production release?
        if (isset($plus) && !preg_match('/^pl\d/', $plus)) {
            $this->latest = false;
        }

        // set the string to insert into the source version file
        $this->sourceVersionString = implode('.', $ver);
        if (isset($plus)) {
            $this->sourceVersionString .= '-' . $plus;
        }

        // set the string to be used for the directory to package from
        $this->directoryName = $this->options['module'] . '-';
        if (!empty($this->hordeVersionString)) {
            $this->directoryName .= $this->hordeVersionString . '-';
        }
        $this->directoryName = strtolower($this->directoryName . $this->sourceVersionString);

        if (!empty($this->hordeVersionString)) {
            $this->sourceVersionString = $this->hordeVersionString . ' (' . $this->sourceVersionString . ')';
        }

        if ($this->oldVersion) {
            $this->oldSourceVersionString = implode('.', $oldver);
            if (isset($oldplus)) {
                $this->oldSourceVersionString .= '-' . $oldplus;
            }
            $this->oldTagVersionString = strtoupper($this->options['module'] . '_' . implode('_', $oldver));
            if (isset($oldplus)) {
                $this->oldTagVersionString .= '_' . $oldplus;
            }
            $this->oldDirectoryName = strtolower($this->options['module'] . '-' . $this->oldHordeVersionString . $this->oldSourceVersionString);
            $this->oldDirectoryName = $this->options['module'] . '-';
            if (!empty($this->oldHordeVersionString)) {
                $this->oldDirectoryName .= $this->oldHordeVersionString . '-';
            }
            $this->oldDirectoryName = strtolower($this->oldDirectoryName . $this->oldSourceVersionString);

            if (!empty($this->oldHordeVersionString)) {
                $this->oldSourceVersionString = $this->oldHordeVersionString . ' (' . $this->oldSourceVersionString . ')';
            }
        }

        // Set string to use for updating ticketing system.
        $this->ticketVersion = implode('.', $ver);
        if (!empty($plus)) {
            $this->ticketVersion .= '-' . $plus;
        }

        if (!empty($this->hordeVersionString)) {
            $this->ticketVersionDesc .= ' ' . $this->hordeVersionString;
        }

        // Account for the 'special' case of the horde module.
        if ($this->options['module'] == 'horde') {
            $this->ticketVersionDesc .= ' ' . implode('.', $ver);
        } else {
            $this->ticketVersionDesc .= ' ' . '(' . implode('.', $ver) . ')';
        }

        // See if we have a 'Final', 'Alpha', or 'RC' to add.
        if ($this->latest) {
            $this->ticketVersionDesc .= ' Final';
        } elseif (!empty($plus) &&
                  preg_match('/^RC(\d+)/', $plus, $matches)) {
            $this->ticketVersionDesc .= ' Release Candidate ' . $matches[1];

        } elseif (!empty($plus) && strtolower($plus) == 'alpha') {
            $this->ticketVersionDesc .= ' Alpha';
        }

        // set the name of the string to put into the source version file when
        // done
        if (!isset($plus)) {
            while (count($ver) < 3) {
                $ver[] = '0';
            }
            $ver[count($ver) - 1] += 1;
        }
        $this->newSourceVersionString = implode('.', $ver) . '-cvs';
        $this->newSourceVersionStringPlain = $this->newSourceVersionString;

        if (!empty($this->hordeVersionString)) {
            $this->newSourceVersionString = $this->hordeVersionString .
                ' (' . $this->newSourceVersionString . ')';
        }

    }

    /**
     * Get all of the command-line arguments from the user
     */
    function getArguments()
    {
        global $argv;

        // Parse the command-line arguments
        array_shift($argv);
        foreach ($argv as $arg) {
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

            // Check to see if they tell us not to announce
            } elseif (strstr($arg, '--nofreshmeat')) {
                $this->options['nofreshmeat']= true;

            // Check to see if they tell us not to add new ticket versions
            } elseif (strstr($arg, '--noticketversion')) {
                $this->options['nowhups'] = true;

            // Check to see if they tell us to do a dry run
            } elseif (strstr($arg, '--dryrun')) {
                $this->options['nocommit'] = true;
                $this->options['noftp'] = true;
                $this->options['noannounce'] = true;
                $this->options['nowhups'] = true;
                $this->options['nofreshmeat']= true;

            // Check to see if they tell us to test (for development only)
            } elseif (strstr($arg, '--test')) {
                $this->options['test']= true;
                // safety first
                $this->options['nocommit'] = true;
                $this->options['noftp'] = true;
                $this->options['noannounce'] = true;
                $this->options['nowhups'] = true;
                $this->options['nofreshmeat']= true;

            // Check for help usage.
            } elseif (strstr($arg, '--help')) {
                $this->print_usage();
                exit;

            // We have no idea what this is
            } else {
                $this->print_usage('You have used unknown arguments: ' . $arg);
                exit;
            }
        }
    }

    /**
     * Check the command-line arguments and set some internal defaults
     */
    function checkArguments()
    {
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

    /**
     * Check the command-line arguments and set some internal defaults
     */
    function checkSetSystem()
    {
        // Set umask
        umask(022);
    }

    /**
     * Show people how to use the damned thing
     */
    function print_usage($message = null)
    {
        if (!is_null($message)) {
            print "\n***  ERROR: $message  ***\n";
        }

        print <<<USAGE

make-release.php: Horde release generator.

   This script takes as arguments the module to make a release of, the
   version of the release, and the branch:

      horde-make-release.php --module=<name>
                         --version=[Hn-]xx.yy[.zz[-<string>]]
                         --oldversion=[Hn-]xx[.yy[.zz[-<string>]]]
                         [--branch=<branchname>] [--nocommit] [--noftp]
                         [--noannounce] [--nofreshmeat] [--noticketversion]
                         [--test] [--dryrun] [--help]

   If you omit the branch, it will implicitly work with the HEAD branch.
   If you release a new major version use the --oldversion=0 option.
   Use the --nocommit option to do a test build (without touching the CVS
   repository).
   Use the --noftp option to not upload any files on the FTP server.
   Use the --noannounce option to not send any release announcements.
   Use the --nofreshmeat option to not send any freshmeat announcements.
   Use the --noticketversion option to not update the version information on
   bugs.horde.org.
   The --dryrun option is an alias for:
     --nocommit --noftp --noannounce --nofreshmeat --noticketversion.
   The --test option is for debugging purposes only.

   EXAMPLES:

   To make a new development release of Horde:
      horde-make-release.php --module=horde --version=2.1-dev --oldversion=2.0

   To make a new stable release of Turba:
      horde-make-release.php --module=turba --version=H3-2.0.2 \
        --oldversion=H3-2.0.1 --branch=FRAMEWORK_3

   To make a new stable release of IMP 3:
      horde-make-release.php --module=imp --version=3.0 --oldversion=2.3.7 \
        --branch=RELENG_3

   To make a brand new Alpha/Beta/RC release of Luxor:
      horde-make-release.php --module=luxor --version=H3-1.0-ALPHA \
        --oldversion=0

USAGE;
    }

}


/**
 * Class for interfacing with the tickets api
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * @author Michael J. Rubinsky <mrubinsk@horde.org>
 */
class Horde_Release_Whups {

    /**
     * Instance of XML_RPC_Client object
     *
     * @var XML_RPC_CLient
     */
    var $_client;

    /**
     * Local copy of config params.
     * @var array
     */
    var $_params;

    function Horde_Release_Whups($params)
    {
        $this->_params = $params;
    }

    /**
     * Add a new version to the current modules queue.
     *
     * @param string $module   The name of the module.
     * @param string $version  The version string.
     * @param string $desc     Descriptive text for this version.
     *
     * @param mixed  true || PEAR_Error
     */
    function addNewVersion($module, $version, $desc = '')
    {
        require_once 'Horde/RPC.php';

        if ($module == 'horde') {
            $module = 'horde base';
        }
        $id = $this->getQueueId($module);
        if (is_a($id, 'PEAR_Error')) {
           return $id;
        }

        if ($id === false) {
            return PEAR::raiseError('Unable to locate requested queue');
        }

        $method = 'tickets.addVersion';
        $params = array($id, $version, $desc);
        $options = array('user' => $this->_params['user'],
                         'pass' => $this->_params['pass']);


        return Horde_RPC::request('jsonrpc', $this->_params['url'], $method,
                                  $params, $options);
    }

    /**
     * Look up the queue id for the requested module name.
     */
    function getQueueId($module)
    {
        $queues = $this->_listQueues();
        if (is_a($queues, 'PEAR_Error')) {
            return $queues;
        }
        foreach ($queues as $id => $queue) {
            if (strtolower($queue) == $module) {
                return $id;
            }
        }
        return false;
    }

    /**
     * Perform a listQueue api call.
     */
    function _listQueues() {
        $method = 'tickets.listQueues';
        $result = Horde_RPC::request('jsonrpc', $this->_params['url'], $method,
                                     null, array('user' => $this->_params['user'],
                                                 'pass' => $this->_params['pass']));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $result->result;
    }

}
