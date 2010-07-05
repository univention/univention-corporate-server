<?php
/**
 * Sorting options
 */
define('VC_SORT_NONE', 0);        // don't sort
define('VC_SORT_AGE', 1);         // sort by age
define('VC_SORT_NAME', 2);        // sort by filename
define('VC_SORT_REV', 3);         // sort by revision number
define('VC_SORT_AUTHOR', 4);      // sort by author name

define('VC_SORT_ASCENDING', 0);   // ascending order
define('VC_SORT_DESCENDING', 1);  // descending order

define('VC_WINDOWS', !strncasecmp(PHP_OS, 'WIN', 3));

/**
 * Version Control generalized library.
 *
 * $Horde: framework/VC/VC.php,v 1.12.8.14 2008-06-07 16:07:26 chuck Exp $
 *
 * @package VC
 */
class VC {

    /**
     * The source root of the repository.
     *
     * @access protected
     * @var string
     */
    var $_sourceroot;

    /**
     * Hash with the locations of all necessary binaries.
     * @var array
     */
    var $_paths = array();

    /**
     * Hash caching the parsed users file.
     * @var array
     */
    var $_users;

    /**
     * Return the source root for this repository, with no trailing /
     *
     * @return string  Source root for this repository.
     */
    function sourceroot()
    {
        return $this->_sourceroot;
    }

    /**
     * Returns the location of the specified binary.
     *
     * @param string $binary  An external program name.
     *
     * @return boolean|string  The location of the external program or false if
     *                         it wasn't specified.
     */
    function getPath($binary)
    {
        if (isset($this->_paths[$binary])) {
            return $this->_paths[$binary];
        }

        return false;
    }

    /**
     * Parse the users file, if present in the source root, and return
     * a hash containing the requisite information, keyed on the
     * username, and with the 'desc','name', and 'mail' values inside.
     *
     * @return boolean|array  False if the file is not present, otherwise
     *                        $this->_users populated with the data
     */
    function getUsers($usersfile)
    {
        /* Check that we haven't already parsed users. */
        if (isset($this->_users) && is_array($this->_users)) {
            return $this->_users;
        }

        if (!@is_file($usersfile) || !($fl = @fopen($usersfile, VC_WINDOWS ? 'rb' : 'r'))) {
            return false;
        }

        $this->_users = array();

        /* Discard the first line, since it'll be the header info. */
        fgets($fl, 4096);

        /* Parse the rest of the lines into a hash, keyed on
         * username. */
        while ($line = fgets($fl, 4096)) {
            if (preg_match('/^\s*$/', $line)) {
                continue;
            }
            if (!preg_match('/^(\w+)\s+(.+)\s+([\w\.\-\_]+@[\w\.\-\_]+)\s+(.*)$/', $line, $regs)) {
                continue;
            }

            $this->_users[$regs[1]]['name'] = trim($regs[2]);
            $this->_users[$regs[1]]['mail'] = trim($regs[3]);
            $this->_users[$regs[1]]['desc'] = trim($regs[4]);
        }

        return $this->_users;
    }

    /**
     * Attempts to return a concrete VC instance based on $driver.
     *
     * @param mixed $driver  The type of concrete VC subclass to return.
     *                       The code is dynamically included.
     * @param array $params  A hash containing any additional configuration
     *                       or  parameters a subclass might need.
     *
     * @return VC  The newly created concrete VC instance, or PEAR_Error on
     *             failure.
     */
    function &factory($driver, $params = array())
    {
        include_once 'VC/' . $driver . '.php';
        $class = 'VC_' . $driver;
        if (class_exists($class)) {
            $vc = new $class($params);
        } else {
            $vc = PEAR::raiseError($class . ' not found.');
        }

        return $vc;
    }

    /**
     * Attempts to return a reference to a concrete VC instance based
     * on $driver. It will only create a new instance if no VC
     * instance with the same parameters currently exists.
     *
     * This should be used if multiple types of file backends (and,
     * thus, multiple VC instances) are required.
     *
     * This method must be invoked as: $var = &VC::singleton()
     *
     * @param mixed $driver  The type of concrete VC subclass to return.
     *                       The code is dynamically included.
     * @param array $params  A hash containing any additional configuration
     *                       or parameters a subclass might need.
     *
     * @return VC  The concrete VC reference, or PEAR_Error on failure.
     */
    function &singleton($driver, $params = array())
    {
        static $instances = array();

        $signature = serialize(array($driver, $params));
        if (!isset($instances[$signature])) {
            $instances[$signature] = &VC::factory($driver, $params);
        }

        return $instances[$signature];
    }

}

/**
 * @package VC
 */
class VC_Diff {

