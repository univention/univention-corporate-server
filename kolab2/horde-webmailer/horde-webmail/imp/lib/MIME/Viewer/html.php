<?php

require_once 'Horde/MIME/Viewer/html.php';

/**
 * The MIME_Viewer_html class renders out HTML text with an effort to
 * remove potentially malicious code.
 *
 * $Horde: imp/lib/MIME/Viewer/html.php,v 1.75.2.40 2009-07-07 22:04:51 slusarz Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Anil Madhavapeddy <anil@recoil.org>
 * @author  Jon Parise <jon@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @package Horde_MIME_Viewer
 */
class IMP_MIME_Viewer_html extends MIME_Viewer_html {

    /**
     * The regular expression to catch any tags and attributes that load
     * external images.
     *
     * @var string
     */
    var $_img_regex = '/
        # match 1
        (
            # <img> tags
            <img[^>]+?src=
            # <input> tags
            |<input[^>]+?src=
            # "background" attributes
            |<body[^>]+?background=|<td[^>]*background=|<table[^>]*background=
            # "style" attributes; match 2; quotes: match 3
            |(style=\s*("|\')?[^>]*?background(?:-image)?:(?(3)[^"\']|[^>])*?url\s*\()
        )
        # whitespace
        \s*
        # opening quotes, parenthesis; match 4
        ("|\')?
        # the image url; match 5
        ((?(2)
            # matched a "style" attribute
            (?(4)[^"\')>]*|[^\s)>]*)
            # did not match a "style" attribute
            |(?(4)[^"\'>]*|[^\s>]*)
        ))
        # closing quotes
        (?(4)\\4)
        # matched a "style" attribute?
        (?(2)
            # closing parenthesis
            \s*\)
            # remainder of the "style" attribute; match 6
            ((?(3)[^"\'>]*|[^\s>]*))
        )
        /isx';

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

        $attachment = $contents->viewAsAttachment();
        $data = $this->mime_part->getContents();
        $msg_charset = $this->mime_part->getCharset();

        /* Run tidy on the HTML. */
        if ($this->getConfigParam('tidy') &&
            ($tidy_config = IMP::getTidyConfig(String::length($data)))) {
            if ($msg_charset == 'us-ascii') {
                $tidy = tidy_parse_string($data, $tidy_config, 'ascii');
                $tidy->cleanRepair();
                $data = tidy_get_output($tidy);
            } else {
                $tidy = tidy_parse_string(String::convertCharset($data, $msg_charset, 'UTF-8'), $tidy_config, 'utf8');
                $tidy->cleanRepair();
                $data = String::convertCharset(tidy_get_output($tidy), 'UTF-8', $msg_charset);
            }
        }

        /* Sanitize the HTML. */
        $data = $this->_cleanHTML($data);

        /* Reset absolutely positioned elements. */
        if (!$attachment) {
            $data = preg_replace('/(style\s*=\s*)(["\'])?([^>"\']*)position\s*:\s*absolute([^>"\']*)\2/i',
                                 '$1"$3$4"',
                                 $data);
        }

        /* Search for inlined images that we can display. */
        $related = $this->mime_part->getInformation('related_part');
        if ($related !== false) {
            $relatedPart = $contents->getMIMEPart($related);
            foreach ($relatedPart->getCIDList() as $ref => $id) {
                $id = trim($id, '<>');
                $cid_part = $contents->getDecodedMIMEPart($ref);
                $data = str_replace("cid:$id", $contents->urlView($cid_part, 'view_attach'), $data);
            }
        }

        /* Convert links to open in new windows. */
        $data = $this->_openLinksInNewWindow($data);

        /* Turn mailto: links into our own compose links. */
        if (!$attachment && $GLOBALS['registry']->hasMethod('mail/compose')) {
            $data = preg_replace_callback('/href\s*=\s*(["\'])?mailto:((?(1)[^\1]*?|[^\s>]+))(?(1)\1|)/i',
                                          array($this, '_mailtoCallback'),
                                          $data);
        }

        /* Filter bad language. */
        $data = IMP::filterText($data);

        if ($attachment) {
            $charset = $this->mime_part->getCharset();
        } else {
            $charset = NLS::getCharset();
            /* Put div around message. */
            $data = '<div id="html-message">' . $data . '</div>';
        }

        /* Only display images if specifically allowed by user. */
        $msg = '';
        $script = '';
        if (!IMP::printMode() &&
            $GLOBALS['prefs']->getValue('html_image_replacement')) {

            /* Check to see if images exist. */
            if (preg_match($this->_img_regex, $data)) {
                /* Make sure the URL parameters are correct for the current
                 * message. */
                $url = Util::removeParameter(Horde::selfUrl(true), array('index'));
                if (!$attachment) {
                    $url = Util::removeParameter($url, array('actionID'));
                }
                $base_ob = &$contents->getBaseObjectPtr();
                $url = Util::addParameter($url, 'index', $base_ob->getMessageIndex());

                $view_img = Util::getFormData('view_html_images');
                $addr_check = ($GLOBALS['prefs']->getValue('html_image_addrbook') && $this->_inAddressBook($contents));

                if (!$view_img && !$addr_check) {
                    $script = Util::bufferOutput(array('Horde', 'addScriptFile'), 'prototype.js', 'imp', true);
                    $script .= Util::bufferOutput(array('Horde', 'addScriptFile'), 'unblockImages.js', 'imp', true);
                    $url = Util::addParameter($url, 'view_html_images', 1);
                    $attributes = $attachment ? array('style' => 'color:blue') : array();
                    $msg = Horde::img('mime/image.png') . ' ' . String::convertCharset(_("Images have been blocked to protect your privacy."), NLS::getCharset(), $charset) . ' ' . Horde::link($url, '', '', '', 'return IMP.unblockImages(' . ($attachment ? 'document.body' : '$(\'html-message\')') . ', \'block-images\');', '', '', $attributes) . String::convertCharset(_("Show Images?"), NLS::getCharset(), $charset) . '</a>';
                    $data = preg_replace_callback($this->_img_regex, array($this, '_blockImages'), $data);
                    if ($attachment) {
                        $msg = '<span style="background:#fff;color:#000">' . nl2br($msg) . '</span><br />';
                    }
                    $msg = '<span id="block-images">' . $msg . '</span>';
                }
            }
        }

        /* If we are viewing inline, give option to view in separate window. */
        if (!$attachment && $this->getConfigParam('external')) {
            if ($msg) {
                $msg = str_replace('</span>', ' | </span>', $msg);
            }
            $msg .= $contents->linkViewJS($this->mime_part, 'view_attach', _("Show this HTML in a new window?"));
        }

        $msg = $contents->formatStatusMsg($msg, null, false);
        if (stristr($data, '<body') === false) {
            return $script . $msg . $data;
        } else {
            return preg_replace('/(<body.*?>)/is', '$1' . $script . $msg, $data);
        }
    }

    /**
     */
    function _mailtoCallback($m)
    {
        // TODO: Move charset conversion into html_entity_decode() once we
        // require PHP 5.0.0.+
        return 'href="' . $GLOBALS['registry']->call('mail/compose', array(String::convertCharset(html_entity_decode($m[2]), 'iso-8859-1', NLS::getCharset()))) . '"';
    }

    /**
     * Called from the image-blocking regexp to construct the new
     * image tags.
     *
     * @param array $matches
     *
     * @return string The new image tag.
     */
    function _blockImages($matches)
    {
        static $blockimg;
        if (!isset($blockimg)) {
            $blockimg = Horde::url($GLOBALS['registry']->getImageDir('imp') . '/spacer_red.png', false, -1);
        }

        return empty($matches[2])
            ? $matches[1] . '"' . $blockimg . '" blocked="' . rawurlencode(str_replace('&amp;', '&', trim($matches[5], '\'" '))) . '"'
            : $matches[1] . "'" . $blockimg . '\')' . $matches[6] . '" blocked="' . rawurlencode(str_replace('&amp;', '&', trim($matches[5], '\'" ')));
    }

    /**
     * Determine whether the sender appears in an available addressbook.
     *
     * @access private
     *
     * @param MIME_Contents &$contents  The MIME_Contents object.
     *
     * @return boolean  Does the sender appear in an addressbook?
     */
    function _inAddressBook(&$contents)
    {
        global $registry, $prefs;

        /* If we don't have access to the sender information, return false. */
        $base_ob = &$contents->getBaseObjectPtr();

        /* If we don't have a contacts provider available, give up. */
        if (!$registry->hasMethod('contacts/getField')) {
            return false;
        }

        $sources = explode("\t", $prefs->getValue('search_sources'));
        if ((count($sources) == 1) && empty($sources[0])) {
            $sources = array();
        }

        /* Try to get back a result from the search. */
        $result = $registry->call('contacts/getField', array($base_ob->getFromAddress(), '__key', $sources, false, true));
        if (is_a($result, 'PEAR_Error')) {
            return false;
        } else {
            return (count($result) > 0);
        }
    }

    /**
     * Convert links to open in a new window.
     *
     * @param string $data Text to convert.
     */
    function _openLinksInNewWindow($data)
    {
        /* Convert links to open in new windows. First we hide all
         * mailto: links, links that have an "#xyz" anchor and ignore
         * all links that already have a target. */
        return preg_replace(
            array('/<a\s([^>]*\s+href=["\']?(#|mailto:))/i',
                  '/<a\s([^>]*)\s+target=["\']?[^>"\'\s]*["\']?/i',
                  '/<a\s/i',
                  '/<area\s([^>]*\s+href=["\']?(#|mailto:))/i',
                  '/<area\s([^>]*)\s+target=["\']?[^>"\'\s]*["\']?/i',
                  '/<area\s/i',
                  "/\x01/",
                  "/\x02/"),
            array("<\x01\\1",
                  "<\x01 \\1 target=\"_blank\"",
                  '<a target="_blank" ',
                  "<\x02\\1",
                  "<\x02 \\1 target=\"_blank\"",
                  '<area target="_blank" ',
                  'a ',
                  'area '),
            $data);
    }

}
