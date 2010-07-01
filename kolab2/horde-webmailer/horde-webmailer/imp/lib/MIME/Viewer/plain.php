<?php

require_once 'Horde/MIME/Viewer/plain.php';

/**
 * The IMP_MIME_Viewer_plain class renders out text/plain MIME parts
 * with URLs made into hyperlinks.
 *
 * $Horde: imp/lib/MIME/Viewer/plain.php,v 1.58.8.25 2009-01-06 15:24:09 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_plain extends MIME_Viewer_plain {

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

        global $conf, $prefs;

        $flowed = ($this->mime_part->getContentTypeParameter('format') == 'flowed');
        $text = $this->mime_part->getContents();

        // If calling as an attachment from view.php, we do not want to alter
        // the text in any way with HTML.
        if ($contents->viewAsAttachment()) {
            // Check for 'flowed' text data.
            if ($flowed) {
                $text = $this->_formatFlowed($text, null, 0, $this->mime_part->getContentTypeParameter('delsp'));
            }
            return $text;
        }

        if ($text === false) {
            return $contents->formatStatusMsg(_("There was an error displaying this message part"));
        }

        // Trim extra whitespace in the text.
        $text = rtrim($text);
        if ($text == '') {
            return '';
        }

        // If requested, scan the message for PGP data.
        if (!empty($conf['utils']['gnupg']) &&
            $prefs->getValue('pgp_scan_body') &&
            preg_match('/-----BEGIN PGP ([^-]+)-----/', $text)) {
            require_once IMP_BASE . '/lib/Crypt/PGP.php';
            $imp_pgp = new IMP_PGP();
            if (($out = $imp_pgp->parseMessageOutput($this->mime_part, $contents))) {
                return $out;
            }
        }

        // If requested, scan the message for UUencoded data.
        if ($this->getConfigParam('uuencode')) {
            // Don't want to use convert_uudecode() here as there may be
            // multiple files residing in the text.
            require_once 'Mail/mimeDecode.php';
            $files = &Mail_mimeDecode::uudecode($text);
        }

        // Check for 'flowed' text data.
        if ($flowed) {
            $text = $this->_formatFlowed($text, null, 0, $this->mime_part->getContentTypeParameter('delsp'));
        } else {
            /* A "From" located at the beginning of a line in the body text
             * will be escaped with a '>' by the IMAP server.  Remove this
             * escape character or else the line will display as being
             * quoted. Flowed conversion would have already taken care of this
             * for us. */
            $text = preg_replace('/(\n+)> ?From(\s+)/', "$1From$2", $text);
        }

        // Build filter stack. Starts with HTML markup and tab expansion.
        require_once 'Horde/Text/Filter.php';
        $filters = array('text2html', 'tabs2spaces');
        $filter_params = array(
            array('parselevel' => TEXT_HTML_MICRO,
                  'charset' => $this->mime_part->getCharset()),
            array());

        // Highlight quoted parts of an email.
        if ($prefs->getValue('highlight_text')) {
            $filters[] = 'highlightquotes';

            $show = $prefs->getValue('show_quoteblocks');
            $hideBlocks = ($show == 'hidden') ||
                ($show == 'thread' &&
                 basename(Horde::selfUrl()) == 'thread.php');
            if (!$hideBlocks &&
                in_array($show, array('list', 'listthread')) &&
                is_a($contents, 'IMP_Contents')) {
                $header = $contents->getHeaderOb();
                $list_info = $header->getListInformation();
                $hideBlocks = $list_info['exists'];
            }
            $filter_params[] = array('hideBlocks' => $hideBlocks);
        }

        // Highlight simple markup of an email.
        if ($prefs->getValue('highlight_simple_markup')) {
            $filters[] = 'simplemarkup';
            $filter_params[] = array();
        }

        // Dim signatures.
        if ($prefs->getValue('dim_signature')) {
            $filters[] = 'dimsignature';
            $filter_params[] = array();
        }

        // Filter bad language.
        if ($prefs->getValue('filtering')) {
            $filters[] = 'words';
            $filter_params[] = array('words_file' => $conf['msgsettings']['filtering']['words'],
                                     'replacement' => $conf['msgsettings']['filtering']['replacement']);
        }

        // Run filters.
        $text = Text_Filter::filter($text, $filters, $filter_params);

        // Wordwrap.
        $text = str_replace('  ', ' &nbsp;', $text);
        $text = str_replace("\n ", "\n&nbsp;", $text);
        if (!strncmp($text, ' ', 1)) {
            $text = '&nbsp;' . substr($text, 1);
        }
        $text = '<div class="fixed leftAlign">' . "\n" . $text . '</div>';

        // Replace UUencoded data with links now.
        if ($this->getConfigParam('uuencode') && !empty($files)) {
            foreach ($files as $file) {
                $uupart = new MIME_Part();
                $uupart->setContents($file['filedata']);
                $uupart->setName(strip_tags($file['filename']));

                $uumessage = &MIME_Message::convertMIMEPart($uupart);
                $mc = new MIME_Contents($uumessage, array('download' => 'download_attach', 'view' => 'view_attach'), array(&$contents));
                $mc->buildMessage();

                $text = preg_replace("/begin ([0-7]{3}) (.+)\r?\n(.+)\r?\nend/Us", '<table>' . $mc->getMessage(true) . '</table>', $text, 1);
            }
        }

        return $text;
    }

}