    /**
     * Obtain a tree containing information about the changes between
     * two revisions.
     *
     * @param array $raw  An array of lines of the raw unified diff,
     *                    normally obtained through VC_Diff::get().
     *
     * @return array
     *
     * @todo document this thoroughly, as the format is a bit complex.
     */
    function humanReadable($raw)
    {
        $ret = array();

        /* Hold the left and right columns of lines for change
         * blocks. */
        $cols = array(array(), array());
        $state = 'empty';

        /* Iterate through every line of the diff. */
        foreach ($raw as $line) {
            /* Look for a header which indicates the start of a diff
             * chunk. */
            if (preg_match('/^@@ \-([0-9]+).*\+([0-9]+).*@@(.*)/', $line, $regs)) {
                /* Push any previous header information to the return
                 * stack. */
                if (isset($data)) {
                    $ret[] = $data;
                }
                $data = array('type' => 'header', 'oldline' => $regs[1],
                              'newline' => $regs[2], 'contents'> array());
                $data['function'] = isset($regs[3]) ? $regs[3] : '';
                $state = 'dump';
            } elseif ($state != 'empty') {
                /* We are in a chunk, so split out the action (+/-)
                 * and the line. */
                preg_match('/^([\+\- ])(.*)/', $line, $regs);
                if (count($regs) > 2) {
                    $action = $regs[1];
                    $content = $regs[2];
                } else {
                    $action = ' ';
                    $content = '';
                }

                if ($action == '+') {
                    /* This is just an addition line. */
                    if ($state == 'dump' || $state == 'add') {
                        /* Start adding to the addition stack. */
                        $cols[0][] = $content;
                        $state = 'add';
                    } else {
                        /* This is inside a change block, so start
                         * accumulating lines. */
                        $state = 'change';
                        $cols[1][] = $content;
                    }
                } elseif ($action == '-') {
                    /* This is a removal line. */
                    $state = 'remove';
                    $cols[0][] = $content;
                } else {
                    /* An empty block with no action. */
                    switch ($state) {
                    case 'add':
                        $data['contents'][] = array('type' => 'add', 'lines' => $cols[0]);
                        break;

                    case 'remove':
                        /* We have some removal lines pending in our
                         * stack, so flush them. */
                        $data['contents'][] = array('type' => 'remove', 'lines' => $cols[0]);
                        break;

                    case 'change':
                        /* We have both remove and addition lines, so
                         * this is a change block. */
                        $data['contents'][] = array('type' => 'change', 'old' => $cols[0], 'new' => $cols[1]);
                        break;
                    }
                    $cols = array(array(), array());
                    $data['contents'][] = array('type' => 'empty', 'line' => $content);
                    $state = 'dump';
                }
            }
        }

        /* Just flush any remaining entries in the columns stack. */
        switch ($state) {
        case 'add':
            $data['contents'][] = array('type' => 'add', 'lines' => $cols[0]);
            break;

        case 'remove':
            /* We have some removal lines pending in our stack, so
             * flush them. */
            $data['contents'][] = array('type' => 'remove', 'lines' => $cols[0]);
            break;

        case 'change':
            /* We have both remove and addition lines, so this is a
             * change block. */
            $data['contents'][] = array('type' => 'change', 'old' => $cols[0], 'new' => $cols[1]);
            break;
        }

        if (isset($data)) {
            $ret[] = $data;
        }

        return $ret;
    }

}

/**
 * @package VC
 */
class VC_File {

    var $rep;
    var $dir;
    var $name;
    var $logs;
    var $revs;
    var $head;
    var $quicklog;
    var $symrev;
    var $revsym;
    var $branches;

    function setRepository($rep)
    {
        $this->rep = $rep;
    }

}

/**
 * VC patchset class.
 *
 * @package VC
 */
class VC_Patchset {

    var $_rep;
    var $_patchsets = array();

    function setRepository($rep)
    {
        $this->_rep = $rep;
    }

}

/**
 * VC revisions class.
 *
 * Copyright Anil Madhavapeddy, <anil@recoil.org>
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @package VC
 */
class VC_Revision {

    /**
     * Validation function to ensure that a revision number is of the
     * right form.
     *
     * @param string $val  Value to check.
     *
     * @return boolean  True if it is a revision number
     */
    function valid($val)
    {
        return $val && preg_match('/^[\d\.]+$/', $val);
    }

    /**
     * Given a revision number, remove a given number of portions from
     * it. For example, if we remove 2 portions of 1.2.3.4, we are
     * left with 1.2.
     *
     * @param string $val      Input revision
     * @param integer $amount  Number of portions to strip
     *
     * @return string  Stripped revision number
     */
    function strip($val, $amount = 1)
    {
        if (!VC_Revision::valid($val)) {
            return false;
        }
        $pos = 0;
        while ($amount-- > 0 && ($pos = strrpos($val, '.')) !== false) {
            $val = substr($val, 0, $pos);
        }
        return $pos !== false ? $val : false;
    }

    /**
     * The size of a revision number is the number of portions it has.
     * For example, 1,2.3.4 is of size 4.
     *
     * @param string $val  Revision number to determine size of
     *
     * @return integer  Size of revision number
     */
    function sizeof($val)
    {
        if (!VC_Revision::valid($val)) {
            return false;
        }

        return (substr_count($val, '.') + 1);
    }

    /**
     * Given two revision numbers, this figures out which one is
     * greater than the other by stepping along the decimal points
     * until a difference is found, at which point a sign comparison
     * of the two is returned.
     *
     * @param string $rev1  Period delimited revision number
     * @param string $rev2  Second period delimited revision number
     *
     * @return integer  1 if the first is greater, -1 if the second if greater,
     *                  and 0 if they are equal
     */
    function cmp($rev1, $rev2)
    {
        return version_compare($rev1, $rev2);
    }

    /**
     * Return the logical revision before this one. Normally, this
     * will be the revision minus one, but in the case of a new
     * branch, we strip off the last two decimal places to return the
     * original branch point.
     *
     * @param string $rev  Revision number to decrement.
     *
     * @return string|boolean  Revision number, or false if none could be
     *                         determined.
     */
    function prev($rev)
    {
        $last_dot = strrpos($rev, '.');
        $val = substr($rev, ++$last_dot);

        if (--$val > 0) {
            return substr($rev, 0, $last_dot) . $val;
        } else {
            $last_dot--;
            while (--$last_dot) {
                if ($rev[$last_dot] == '.') {
                    return  substr($rev, 0, $last_dot);
                } elseif ($rev[$last_dot] == null) {
                    return false;
                }
            }
        }
    }

}
