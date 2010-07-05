<?php
/**
 * Provides simple views.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/View.php,v 1.6.2.1 2009-03-06 18:12:01 wrobel Exp $
 *
 * @package Kolab_FreeBusy
 */

/**
 * The Horde_Kolab_FreeBusy_View:: class renders data.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/View.php,v 1.6.2.1 2009-03-06 18:12:01 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_View {

    /**
     * The data that should get rendered.
     *
     * @var array
     */
    var $_data;

    /**
     * Constructor.
     *
     * @param array $data The data to display
     */
    function Horde_Kolab_FreeBusy_View(&$data)
    {
        $this->_data = $data;
    }

    /**
     * Render the data.
     */
    function render()
    {
        echo 'Not implemented!';
    }
}

/**
 * The Horde_Kolab_FreeBusy_View_vfb:: class renders free/busy data.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/View.php,v 1.6.2.1 2009-03-06 18:12:01 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <p@rdus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_View_vfb extends Horde_Kolab_FreeBusy_View {

    /**
     * The free/busy data that should be displayed.
     *
     * @var Horde_iCalendar
     */
    var $_vfb;

    /**
     * Current timestamp.
     *
     * @var int
     */
    var $_ts;

    /**
     * Constructor.
     *
     * @param Horde_iCalendar $vfb The free/busy data to display.
     */
    function Horde_Kolab_FreeBusy_View_vfb(&$data)
    {

        $data['vfb'] = $data['fb']->exportvCalendar();

        $ts = time();

        $components = &$data['fb']->getComponents();
        foreach ($components as $component) {
            if ($component->getType() == 'vFreebusy') {
                $attr = $component->getAttribute('DTSTAMP');
                if (!empty($attr) && !is_a($attr, 'PEAR_Error')) {
                    $ts = $attr;
                    break;
                }
            }
        }

        $data['ts'] = $ts;

        Horde_Kolab_FreeBusy_View::Horde_Kolab_FreeBusy_View($data);
    }

    /**
     * Display the free/busy information.
     *
     * @param string $content File name of the offered file.
     */
    function render()
    {
        global $conf;

        if (!empty($conf['fb']['send_content_type'])) {
            $send_content_type = $conf['fb']['send_content_type'];
        } else {
            $send_content_type = false;
        }

        if (!empty($conf['fb']['send_content_length'])) {
            $send_content_length = $conf['fb']['send_content_length'];
        } else {
            $send_content_length = false;
        }

        if (!empty($conf['fb']['send_content_disposition'])) {
            $send_content_disposition = $conf['fb']['send_content_disposition'];
        } else {
            $send_content_disposition = false;
        }

        /* Ensure that the data doesn't get cached along the way */
        header('Cache-Control: no-store, no-cache, must-revalidate');
        header('Cache-Control: post-check=0, pre-check=0', false);
        header('Pragma: no-cache');
        header('Expires: Mon, 26 Jul 1997 05:00:00 GMT');
        header('Last-Modified: ' . gmdate("D, d M Y H:i:s", $this->_data['ts']) . ' GMT');
        header('Pragma: public');
        header('Content-Transfer-Encoding: none');
        if ($send_content_type) {
            header('Content-Type: text/calendar');
        }
        if ($send_content_length) {
            header('Content-Length: ' . strlen($this->_data['vfb']));
        }
        if ($send_content_disposition) {
            header('Content-Disposition: attachment; filename="' . $this->_data['name'] . '"');
        }

        echo $this->_data['vfb'];

        exit(0);
    }
}

/** Error types */
define('FREEBUSY_ERROR_NOTFOUND', 0);
define('FREEBUSY_ERROR_UNAUTHORIZED', 1);
define('FREEBUSY_ERROR_SERVER', 2);

