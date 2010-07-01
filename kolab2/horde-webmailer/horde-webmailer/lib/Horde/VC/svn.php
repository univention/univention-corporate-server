<?php
/**
 * VC_svn implementation.
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * $Horde: framework/VC/VC/svn.php,v 1.28.4.23 2009-01-06 15:23:46 jan Exp $
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @since   Horde 3.0
 * @package VC
 */
class VC_svn extends VC {

    var $_username = '';
    var $_password = '';

    /**
     * Constructor.
     *
     * @param array $params  Any parameter the class expects.
     *                       Current parameters:
     *                       'sourceroot': The source root for this
     *                                     repository
     *                       'paths': Hash with the locations of all
     *                                necessary binaries: 'svn', 'diff'
     */
    function VC_svn($params)
    {
        $this->_sourceroot = $params['sourceroot'];
        $this->_paths = $params['paths'];

        if (!empty($params['username'])) {
            $this->_username = $params['username'];
        }

        if (!empty($params['password'])) {
            $this->_password = $params['password'];
        }
    }

    function isFile($where)
    {
        return true;
    }

    function getCommand()
    {
        $svnPath = $this->getPath('svn');
        if (isset($this->_paths['svn_home'])) {
            $tempDir = $this->_paths['svn_home'];
        } else {
            $tempDir = Util::getTempDir();
        }
        $command = $svnPath . ' --non-interactive --config-dir ' . $tempDir;

        if ($this->_username) {
            $command .= ' --username ' . $this->_username;
        }

        if ($this->_password) {
            $command .= ' --password ' . $this->_password;
        }

        return $command;
    }

    function &queryDir($where)
    {
        $dir = new VC_Directory_svn($this, $where);
        return $dir;
    }

    function getCheckout($file, $rev)
    {
        return VC_Checkout_svn::get($this, $file->queryFullPath(), $rev);
    }

    function getDiff($file, $rev1, $rev2, $type = 'context', $num = 3, $ws = true)
    {
        return VC_Diff_svn::get($this, $file, $rev1, $rev2, $type, $num, $ws);
    }

    function &getFileObject($filename, $cache = null, $quicklog = false)
    {
        $fo = &VC_File_svn::getFileObject($this, $filename, $cache, $quicklog);
        return $fo;
    }

    function &getAnnotateObject($filename)
    {
        $blame = new VC_Annotate_svn($this, $filename);
        return $blame;
    }

    function &getPatchsetObject($filename, $cache = null)
    {
        $po = &VC_Patchset_svn::getPatchsetObject($this, $filename, $cache);
        return $po;
    }

}

/**
 * VC_svn annotate class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Annotate_svn {

    var $file;
    var $SVN;
    var $tmpfile;

    function VC_Annotate_svn($rep, $file)
    {
        $this->SVN = $rep;
        $this->file = $file;
    }

    function doAnnotate($rev)
    {
        /* Make sure that the file values for this object is valid. */
        if (is_a($this->file, 'PEAR_Error')) {
            return false;
        }

        if (!VC_Revision::valid($rev)) {
            return false;
        }

        $Q = VC_WINDOWS ? '"' : "'";
        $command = $this->SVN->getCommand() . ' annotate -r 1:' . $rev . ' ' . $Q . str_replace($Q, '\\' . $Q, $this->file->queryFullPath()) . $Q . ' 2>&1';
        $pipe = popen($command, 'r');
        if (!$pipe) {
            return PEAR::raiseError('Failed to execute svn annotate: ' . $command);
        }

        $lines = array();
        $lineno = 1;
        while (!feof($pipe)) {
            $line = fgets($pipe, 4096);
            if (preg_match('/^\s+(\d+)\s+([\w\.]+)\s(.*)$/', $line, $regs)) {
                $entry = array();
                $entry['rev']    = $regs[1];
                $entry['author'] = trim($regs[2]);
                $entry['date']   = '';
                $entry['line']   = $regs[3];
                $entry['lineno'] = $lineno++;
                $lines[] = $entry;
            }
        }

        pclose($pipe);
        return $lines;
    }

}

