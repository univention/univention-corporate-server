<?php

require_once 'Horde/String.php';

/**
 * Takes HTML and converts it to formatted, plain text.
 *
 * Parameters:
 * <pre>
 * charset -- The charset to use for html_entity_decode() calls.
 * width   -- The wrapping width.
 * wrap    -- Whether to wrap the text or not.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/html2text.php,v 1.4.10.25 2009-04-02 14:37:19 jan Exp $
 *
 * Copyright 2003-2004 Jon Abernathy <jon@chuggnutt.com>
 * Original source: http://www.chuggnutt.com/html2text.php
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Abernathy <jon@chuggnutt.com>
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.0
 * @package Horde_Text
 */
class Text_Filter_html2text extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('charset' => null,
                         'width' => 70,
                         'wrap' => true);

    /**
     * Executes any code necessaray before applying the filter patterns.
     *
     * @param string $text  The text before the filtering.
     *
     * @return string  The modified text.
     */
    function preProcess($text)
    {
        global $_html2text_state;

        if (is_null($this->_params['charset'])) {
            $this->_params['charset'] = isset($GLOBALS['_HORDE_STRING_CHARSET']) ? $GLOBALS['_HORDE_STRING_CHARSET'] : 'ISO-8859-1';
        }

        $_html2text_state['linkList'] = '';
        $_html2text_state['linkCount'] = 0;

        return trim($text);
    }

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $regexp = array(
            // Non-legal carriage return.
            '/\r/' => '',

            // Leading and trailing whitespace.
            '/^\s*(.*?)\s*$/m' => '\1',

            // Normalize <br>.
            '/<br[^>]*>([^\n]*)\n/i' => "<br>\\1",

            // Newlines and tabs.
            '/[\n\t]+/' => ' ',

            // <script>s -- which strip_tags() supposedly has problems with.
            '/<script[^>]*>.*?<\/script>/i' => '',

            // <style>s -- which strip_tags() supposedly has problems with.
            '/<style[^>]*>.*?<\/style>/i' => '',

            // Comments -- which strip_tags() might have a problem with.
            // //'/<!-- .* -->/' => '',

            // h1 - h3
            '/<h[123][^>]*>(.+?)<\/h[123]> ?/ie' => 'strtoupper("\n\n" . \'\1\' . "\n\n")',

            // h4 - h6
            '/<h[456][^>]*>(.+?)<\/h[456]> ?/ie' => 'ucwords("\n\n" . \'\1\' . "\n\n")',

            // <p>
            '/<p[^>]*> ?/i' => "\n\n",

            // <br>/<div>
            '/<(br|div)[^>]*> ?/i' => "\n",

            // <b>
            '/<b[^>]*>(.+?)<\/b>/ie' => 'strtoupper(\'\1\')',

            // <strong>
            '/<strong[^>]*>(.+?)<\/strong>/ie' => 'strtoupper(\'\1\')',
            '/<span\\s+style="font-weight:\\s*bold.*">(.+?)<\/span>/ie' => 'strtoupper(\'\1\')',

            // <i>
            '/<i[^>]*>(.+?)<\/i>/i' => '/\\1/',

            // <em>
            '/<em[^>]*>(.+?)<\/em>/i' => '/\\1/',

            // <u>
            '/<u[^>]*>(.+?)<\/u>/i' => '_\\1_',

            // <ul>/<ol> and </ul>/</ol>
            '/(<(u|o)l[^>]*>| ?<\/(u|o)l>) ?/i' => "\n\n",

            // <li>
            '/ ?<li[^>]*>/i' => "\n  * ",

            // <a href="">
            '/<a href="([^"]+)"[^>]*>(.+?)<\/a>/ie' => 'Text_Filter_html2text::_buildLinkList($GLOBALS["_html2text_state"]["linkCount"], \'\1\', \'\2\')',

            // <hr>
            '/<hr[^>]*> ?/i' => "\n-------------------------\n",

            // <table> and </table>
            '/(<table[^>]*>| ?<\/table>) ?/i' => "\n\n",

            // <tr>
            '/ ?<tr[^>]*> ?/i' => "\n\t",

            // <td> and </td>
            '/ ?<td[^>]*>(.+?)<\/td> ?/i' => '\1' . "\t\t",
            '/\t\t<\/tr>/i' => '',

            // entities
            '/&nbsp;/i' => ' ',
            '/&trade;/i' => '(tm)',
            '/&#(\d+);/e' => 'String::convertCharset(Text_Filter_html2text::_int2utf8(\'\1\'), "UTF-8", "' . $this->_params['charset'] . '")',

            // Some mailers (e.g. Hotmail) use the following div tag as a way
            // to define a block of text.
            '/<div class=rte>(.+?)<\/div> ?/i' => '\1' . "\n"
        );

        return array('regexp' => $regexp);
    }

    /**
     * Executes any code necessaray after applying the filter
     * patterns.
     *
     * @param string $text  The text after the filtering.
     *
     * @return string  The modified text.
     */
    function postProcess($text)
    {
        global $_html2text_state;

        /* Convert blockquote tags. */
        $text = preg_replace(array('/<blockquote [^>]*(type="?cite"?|class="?gmail_quote"?)[^>]*>\n?/',
                                   '/\n?<\/blockquote>\n?/is'),
                             array(chr(0), chr(1)),
                             $text);
        if (strpos($text, chr(0)) !== false) {
            $text = $this->_blockQuote($text);
        }

        /* Strip any other HTML tags. */
        $text = strip_tags($text);

        /* Convert HTML entities. */
        $trans = array_flip(get_html_translation_table(HTML_ENTITIES));
        $trans = String::convertCharset($trans, 'ISO-8859-1', $this->_params['charset']);
        $text = strtr($text, $trans);

        /* Bring down number of empty lines to 2 max. */
        $text = preg_replace("/\n[[:space:]]+\n/", "\n\n", $text);
        $text = preg_replace("/[\n]{3,}/", "\n\n", $text);

        /* Wrap the text to a readable format. */
        if ($this->_params['wrap']) {
            $text = wordwrap($text, $this->_params['width']);
        }

        /* Add link list. */
        if (!empty($_html2text_state['linkList'])) {
            $text .= "\n\n" . _("Links") . ":\n" .
                str_repeat('-', String::length(_("Links")) + 1) . "\n" .
                $_html2text_state['linkList'];
        }

        return $text;
    }

    /**
     * Replaces blockquote tags with > quotes.
     *
     * @param string $text  The text to quote.
     *
     * @return string  The quoted text.
     */
    function _blockQuote($text)
    {
        return preg_replace(
            '/([^\x00\x01]*)\x00(((?>[^\x00\x01]*)|(?R))*)\x01([^\x00\x01]*)/se',
            "stripslashes('$1') . \"\n\n\" . \$this->_quote('$2') . \"\n\n\" . stripslashes('$4')",
            $text);
    }

    /**
     * Quotes a chunk of text.
     *
     * @param string $text  The text to quote.
     *
     * @return string  The quoted text.
     */
    function _quote($text)
    {
        $text = stripslashes($text);
        if (strpos($text, chr(0)) !== false) {
            $text = stripslashes($this->_blockQuote($text));
        }

        $text = trim(strip_tags($text));
        if ($this->_params['wrap']) {
            $text = wordwrap($text, $this->_params['width'] - 2);
        }

        return preg_replace(array('/^/m', '/(\n>\s*$){3,}/m', '/^>\s+$/m'),
                            array('> ', "\n> ", '>'),
                            $text);
    }

    /**
     * Returns the UTF-8 character sequence of a Unicode value.
     *
     * @param integer $num  A Unicode value.
     *
     * @return string  The UTF-8 string.
     */
    function _int2utf8($num)
    {
        if ($num < 128) {
            return chr($num);
        }
        if ($num < 2048) {
            return chr(($num >> 6) + 192) . chr(($num & 63) + 128);
        }
        if ($num < 65536) {
            return chr(($num >> 12) + 224) . chr((($num >> 6) & 63) + 128) .
                chr(($num & 63) + 128);
        }
        if ($num < 2097152) {
            return chr(($num >> 18) + 240) . chr((($num >> 12) & 63) + 128) .
                chr((($num >> 6) & 63) + 128) . chr(($num & 63) + 128);
        }
        return '';
    }

    /**
     * Helper function called by preg_replace() on link replacement.
     *
     * Maintains an internal list of links to be displayed at the end
     * of the text, with numeric indices to the original point in the
     * text they appeared.
     *
     * @access private
     *
     * @param integer $link_count  Counter tracking current link number.
     * @param string  $link        URL of the link.
     * @param string  $display     Part of the text to associate number with.
     *
     * @return string  The link replacement.
     */
    function _buildLinkList($link_count, $link, $display)
    {
        global $_html2text_state;

        if ($link == strip_tags($display)) {
            return $display;
        }
        $parsed_link = parse_url($link);
        $parsed_display = parse_url(strip_tags(preg_replace('/^&lt;|&gt;$/', '', $display)));
        if (isset($parsed_link['path'])) {
            $parsed_link['path'] = trim($parsed_link['path'], '/');
            if (!strlen($parsed_link['path'])) {
                unset($parsed_link['path']);
            }
        }
        if (isset($parsed_display['path'])) {
            $parsed_display['path'] = trim($parsed_display['path'], '/');
            if (!strlen($parsed_display['path'])) {
                unset($parsed_display['path']);
            }
        }
        if (((!isset($parsed_link['host']) &&
              !isset($parsed_display['host'])) ||
             (isset($parsed_link['host']) &&
              isset($parsed_display['host']) &&
              $parsed_link['host'] == $parsed_display['host'])) &&
            ((!isset($parsed_link['path']) &&
              !isset($parsed_display['path'])) ||
             (isset($parsed_link['path']) &&
              isset($parsed_display['path']) &&
              $parsed_link['path'] == $parsed_display['path']))) {
            return $display;
        }

        $_html2text_state['linkCount']++;
        $_html2text_state['linkList'] .= '[' . $_html2text_state['linkCount'] . "] $link\n";
        return $display . '[' . $_html2text_state['linkCount'] . ']';
    }

}