/**
 * The Horde_Kolab_FreeBusy_View_error:: class provides error pages for the 
 * Kolab free/busy system.
 *
 * $Horde: framework/Kolab_FreeBusy/lib/Horde/Kolab/FreeBusy/View.php,v 1.6.2.1 2009-03-06 18:12:01 wrobel Exp $
 *
 * Copyright 2004-2008 Klarälvdalens Datakonsult AB
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Steffen Hansen <steffen@klaralvdalens-datakonsult.se>
 * @package Kolab_FreeBusy
 */
class Horde_Kolab_FreeBusy_View_error extends Horde_Kolab_FreeBusy_View {

    /**
     * Display the error information.
     */
    function render()
    {
        switch ($this->_data['type']) {
        case FREEBUSY_ERROR_NOTFOUND:
            $this->notFound($this->_data['error']);
            exit(1);
        case FREEBUSY_ERROR_UNAUTHORIZED:
            $this->unauthorized($this->_data['error']);
            exit(1);
        case FREEBUSY_ERROR_SERVER:
            $this->serverError($this->_data['error']);
            exit(1);
        }
    }

    /**
     * Deliver a "Not Found" page
     *
     * @param PEAR_Error $error    The error.
     */
    function notFound($error)
    {
        $headers = array('HTTP/1.0 404 Not Found');
        if (isset($_SERVER['REQUEST_URI'])) {
            $url = htmlentities($_SERVER['REQUEST_URI']);
        } else {
            $url = '/';
        }
        $message = sprintf(_("The requested URL %s was not found on this server."), $url);

        $this->_errorPage($error, $headers, _("404 Not Found"), _("Not found"), $message);
    }

    /**
     * Deliver a "Unauthorized" page
     *
     * @param PEAR_Error $error    The error.
     */
    function unauthorized($error)
    {
        global $conf;

        if (!empty($conf['kolab']['imap']['maildomain'])) {
            $email_domain = $conf['kolab']['imap']['maildomain'];
        } else {
            $email_domain = 'localhost';
        }

        $headers = array('WWW-Authenticate: Basic realm="freebusy-' . $email_domain . '"',
                         'HTTP/1.0 401 Unauthorized');

        $this->_errorPage($error, $headers, _("401 Unauthorized"), _("Unauthorized"),
                  _("You are not authorized to access the requested URL."));
    }

    /**
     * Deliver a "Server Error" page
     *
     * @param PEAR_Error $error    The error.
     */
    function serverError($error)
    {
        $headers = array('HTTP/1.0 500 Server Error');
        if (isset($_SERVER['REQUEST_URI'])) {
            $url = htmlentities($_SERVER['REQUEST_URI']);
        } else {
            $url = '/';
        }
        $this->_errorPage($error, $headers, _("500 Server Error"), _("Error"),
                  htmlentities($$url));
    }

    /**
     * Deliver an error page
     *
     * @param PEAR_Error $error    The error.
     * @param array      $headers  The HTTP headers to deliver with the response
     * @param string     $title    The page title
     * @param string     $headline The headline of the page
     * @param string     $body     The message to display on the page
     */
    function _errorPage($error, $headers, $title, $headline, $body)
    {
        global $conf;

        /* Print the headers */
        foreach ($headers as $line) {
            header($line);
        }

        /* Print the page */
        echo "<!DOCTYPE HTML PUBLIC \"-//IETF//DTD HTML 2.0//EN\">\n";
        echo "<html><head><title>" . $title . "</title></head>\n";
        echo "<body>\n";
        echo "<h1>" . $headline . "</h1>\n";
        echo "<p>" . $body . "</p>\n";
        if (!empty($error)) {
            echo "<hr><pre>" . $error->getMessage() . "</pre>\n";
            Horde::logMessage($error, __FILE__, __LINE__, PEAR_LOG_ERR);
        }
        echo "<hr>\n";
        echo isset($_SERVER['SERVER_SIGNATURE'])?$_SERVER['SERVER_SIGNATURE']:'' . "\n";
        echo "</body></html>\n";
    }
}