/**
 * VC_svn checkout class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Checkout_svn {

    /**
     * Static function which returns a file pointing to the head of the requested
     * revision of an RCS file.
     * @param fullname Fully qualified pathname of the desired RCS file to checkout
     * @param rev RCS revision number to check out
     * @return Either a PEAR_Error object, or a stream pointer to the head of the checkout
     */
    function get($rep, $fullname, $rev)
    {
        if (!VC_Revision::valid($rev)) {
            return PEAR::raiseError('Invalid revision number');
        }

        if (VC_WINDOWS) {
            $Q = '"';
            $mode = 'rb';
        } else {
            $Q = "'";
            $mode = 'r';
        }

        if (!($RCS = popen($rep->getCommand() . ' cat -r ' . $rev . ' ' . $Q . str_replace($Q, '\\' . $Q, $fullname) . $Q . ' 2>&1', $mode))) {
            return PEAR::raiseError('Couldn\'t perform checkout of the requested file');
        }

        return $RCS;
    }

}

/**
 * VC_svn diff class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Diff_svn {

    /**
     * Obtain the differences between two revisions of a file.
     *
     * @param VC_svn $rep        A repository object.
     * @param VC_File_svn $file  The desired file.
     * @param string $rev1       Original revision number to compare from.
     * @param string $rev2       New revision number to compare against.
     * @param string $type       The type of diff (e.g. 'unified').
     * @param integer $num       Number of lines to be used in context and
     *                           unified diffs.
     * @param boolean $ws        Show whitespace in the diff?
     *
     * @return string|boolean  False on failure, or a string containing the
     *                         diff on success.
     */
    function get($rep, $file, $rev1, $rev2, $type = 'context', $num = 3,
                 $ws = true)
    {
        /* Make sure that the file parameter is valid */
        if (is_a($file, 'PEAR_Error')) {
            return false;
        }

        /* Check that the revision numbers are valid */
        $rev1 = VC_Revision::valid($rev1) ? $rev1 : 0;
        $rev2 = VC_Revision::valid($rev1) ? $rev2 : 0;

        $fullName = $file->queryFullPath();
        $diff = array();
        $options = '';
        if (!$ws) {
            $options .= ' -bB ';
        }

        switch ($type) {
        case 'context':
            $options .= '--context=' . (int)$num;
            break;

        case 'unified':
            $options .= '-p --unified=' . (int)$num;
            break;

        case 'column':
            $options .= '--side-by-side --width=120';
            break;

        case 'ed':
            $options .= '-e';
            break;
        }

        // TODO: add options for $hr options - however these may not
        // be compatible with some diffs.
        $Q = VC_WINDOWS ? '"' : "'";
        $command = $rep->getCommand() . " diff --diff-cmd " . $rep->getPath('diff') . " -r $rev1:$rev2 -x " . $Q . $options . $Q . ' ' . $Q . $file->queryFullPath() . $Q . ' 2>&1';

        exec($command, $diff, $retval);
        return $diff;
    }

}

