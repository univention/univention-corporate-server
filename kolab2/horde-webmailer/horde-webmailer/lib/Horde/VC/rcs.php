<?php
/**
 * VC_rcs implementation.
 *
 * Copyright 2004-2007 Jeff Schwentner <jeffrey.schwentner@lmco.com>
 *
 * $Horde: framework/VC/VC/rcs.php,v 1.3.8.7 2007-12-20 13:50:17 jan Exp $
 *
 * @author  Jeff Schwentner <jeffrey.schwentner@lmco.com>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package VC
 */
class VC_rcs extends VC {

    /**
     * Checks an RCS file in with a specified change log.
     *
     * @param string $filepath    Location of file to check in.
     * @param string $message     Log of changes since last version.
     * @param string $user        The user name to use for the check in.
     * @param boolean $newBinary  Does the change involve binary data?
     *
     * @return string|object  The new revision number on success, or a
     *                        PEAR_Error object on failure.
     */
    function ci($filepath, $message, $user = null, $newBinary = false)
    {
        if ($user) {
            putenv('LOGNAME=' . $user);
        } else {
            putenv('LOGNAME=guest');
        }

        $Q = VC_WINDOWS ? '"' : "'" ;

        $ci_cmd = $this->getPath('ci') . ' ' . $Q . $filepath . $Q.' 2>&1';
        $rcs_cmd = $this->getPath('rcs') . ' -i -kb ' . $Q . $filepath . $Q.' 2>&1';
        $output = '';

        $message_lines = explode("\n", $message);

        $pipe_def = array(0 => array("pipe", 'r'),
                          1 => array("pipe", 'w'));

        if ($newBinary) {
            $process = proc_open($rcs_cmd, $pipe_def, $pipes);
        } else {
            $process = proc_open($ci_cmd, $pipe_def, $pipes);
        }

        if (is_resource($process)) {
            foreach ($message_lines as $line) {
                if ($line == '.\n') {
                    $line = '. \n';
                }
                fwrite($pipes[0], $line);
            }

            fwrite($pipes[0], "\n.\n");
            fclose($pipes[0]);

            while (!feof($pipes[1])) {
                $output .= fread($pipes[1], 8192);
            }
            fclose($pipes[1]);
            proc_close($process);
        } else {
            return PEAR::raiseError('Failed to open pipe in ci()');
        }

        if ($newBinary) {
            exec($ci_cmd . ' 2>&1', $return_array, $retval);

            if ($retval) {
                return PEAR::raiseError("Unable to spawn ci on $filepath from ci()");
            } else {
                foreach ($return_array as $line) {
                    $output .= $line;
                }
            }
        }

        $rev_start = strpos($output, 'new revision: ');

        // If no new revision, see if this is an initial checkin.
        if ($rev_start === false) {
            $rev_start = strpos($output, 'initial revision: ');
            $rev_end = strpos($output, ' ', $rev_start);
        } else {
            $rev_end = strpos($output, ';', $rev_start);
        }

        if ($rev_start !== false && $rev_end !== false) {
            $rev_start += 14;
            return substr($output, $rev_start, $rev_end - $rev_start);
        } else {
            unlock($filepath);
            $temp_pos = strpos($output, 'file is unchanged');
            if ($temp_pos !== false) {
                return PEAR::raiseError('Check-in Failure: ' . basename($filepath) . ' has not been modified');
            } else {
                return PEAR::raiseError("Failed to checkin $filepath, $ci_cmd, $output");
            }
        }
    }

    /**
     * Checks the locks on a CVS/RCS file.
     *
     * @param string $filepath    Location of file.
     * @param string &$locked_by  Returns the username holding the lock.
     *
     * @return boolean|object  True on success, or a PEAR_Error on failure.
     */
    function isLocked($filepath, &$locked_by)
    {
        $rlog_cmd  = $this->getPath('rlog');
        $rlog_flag = ' -L ';

        $Q = VC_WINDOWS ? '"' : "'";

        $cmd = $rlog_cmd . $rlog_flag . $Q . $filepath . $Q;

        exec($cmd.' 2>&1', $return_array, $retval);

        if ($retval) {
            return PEAR::raiseError("Unable to spawn rlog on $filepath from isLocked()");
        } else {
            $output = '';

            foreach ($return_array as $line) {
                $output .= $line;
            }

            $start_name = strpos($output, 'locked by: ');
            $end_name = strpos($output, ';', $start_name);

            if ($start_name !== false && $end_name !== false) {
                $start_name += 11;
                $locked_by = substr($output, $start_name, $end_name - $start_name);
                return true;
            }  elseif (strlen($output) == 0) {
                return false;
            } else {
                return PEAR::raiseError('Failure running rlog in isLocked()');
            }
        }
    }

    /**
     * Locks a CVS/RCS file.
     *
     * @param string $filepath  Location of file.
     * @param string $user      User name to lock the file with
     *
     * @return boolean|object  True on success, or a PEAR_Error on failure.
     */
    function lock($filepath, $user = null)
    {
        // Get username for RCS tag.
        if ($user) {
            putenv('LOGNAME=' . $user);
        } else {
            putenv('LOGNAME=guest');
        }

        $rcs_cmd = $this->getPath('rcs');
        $rcs_flag = ' -l ';

        $Q = VC_WINDOWS ? '"' : "'" ;
        $cmd = $rcs_cmd . $rcs_flag . $Q . $filepath . $Q;
        exec($cmd.' 2>&1', $return_array, $retval);

        if ($retval) {
            return PEAR::raiseError('Failed to spawn rcs ("' . $cmd . '") on "' . $filepath . '" (returned ' . $retval . ')');
        } else {
            $output = '';
            foreach ($return_array as $line) {
                $output .= $line;
            }

            $locked_pos = strpos($output, 'locked');
            if ($locked_pos !== false) {
                return true;
            } else {
                return PEAR::raiseError('Failed to lock "' . $filepath . '" (Ran "' . $cmd . '", got return code ' . $retval . ', output: ' . $output . ')');
            }
        }
    }

    /**
     * Unlocks a CVS/RCS file.
     *
     * @param string $filepath  Location of file.
     * @param string $user      User name to unlock the file with
     *
     * @return boolean|object  True on success, or a PEAR_Error on failure.
     */
    function unlock($filepath, $user = null)
    {
        // Get username for RCS tag.
        if ($user) {
            putenv('LOGNAME=' . $user);
        } else {
            putenv('LOGNAME=guest');
        }

        $rcs_cmd = $this->getPath('rcs');
        $rcs_flag = ' -u ';

        $Q = VC_WINDOWS ? '"' : "'" ;
        $cmd = $rcs_cmd . $rcs_flag . $Q . $filepath . $Q;
        exec($cmd . ' 2>&1', $return_array, $retval);

        if ($retval) {
            return PEAR::raiseError('Failed to spawn rcs ("' . $cmd . '") on "' . $filepath . '" (returned ' . $retval . ')');
        } else {
            $output = '';

            foreach ($return_array as $line) {
                $output .= $line;
            }

            $unlocked_pos = strpos($output, 'unlocked');

            if ($unlocked_pos !== false) {
                return true;
            } else {
                // Already unlocked.
                return true;
            }
        }
    }

}
