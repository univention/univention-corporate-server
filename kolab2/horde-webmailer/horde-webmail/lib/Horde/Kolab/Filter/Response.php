<?php
/**
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Response.php,v 1.3.2.2 2009-02-24 11:17:39 wrobel Exp $
 *
 * @package Kolab_Filter
 */

/* Require the PEAR library for PEAR errors */
require_once 'PEAR.php';

/* Some output constants */
define( 'OUT_STDOUT', 128 );
define( 'OUT_LOG', 256 );

/* Failure constants from postfix src/global/sys_exits.h */
define('EX_USAGE', 64);       /* command line usage error */
define('EX_DATAERR', 65);     /* data format error */
define('EX_NOINPUT', 66);     /* cannot open input */
define('EX_NOUSER', 67);      /* user unknown */
define('EX_NOHOST', 68);      /* host name unknown */
define('EX_UNAVAILABLE', 69); /* service unavailable */
define('EX_SOFTWARE', 70);    /* internal software error */
define('EX_OSERR', 71);       /* system resource error */
define('EX_OSFILE', 72);      /* critical OS file missing */
define('EX_CANTCREAT', 73);   /* can't create user output file */
define('EX_IOERR', 74);       /* input/output error */
define('EX_TEMPFAIL', 75);    /* temporary failure */
define('EX_PROTOCOL', 76);    /* remote error in protocol */
define('EX_NOPERM', 77);      /* permission denied */
define('EX_CONFIG', 78);      /* local configuration error */

/**
 * Provides error handling for the Kolab server filter scripts.
 *
 * $Horde: framework/Kolab_Filter/lib/Horde/Kolab/Filter/Response.php,v 1.3.2.2 2009-02-24 11:17:39 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @package Kolab_Filter
 */
class Horde_Kolab_Filter_Response
{

    /**
     * Constructor.
     */
    function Horde_Kolab_Filter_Response()
    {
        /* Set a custom PHP error handler to catch any coding errors */
        set_error_handler(array($this, '_fatal'));
    }

    /**
     * Handle the results of the message transport.
     *
     * @param mixed $result The reponse of the transport.
     */
    function handle($result)
    {
        /* No error? Be happy and exit clean */
        if (!is_a($result, 'PEAR_Error')) {
            exit(0);
        }

        $msg = $result->getMessage();
        $code = $result->getCode();

        if ($code & OUT_STDOUT) {
            fwrite(STDOUT, $msg);
        }
        if  ($code & OUT_LOG || empty($code)) {
            $this->_log($result);
        }

        // FIXME: Add a userinfo handler in case there were multiple
        // combined errors

        /* If we have an error code we want to return it to the
         * calling application and exit here
         */
        if ($code) {
            /* Return the first seven bits as error code to postfix */
            exit($code & 127);
        }
    }

    /**
     * An alternative PHP error handler so that we don't drop silent
     * on fatal errors.
     *
     * @param int    $errno    The error number.
     * @param string $errmsg   The error message.
     * @param string $filename The file where the error occured.
     * @param int    $linenum  The line where the error occured.
     * @param mixed  $vars     ?
     *
     * @return boolean Always false.
     */
    function _fatal($errno, $errmsg, $filename, $linenum, $vars)
    {
        /* Ignore strict errors for now since even PEAR will raise
         * strict notices 
         */
        if ($errno == E_STRICT) {
            return false;
        }

        $fatal = array(E_ERROR,
                       E_PARSE,
                       E_CORE_ERROR,
                       E_COMPILE_ERROR,
                       E_USER_ERROR);

        if (in_array($errno, $fatal)) {
            $code = OUT_STDOUT | OUT_LOG | EX_UNAVAILABLE;
            $msg = 'CRITICAL: You hit a fatal bug in kolab-filter. Please inform the Kolab developers at https://www.intevation.de/roundup/kolab/. The error was: ' . $errmsg;
        } else {
            $code = 0;
            $msg = 'PHP Error: ' . $errmsg;
        }

        $error = &new PEAR_Error($msg, $code);
        $this->handle($error);

        return false;
    }

    /**
     * Log an error.
     *
     * @param PEAR_error $result The reponse of the transport.
     */
    function _log($result)
    {
        global $conf;

        $msg = $result->getMessage() . '; Code: ' . $result->getCode();

        /* Log all errors */
        $file = __FILE__;
        $line = __LINE__;

        $frames = $result->getBacktrace();
        if (count($frames) > 1) {
            $frame = $frames[1];
        } else if (count($frames) == 1) {
            $frame = $frames[0];
        }
        if (isset($frame['file'])) {
            $file = $frame['file'];
        }
        if (isset($frame['line'])) {
            $line = $frame['line'];
        }

        /* In debugging mode the errors get delivered to the screen
         * without a time stamp (mainly because of unit testing) 
         */
        if (!isset($conf['kolab']['filter']['debug'])
            || !$conf['kolab']['filter']['debug']) {
            Horde::logMessage($msg, $file, $line, PEAR_LOG_ERR);
        } else {
            $msg .= ' (Line ' . $frame['line'] . ' in ' . basename($frame['file']) . ")\n";
            fwrite(STDOUT, $msg);
        }
    }
}
