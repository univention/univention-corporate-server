<?php
/**
 * The Text_Filter_emails:: class finds email addresses in a block of text and
 * turns them into links.
 *
 * Parameters:
 * <pre>
 * always_mailto -- If true, a mailto: link is generated always.  Only if no
 *                  mail/compose registry API method exists otherwise.
 * class         -- CSS class of the generated <a> tag.  Defaults to none.
 * encode        -- Whether to escape special HTML characters in the URLs and
 *                  finally "encode" the complete tag so that it can be decoded
 *                  later with the decode() method. This is useful if you want
 *                  to run htmlspecialchars() or similar *after* using this
 *                  filter.
 * </pre>
 *
 * $Horde: framework/Text_Filter/Filter/emails.php,v 1.15.10.21 2009-01-06 15:23:42 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Tyler Colbert <tyler@colberts.us>
 * @author Jan Schneider <jan@horde.org>
 * @package Horde_Text
 */
class Text_Filter_emails extends Text_Filter {

    /**
     * Filter parameters.
     *
     * @var array
     */
    var $_params = array('always_mailto' => false,
                         'class' => '',
                         'encode' => false);

    /**
     * Returns a hash with replace patterns.
     *
     * @return array  Patterns hash.
     */
    function getPatterns()
    {
        global $registry;

        $class = empty($this->_params['class']) ? '' : ' class="' . $this->_params['class'] . '"';

        $regexp = <<<EOR
            /
                # Version 1: mailto: links with any valid email characters.
                # Pattern 1: Outlook parenthesizes in sqare brackets
                (\[\s*)?
                # Pattern 2: mailto: protocol prefix
                (mailto:\s?)
                # Pattern 3: email address
                ([^\s\?"<&]*)
                # Pattern 4: closing angle brackets?
                (&gt;)?
                # Pattern 5 to 7: Optional parameters
                ((\?)([^\s"<]*[\w+#?\/&=]))?
                # Pattern 8: Closing Outlook square bracket
                ((?(1)\s*\]))
            |
                # Version 2 Pattern 9 and 10: simple email addresses.
                (^|\s|&lt;)([\w-+.=]+@[-A-Z0-9.]*[A-Z0-9])
                # Pattern 11 to 13: Optional parameters
                ((\?)([^\s"<]*[\w+#?\/&=]))?
            /eix
EOR;

        if (is_a($registry, 'Registry') &&
            $registry->hasMethod('mail/compose') &&
            !$this->_params['always_mailto']) {
            /* If we have a mail/compose registry method, use it. */
            $replacement = 'Text_Filter_emails::callback(\''
                . $this->_params['encode'] . '\', \'' . $class
                . '\', \'$1\', \'$2\', \'$3\', \'$5\', \'$7\', \'$8\', \'$9\', \'$10\', \'$11\', \'$13\')
                . \'$4\'';
        } else {
            /* Otherwise, generate a standard mailto: and let the browser
             * handle it. */
            if ($this->_params['encode']) {
                $replacement = <<<EOP
                    '$9' === ''
                    ? htmlspecialchars('$1$2') . '<a$class href="mailto:'
                        . htmlspecialchars('$3$5') . '" title="'
                        . sprintf(_("New Message to %s"), htmlspecialchars('$3'))
                        . '">' . htmlspecialchars('$3$5') . '</a>'
                        . htmlspecialchars('$4$8')
                    : htmlspecialchars('$9') . '<a$class href="mailto:'
                        . htmlspecialchars('$10$11') . '" title="'
                        . sprintf(_("New Message to %s"), htmlspecialchars('$10'))
                        . '">' . htmlspecialchars('$10$11') . '</a>'
EOP;
                $replacement = 'chr(1).chr(1).chr(1).base64_encode('
                    . $replacement . ').chr(1).chr(1).chr(1)';
            } else {
                $replacement = <<<EOP
                    '$9' === ''
                    ? '$1$2<a$class href="mailto:$3$5" title="'
                        . sprintf(_("New Message to %s"), htmlspecialchars('$3'))
                        . '">$3$5</a>$4$8'
                    : '$9<a$class href="mailto:$10$11" title="'
                        . sprintf(_("New Message to %s"), htmlspecialchars('$10'))
                        . '">$10$11</a>'
EOP;
            }
        }

        return array('regexp' => array($regexp => $replacement));
    }

    function callback($encode, $class, $bracket1, $protocol, $email,
                      $args_long, $args, $bracket2, $prefix, $email2,
                      $args_long2, $args2)
    {
        if (!empty($email2)) {
            $args = $args2;
            $email = $email2;
            $args_long = $args_long2;
        }

        parse_str($args, $extra);
        $url = $GLOBALS['registry']->call('mail/compose',
                                          array(array('to' => $email),
                                          $extra));
        if (is_a($url, 'PEAR_Error')) {
            $url = 'mailto:' . urlencode($email);
        }

        $url = str_replace('&amp;', '&', $url);
        if (substr($url, 0, 11) == 'javascript:') {
            $href = '#';
            $onclick = ' onclick="' . substr($url, 11) . ';return false;"';
        } else {
            $href = $url;
            $onclick = '';
        }

        if ($encode) {
            return chr(1).chr(1).chr(1)
                . base64_encode(
                    htmlspecialchars($bracket1 . $protocol . $prefix)
                    . '<a' . $class . ' href="' . htmlspecialchars($href)
                    . '" title="' . sprintf(_("New Message to %s"),
                                            htmlspecialchars($email))
                    . '"' . $onclick . '>'
                    . htmlspecialchars($email . $args_long) . '</a>'
                    . htmlspecialchars($bracket2))
                . chr(1).chr(1).chr(1);
        } else {
            return $bracket1 . $protocol . $prefix . '<a' . $class
                . ' href="' . $href . '" title="'
                . sprintf(_("New Message to %s"), htmlspecialchars($email))
                . '"' . $onclick . '>' . htmlspecialchars($email) . $args_long
                . '</a>' . $bracket2;
        }
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
        return preg_replace('/\01\01\01([\w=+\/]*)\01\01\01/e', 'base64_decode(\'$1\')', $text);
    }

}
