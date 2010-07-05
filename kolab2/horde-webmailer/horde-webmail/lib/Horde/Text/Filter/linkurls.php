<?php
/**
 * The Text_Filter_linkurls:: class turns all URLs in the text into hyperlinks.
 *
 * Parameters:
 * <pre>
 * target   -- The link target.  Defaults to _blank.
 * class    -- The CSS class of the generated links.  Defaults to none.
 * nofollow -- Whether to set the 'rel="nofollow"' attribute on links.
 * callback -- An optional callback function that the URL is passed through
 *             before being set as the href attribute.  Must be a string with
 *             the function name, the function must take the original as the
 *             first and only parameter.
 * encode   -- Whether to escape special HTML characters in the URLs and
 *             finally "encode" the complete tag so that it can be decoded
 *             later with the decode() method. This is useful if you want to
 *             run htmlspecialchars() or similar *after* using this filter.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/linkurls.php,v 1.11.10.11 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Tyler Colbert <tyler@colberts.us>
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Text
 */
class Text_Filter_linkurls extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('target' => '_blank',
                         'class' => '',
                         'nofollow' => false,
                         'callback' => null,
                         'encode' => false);

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        $class = $this->_params['class'];
        if (!empty($class)) {
            $class = ' class="' . $class . '"';
        }
        $nofollow = $this->_params['nofollow'] ? ' rel="nofollow"' : '';

        $replacement = $this->_params['callback']
            ? '\' . ' . $this->_params['callback'] . '(\'$0\') . \''
            : '$0';
        if ($this->_params['encode']) {
            $replacement = 'chr(0).chr(0).chr(0).base64_encode(\'<a href="\'.htmlspecialchars(\'' . $replacement . '\').\'"' . $nofollow . ' target="_blank"' . $class . '>\'.htmlspecialchars(\'$0\').\'</a>\').chr(0).chr(0).chr(0)';
        } else {
            $replacement = '\'<a href="' . $replacement . '"' . $nofollow
                . ' target="_blank"' . $class . '>$0</a>\'';
        }

        $regexp = array('|([\w+-]{1,20})://([^\s"<]*[\w+#?/&=])|e' =>
                        $replacement);

        return array('regexp' => $regexp);
    }

    /**
     * "Decodes" the text formerly encoded by using the "encode" parameter.
     *
     * @param string $text  An encoded text.
     *
     * @return string  The decoded text.
     */
    function decode($text)
    {
        return preg_replace('/\00\00\00([\w=+\/]*)\00\00\00/e', 'base64_decode(\'$1\')', $text);
    }

}
