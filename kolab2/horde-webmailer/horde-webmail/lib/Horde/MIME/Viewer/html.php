<?php
/**
 * The MIME_Viewer_html class renders out HTML text with an effort to
 * remove potentially malicious code.
 *
 * $Horde: framework/MIME/MIME/Viewer/html.php,v 1.14.4.33 2009-03-18 22:40:24 jan Exp $
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
class MIME_Viewer_html extends MIME_Viewer {

    /**
     * Render out the currently set contents.
     *
     * @param array $params  Any parameters the viewer may need.
     *
     * @return string  The rendered text.
     */
    function render($params = null)
    {
        return $this->_cleanHTML($this->mime_part->getContents());
    }

    /**
     * Filters active content, dereferences external links, detects phishing,
     * etc.
     *
     * @access private
     * @todo Use IP checks from
     * http://lxr.mozilla.org/mailnews/source/mail/base/content/phishingDetector.js.
     *
     * @param string $data  The HTML data.
     *
     * @return string  The cleaned HTML data.
     */
    function _cleanHTML($data)
    {
        global $browser, $prefs;

        $phish_warn = false;

        require_once 'Horde/MIME/Contents.php';
        $attachment = MIME_Contents::viewAsAttachment();

        /* Deal with <base> tags in the HTML, since they will screw up our own
         * relative paths. */
        if (preg_match('/<base href="?([^"> ]*)"? ?\/?>/i', $data, $matches)) {
            $base = $matches[1];
            if (substr($base, -1, 1) != '/') {
                $base .= '/';
            }

            /* Recursively call _cleanHTML() to prevent clever fiends from
             * sneaking nasty things into the page via $base. */
            $base = $this->_cleanHTML($base);
        }

        /* Attempt to fix paths that were relying on a <base> tag. */
        if (!empty($base)) {
            $pattern = array('|src=(["\'])([^:"\']+)\1|i',
                             '|src=([^: >"\']+)|i',
                             '|href= *(["\'])([^:"\']+)\1|i',
                             '|href=([^: >"\']+)|i');
            $replace = array('src=\1' . $base . '\2\1',
                             'src=' . $base . '\1',
                             'href=\1' . $base . '\2\1',
                             'href=' . $base . '\1');
            $data = preg_replace($pattern, $replace, $data);
        }

        require_once 'Horde/Text/Filter.php';
        $strip_style_attributes = (($browser->isBrowser('mozilla') &&
                                    $browser->getMajor() == 4) ||
                                   $browser->isBrowser('msie'));
        $strip_styles = !$attachment || $strip_style_attributes;
        $data = Text_Filter::filter($data, 'xss',
                                    array('body_only' => !$attachment,
                                          'strip_styles' => $strip_styles,
                                          'strip_style_attributes' => $strip_style_attributes));

        /* Check for phishing exploits. */
        if ($this->getConfigParam('phishing_check')) {
            if (preg_match('/href\s*=\s*["\']?\s*(http|https|ftp):\/\/(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?:[^>]*>\s*(?:\\1:\/\/)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[^<]*<\/a)?/i', $data, $m)) {
                /* Check 1: Check for IP address links, but ignore if the link
                 * text has the same IP address. */
                if (!isset($m[3]) || $m[2] != $m[3]) {
                    if (isset($m[3])) {
                        $data = preg_replace('/href\s*=\s*["\']?\s*(http|https|ftp):\/\/' . preg_quote($m[2], '/') . '(?:[^>]*>\s*(?:$1:\/\/)?' . preg_quote($m[3], '/') . '[^<]*<\/a)?/i', 'class="mimeStatusWarning" $0', $data);
                    }
                    $phish_warn = true;
                }
            } elseif (preg_match_all('/href\s*=\s*["\']?\s*(?:http|https|ftp):\/\/([^\s"\'>]+)["\']?[^>]*>\s*(?:(?:http|https|ftp):\/\/)?(.*?)<\/a/is', $data, $m)) {
                /* $m[1] = Link; $m[2] = Target
                 * Check 2: Check for links that point to a different host than
                 * the target url; if target looks like a domain name, check it
                 * against the link. */
                $links = count($m[0]);
                for ($i = 0; $i < $links; $i++) {
                    $link = strtolower(urldecode($m[1][$i]));
                    $target = strtolower(preg_replace('/^(http|https|ftp):\/\//', '', strip_tags($m[2][$i])));
                    if (preg_match('/^[-._\da-z]+\.[a-z]{2,}/i', $target) &&
                        strpos($link, $target) !== 0 &&
                        strpos($target, $link) !== 0) {
                        /* Don't consider the link a phishing link if the
                         * domain is the same on both links (e.g.
                         * adtracking.example.com & www.example.com). */
                        preg_match('/\.?([^\.\/]+\.[^\.\/]+)[\/?]/', $link, $host1);
                        preg_match('/\.?([^\.\/]+\.[^\.\/ ]+)([\/ ].*)?$/s', $target, $host2);
                        if (!(count($host1) && count($host2)) ||
                            strcasecmp($host1[1], $host2[1]) !== 0) {
                            $data = preg_replace('/href\s*=\s*["\']?\s*(?:http|https|ftp):\/\/' . preg_quote($m[1][$i], '/') . '["\']?[^>]*>\s*(?:(?:http|https|ftp):\/\/)?' . preg_quote($m[2][$i], '/') . '<\/a/is', 'class="mimeStatusWarning" $0', $data);
                            $phish_warn = true;
                        }
                    }
                }
            }
        }

        /* Try to derefer all external references. */
        $data = preg_replace_callback('/href\s*=\s*(["\'])?((?(1)[^\1]*?|[^\s>]+))(?(1)\1|)/i',
                                      array($this, '_dereferExternalReferencesCallback'),
                                      $data);

        /* Prepend phishing warning. */
        if ($phish_warn) {
            require_once 'Horde/MIME/Contents.php';
            $contents = new MIME_Contents(new MIME_Part());
            $phish_warning = sprintf(_("%s: This message may not be from whom it claims to be. Beware of following any links in it or of providing the sender with any personal information.") . ' ' . _("The links that caused this warning have the same background color as this message."), _("Warning"));
            if ($contents->viewAsAttachment()) {
                $phish_warning = '<span style="background-color:#ffd0af;color:black">' . String::convertCharset($phish_warning, NLS::getCharset(), $this->mime_part->getCharset()) . '</span><br />';
            }
            $phish_warning = $contents->formatStatusMsg($phish_warning, null, true, 'mimeStatusWarning');
            if (stristr($data, '<body') === false) {
                $data = $phish_warning . $data;
            } else {
                $data = preg_replace('/(.*<body.*?>)(.*)/i', '$1' . $phish_warning . '$2', $data);
            }
        }

        return $data;
    }

    function _dereferExternalReferencesCallback($m)
    {
        return 'href="' . Horde::externalUrl($m[2]) . '"';
    }

    /**
     * Return the content-type of the rendered text.
     *
     * @return string  The MIME Content-Type.
     */
    function getType()
    {
        require_once 'Horde/MIME/Contents.php';
        return MIME_Contents::viewAsAttachment() ? $this->mime_part->getType(true) : 'text/html; charset=' . NLS::getCharset();
    }

}