/**
 * VC_svn directory class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Directory_svn {

    var $rep;
    var $dirName;
    var $files;
    var $atticFiles;
    var $mergedFiles;
    var $dirs;
    var $parent;
    var $moduleName;

    /**
     * Create a SVN Directory object to store information about the
     * files in a single directory in the repository
     *
     * @param VC_Repository_svn $rp  The VC_Repository object this directory
     *                               is part of.
     * @param string $dn             Path to the directory.
     * @param VC_Directory_svn $pn   The parent VC_Directory to this one.
     */
    function VC_Directory_svn($rep, $dn, $pn = '')
    {
        $this->rep = $rep;
        $this->parent = $pn;
        $this->moduleName = $dn;
        $this->dirName = "/$dn";
        $this->files = array();
        $this->dirs = array();
    }

    /**
     * Return fully qualified pathname to this directory with no
     * trailing /.
     *
     * @return Pathname of this directory
     */
    function queryDir()
    {
        return $this->dirName;
    }

    function &queryDirList()
    {
        return $this->dirs;
    }

    function &queryFileList($showattic = false)
    {
        if ($showattic && isset($this->mergedFiles)) {
            return $this->mergedFiles;
        } else {
            return $this->files;
        }
    }

    /**
     * Tell the object to open and browse its current directory, and
     * retrieve a list of all the objects in there.  It then populates
     * the file/directory stack and makes it available for retrieval.
     *
     * @return PEAR_Error object on an error, 1 on success.
     */
    function browseDir($cache = null, $quicklog = true, $showattic = false)
    {
        $Q = VC_WINDOWS ? '"' : "'" ;
        $cmd = $this->rep->getCommand() . ' ls ' . $Q . str_replace($Q, '\\' . $Q, $this->rep->sourceroot() . $this->queryDir()) . $Q . ' 2>&1';

        $dir = popen($cmd, 'r');
        if (!$dir) {
            return PEAR::raiseError('Failed to execute svn ls: ' . $cmd);
        }

        /* Create two arrays - one of all the files, and the other of
         * all the dirs. */
        $errors = array();
        while (!feof($dir)) {
            $line = chop(fgets($dir, 1024));
            if (!strlen($line)) {
                continue;
            }

            if (substr($line, 0, 4) == 'svn:') {
                $errors[] = $line;
            } elseif (substr($line, -1) == '/') {
                $this->dirs[] = substr($line, 0, -1);
            } else {
                $fl = $this->rep->getFileObject($this->queryDir() . "/$line", $cache, $quicklog);
                if (is_a($fl, 'PEAR_Error')) {
                    return $fl;
                } else {
                    $this->files[] = $fl;
                }
            }
        }

        pclose($dir);

        if ($errors) {
            return PEAR::raiseError(implode("\n", $errors));
        }

        return true;
    }

    /**
     * Sort the contents of the directory in a given fashion and
     * order.
     *
     * @param $how Of the form VC_SORT_* where * can be:
     *             NONE, NAME, AGE, REV for sorting by name, age or revision.
     * @param $dir Of the form VC_SORT_* where * can be:
     *             ASCENDING, DESCENDING for the order of the sort.
     */
    function applySort($how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
        /* TODO: this code looks very inefficient! optimise... -
         * avsm. */

        // Assume by name for the moment.
        natcasesort($this->dirs);
        $this->doFileSort($this->files, $how, $dir);
        if (isset($this->atticFiles)) {
            $this->doFileSort($this->atticFiles, $how, $dir);
        }
        if (isset($this->mergedFiles)) {
            $this->doFileSort($this->mergedFiles, $how, $dir);
        }
        if ($dir == VC_SORT_DESCENDING) {
            $this->dirs = array_reverse($this->dirs);
            $this->files = array_reverse($this->files);
            if (isset($this->mergedFiles)) {
                $this->mergedFiles = array_reverse($this->mergedFiles);
            }
        }
    }

    function doFileSort(&$fileList, $how = VC_SORT_NONE, $dir = VC_SORT_ASCENDING)
    {
        switch ($how) {
        case VC_SORT_AGE:
            usort($fileList, array($this, 'fileAgeSort'));
            break;

        case VC_SORT_NAME:
            usort($fileList, array($this, 'fileNameSort'));
            break;

        case VC_SORT_AUTHOR:
            usort($fileList, array($this, 'fileAuthorSort'));
            break;

        case VC_SORT_REV:
            usort($fileList, array($this, 'fileRevSort'));
            break;

        case VC_SORT_NONE:
        default:
            break;
        }
    }

    /**
     * Sort function for ascending age.
     */
    function fileAgeSort($a, $b)
    {
        $aa = $a->queryLastLog();
        $bb = $b->queryLastLog();
        if ($aa->queryDate() == $bb->queryDate()) {
            return 0;
        } else {
            return ($aa->queryDate() < $bb->queryDate()) ? 1 : -1;
        }
    }

    /**
     * Sort function by author name.
     */
    function fileAuthorSort($a, $b)
    {
        $aa = $a->queryLastLog();
        $bb = $b->queryLastLog();
        if ($aa->queryAuthor() == $bb->queryAuthor()) {
            return 0;
        } else {
            return ($aa->queryAuthor() > $bb->queryAuthor()) ? 1 : -1;
        }
    }

    /**
     * Sort function for ascending filename.
     */
    function fileNameSort($a, $b)
    {
        return strcasecmp($a->name, $b->name);
    }

    /**
     * Sort function for ascending revision.
     */
    function fileRevSort($a, $b)
    {
        return VC_Revision::cmp($a->queryHead(), $b->queryHead());
    }

}

