<?php
/**
 * The IMP_MIME_Viewer_partial class allows multipart/partial messages to be
 * displayed (RFC 2046 [5.2.2]).
 *
 * $Horde: imp/lib/MIME/Viewer/partial.php,v 1.17.10.14 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_partial extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * @param array $params  An array with a reference to a MIME_Contents
     *                       object.
     *
     * @return string  The rendered text in HTML.
     */
    function render($params)
    {
        $contents = &$params[0];

        $base_ob = &$contents->getBaseObjectPtr();
        $curr_index = $base_ob->getMessageIndex();
        $id = $this->mime_part->getContentTypeParameter('id');
        $parts = array();

        require_once IMP_BASE . '/lib/IMAP/Search.php';
        require_once 'Horde/MIME/Contents.php';
        require_once 'Horde/MIME/Structure.php';

        /* Perform the search to find the other parts of the message. */
        $imap_search = &IMP_IMAP_Search::singleton(array('pop3' => ($_SESSION['imp']['base_protocol'] == 'pop3')));
        $query = new IMP_IMAP_Search_Query();
        $query->header('Content-Type', $id);
        $indices = $imap_search->searchMailbox($query, null, $GLOBALS['imp_mbox']['thismailbox']);

        /* If not able to find the other parts of the message, print error. */
        if (count($indices) != $this->mime_part->getContentTypeParameter('total')) {
            return $contents->formatStatusMsg(sprintf(_("Cannot display - found only %s of %s parts of this message in the current mailbox."), count($indices), $this->mime_part->getContentTypeParameter('total')));
        }

        /* Get the contents of each of the parts. */
        foreach ($indices as $val) {
            /* No need to fetch the current part again. */
            if ($val == $curr_index) {
                $parts[$this->mime_part->getContentTypeParameter('number')] = $this->mime_part->getContents();
            } else {
                require_once IMP_BASE . '/lib/MIME/Contents.php';
                require_once IMP_BASE . '/lib/MIME/Headers.php';
                $imp_contents = &IMP_Contents::singleton($val . IMP_IDX_SEP . $GLOBALS['imp_mbox']['thismailbox']);
                $part = &$imp_contents->getMIMEPart(0);
                $parts[$part->getContentTypeParameter('number')] = $imp_contents->getBody();
            }
        }

        /* Sort the parts in numerical order. */
        ksort($parts, SORT_NUMERIC);

        /* Combine the parts and render the underlying data. */
        $mime_message = &MIME_Structure::parseTextMIMEMessage(implode('', $parts));
        $mc = new MIME_Contents($mime_message, array('download' => 'download_attach', 'view' => 'view_attach'), array(&$contents));
        $mc->buildMessage();

        return '<table>' . $mc->getMessage(true) . '</table>';
    }

    /**
     * Return the content-type of the rendered output.
     *
     * @return string  The content-type of the output.
     */
    function getType()
    {
        return 'text/html; charset=' . NLS::getCharset();
    }

}