/**
 * VC_svn file class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_File_svn extends VC_File {

    /**
     * Create a repository file object, and give it information about
     * what its parent directory and repository objects are.
     *
     * @param string $fl  Full path to this file.
     */
    function VC_File_svn($rep, $fl, $quicklog = false)
    {
        $this->rep = $rep;
        $this->name = basename($fl);
        $this->dir = dirname($fl);
        $this->logs = array();
        $this->quicklog = $quicklog;
        $this->revs = array();
        $this->revsym = array();
        $this->symrev = array();
        $this->branches = array();
    }

    function &getFileObject($rep, $filename, $cache = null, $quicklog = false)
    {
        /* The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data. */
        $cacheVersion = 2;
        $cacheId = $rep->sourceroot() . '_n' . $filename . '_f' . (int)$quicklog . '_v' . $cacheVersion;

        if ($cache &&
            // The file is cached for one hour no matter what, because
            // there is no way to determine with Subversion the time
            // the file last changed.
            $cache->exists($cacheId, 3600)) {
            $fileOb = unserialize($cache->get($cacheId, 3600));
            $fileOb->setRepository($rep);
        } else {
            $fileOb = new VC_File_svn($rep, $filename, $quicklog);
            $fileOb->setRepository($rep);
            if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
                return $result;
            }
            $fileOb->applySort(VC_SORT_AGE);

            if ($cache) {
                $cache->set($cacheId, serialize($fileOb));
            }
        }

        return $fileOb;
    }

    /**
     * If this file is present in an Attic directory, this indicates
     * it.
     *
     * @return true if file is in the Attic, and false otherwise
     */
    function isAtticFile()
    {
        // Not implemented yet
        return false;
    }

    /**
     * Returns the name of the current file as in the repository
     *
     * @return Filename (without the path)
     */
    function queryRepositoryName()
    {
        return $this->name;
    }

    /**
     * Returns name of the current file without the repository
     * extensions (usually ,v)
     *
     * @return Filename without repository extension
     */
    function queryName()
    {
       return preg_replace('/,v$/', '', $this->name);
    }

    /**
     * Return the last revision of the current file on the HEAD branch
     *
     * @return Last revision of the current file
     */
    function queryRevision()
    {
        if (!isset($this->revs[0])) {
            return PEAR::raiseError('No revisions');
        }
        return $this->revs[0];
    }

    function queryPreviousRevision($rev)
    {
        $last = false;
        foreach ($this->revs as $entry) {
            if ($last)
                return $entry;
            if ($entry == $rev)
                $last = true;
        }

        return false;
    }

    /**
     * Return the HEAD (most recent) revision number for this file.
     *
     * @return HEAD revision number
     */
    function queryHead()
    {
        return $this->queryRevision();
    }

    /**
     * Return the last VC_Log object in the file.
     *
     * @return VC_Log of the last entry in the file
     */
    function queryLastLog()
    {
        if (!isset($this->revs[0]) || !isset($this->logs[$this->revs[0]])) {
            return PEAR::raiseError('No revisions');
        }
        return $this->logs[$this->revs[0]];
    }

    /**
     * Sort the list of VC_Log objects that this file contains.
     *
     * @param how VC_SORT_REV (sort by revision),
     *            VC_SORT_NAME (sort by author name),
     *            VC_SORT_AGE (sort by commit date)
     */
    function applySort($how = VC_SORT_REV)
    {
        switch ($how) {
        case VC_SORT_REV:
            $func = 'Revision';
            break;
        case VC_SORT_NAME:
            $func = 'Name';
            break;
        case VC_SORT_AGE:
            $func = 'Age';
            break;
        default:
            $func = 'Revision';
        }
        uasort($this->logs, array($this, "sortBy$func"));
        return true;
    }

    /**
     * The sortBy*() functions are internally used by applySort.
     */
    function sortByRevision($a, $b)
    {
        return VC_Revision::cmp($b->rev, $a->rev);
    }

    function sortByAge($a, $b)
    {
        return $b->date - $a->date;
    }

    function sortByName($a, $b)
    {
        return strcmp($a->author, $b->author);
    }

    /**
     * Populate the object with information about the revisions logs
     * and dates of the file.
     *
     * @return mixed boolean            True on success,
     *               PEAR_Error         On error.
     */
    function getBrowseInfo()
    {
        /* This doesn't work; need to find another way to simply
         * request the most recent revision:
         *
         * $flag = $this->quicklog ? '-r HEAD ' : ''; */
        $flag = '';
        $Q = VC_WINDOWS ? '"' : "'";
        $cmd = $this->rep->getCommand() . ' log -v ' . $flag . $Q . str_replace($Q, '\\' . $Q, $this->queryFullPath()) . $Q . ' 2>&1';
        $pipe = popen($cmd, 'r');
        if (!$pipe) {
            return PEAR::raiseError('Failed to execute svn log: ' . $cmd);
        }

        $header = fgets($pipe);
        if (!strspn($header, '-')) {
            return PEAR::raiseError('Error executing svn log: ' . $header);
        }

        while (!feof($pipe)) {
            $log = new VC_Log_svn($this->rep, $this);
            $err = $log->processLog($pipe);
            if ($err) {
                $rev = $log->queryRevision();
                $this->logs[$rev] = $log;
                $this->revs[] = $rev;
            }

            if ($this->quicklog) {
                break;
            }
        }

        pclose($pipe);
        return true;
    }

    /**
     * Return the fully qualified filename of this object.
     *
     * @return Fully qualified filename of this object
     */
    function queryFullPath()
    {
        return $this->rep->sourceroot() . '/' . $this->queryModulePath();
    }

    /**
     * Return the name of this file relative to its sourceroot.
     *
     * @return string  Pathname relative to the sourceroot.
     */
    function queryModulePath()
    {
        return $this->dir . '/' . $this->name;
    }

}

/**
 * VC_svn log class.
 *
 * Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Log_svn {

    var $rep;
    var $err;
    var $file;
    var $files;
    var $tags;
    var $rev;
    var $date;
    var $log;
    var $author;
    var $state;
    var $lines;
    var $branches;

    /**
     * Constructor.
     */
    function VC_Log_svn($rep, $fl)
    {
        $this->rep = $rep;
        $this->file = $fl;
        $this->branches = array();
    }

    function processLog($pipe)
    {
        $line = fgets($pipe);

        if (feof($pipe)) {
            return false;
        }

        if (preg_match('/^r([0-9]*) \| (.*?) \| (.*) \(.*\) \| ([0-9]*) lines?$/', $line, $matches)) {
            $this->rev = $matches[1];
            $this->author = $matches[2];
            $this->date = strtotime($matches[3]);
            $size = $matches[4];
        } else {
            $this->err = $line;
            return false;
        }

        fgets($pipe);

        $this->files = array();
        while (($line = trim(fgets($pipe))) != '') {
            $this->files[] = $line;
        }

        for ($i = 0; $i != $size; ++$i) {
            $this->log = $this->log . chop(fgets($pipe)) . "\n";
        }

        $this->log = chop($this->log);
        fgets($pipe);

        return true;
    }

    function queryDate()
    {
        return $this->date;
    }

    function queryRevision()
    {
        return $this->rev;
    }

    function queryAuthor()
    {
        return $this->author;
    }

    function queryLog()
    {
        return $this->log;
    }

    function queryChangedLines()
    {
        return isset($this->lines) ? ($this->lines) : '';
    }

    /**
     * Given a branch revision number, this function remaps it
     * accordingly, and performs a lookup on the file object to
     * return the symbolic name(s) of that branch in the tree.
     *
     * @return hash of symbolic names => branch numbers
     */
    function querySymbolicBranches()
    {
        $symBranches = array();
        foreach ($this->branches as $branch) {
            $parts = explode('.', $branch);
            $last = array_pop($parts);
            $parts[] = '0';
            $parts[] = $last;
            $rev = implode('.', $parts);
            if (isset($this->file->branches[$branch])) {
                $symBranches[$this->file->branches[$branch]] = $branch;
            }
        }
        return $symBranches;
    }

}

/**
 * VC_svn Patchset class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Patchset_svn extends VC_Patchset {

    var $_file;

    /**
     * Create a patchset object.
     *
     * @param string $file  The filename to get patchsets for.
     */
    function VC_Patchset_svn($file)
    {
        $this->_file = $file;
    }

    function &getPatchsetObject($rep, $filename, $cache = null)
    {
        /* The version of the cached data. Increment this whenever the
         * internal storage format changes, such that we must
         * invalidate prior cached data. */
        $cacheVersion = 1;
        $cacheId = $rep->sourceroot() . '_n' . $filename . '_f_v' . $cacheVersion;

        if ($cache &&
            // The file is cached for one hour no matter what, because
            // there is no way to determine with svn the time the file
            // last changed.
            $cache->exists($cacheId, 3600)) {
            $psOb = unserialize($cache->get($cacheId, 3600));
            $psOb->setRepository($rep);
        } else {
            $psOb = new VC_Patchset_svn($filename);
            $psOb->setRepository($rep);
            if (is_a(($result = $psOb->getPatchsets()), 'PEAR_Error')) {
                return $result;
            }

            if ($cache) {
                $cache->set($cacheId, serialize($psOb));
            }
        }

        return $psOb;
    }

    /**
     * Populate the object with information about the patchsets that
     * this file is involved in.
     *
     * @return mixed  PEAR_Error object on error, or true on success.
     */
    function getPatchsets()
    {
        $fileOb = new VC_File_svn($this->_rep, $this->_file);
        if (is_a(($result = $fileOb->getBrowseInfo()), 'PEAR_Error')) {
            return $result;
        }

        $this->_patchsets = array();
        foreach ($fileOb->logs as $rev => $log) {
            $this->_patchsets[$rev] = array();
            $this->_patchsets[$rev]['date'] = $log->queryDate();
            $this->_patchsets[$rev]['author'] = $log->queryAuthor();
            $this->_patchsets[$rev]['branch'] = '';
            $this->_patchsets[$rev]['tag'] = '';
            $this->_patchsets[$rev]['log'] = $log->queryLog();
            $this->_patchsets[$rev]['members'] = array();
            foreach ($log->files as $file) {
                $action = substr($file, 0, 1);
                $file = preg_replace('/.*?\s(.*?)(\s|$).*/', '\\1', $file);
                $to = $rev;
                if ($action == 'A') {
                    $from = 'INITIAL';
                } elseif ($action == 'D') {
                    $from = $to;
                    $to = '(DEAD)';
                } else {
                    // This technically isn't the previous revision,
                    // but it works for diffing purposes.
                    $from = $to - 1;
                }

                $this->_patchsets[$rev]['members'][] = array('file' => $file,
                                                             'from' => $from,
                                                             'to' => $to);
            }
        }

        return true;
    }

}
