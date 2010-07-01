<?php
/**
 * $Horde: framework/View/lib/Horde/View/Helper/Url.php,v 1.1.2.1 2008-05-22 01:25:36 chuck Exp $
 *
 * @category Horde
 * @package Horde_View
 * @subpackage Helpers
 */

/**
 * View helper for URLs
 *
 * @category Horde
 * @package Horde_View
 * @subpackage Helpers
 */
class Horde_View_Helper_Url extends Horde_View_Helper {

    /**
     * Creates a link tag of the given +name+ using a URL created by the set
     * of +options+. See the valid options in the documentation for
     * url_for. It's also possible to pass a string instead
     * of an options hash to get a link tag that uses the value of the string as the
     * href for the link, or use +:back+ to link to the referrer - a JavaScript back
     * link will be used in place of a referrer if none exists. If nil is passed as
     * a name, the link itself will become the name.
     *
     * ==== Options
     * * <tt>:confirm => 'question?'</tt> -- This will add a JavaScript confirm
     *   prompt with the question specified. If the user accepts, the link is
     *   processed normally, otherwise no action is taken.
     * * <tt>:popup => true || array of window options</tt> -- This will force the
     *   link to open in a popup window. By passing true, a default browser window
     *   will be opened with the URL. You can also specify an array of options
     *   that are passed-thru to JavaScripts window.open method.
     * * <tt>:method => symbol of HTTP verb</tt> -- This modifier will dynamically
     *   create an HTML form and immediately submit the form for processing using
     *   the HTTP verb specified. Useful for having links perform a POST operation
     *   in dangerous actions like deleting a record (which search bots can follow
     *   while spidering your site). Supported verbs are :post, :delete and :put.
     *   Note that if the user has JavaScript disabled, the request will fall back
     *   to using GET. If you are relying on the POST behavior, you should check
     *   for it in your controller's action by using the request object's methods
     *   for post?, delete? or put?.
     * * The +html_options+ will accept a hash of html attributes for the link tag.
     *
     * Note that if the user has JavaScript disabled, the request will fall back
     * to using GET. If :href=>'#' is used and the user has JavaScript disabled
     * clicking the link will have no effect. If you are relying on the POST
     * behavior, your should check for it in your controller's action by using the
     * request object's methods for post?, delete? or put?.
     */
    public function linkTo($name, $url, $htmlOptions = array())
    {
        if ($htmlOptions) {
            $href = isset($htmlOptions['href']) ? $htmlOptions['href'] : null;
            // @todo convert_otpions_to_javascript!(html_options, url)
            $tagOptions = $this->tagOptions($htmlOptions);
        } else {
            $tagOptions = null;
        }

        $hrefAttr = isset($href) ? null : 'href="' . $url . '"';
        $nameOrUrl = isset($name) ? $name : $url;
        return '<a ' . $hrefAttr . $tagOptions . '>' . $this->escape($nameOrUrl) . '</a>';
    }

    /**
     * Creates a link tag of the given $name using $url unless the current
     * request URI is the same as the links, in which case only the name is
     * returned.
     */
    public function linkToUnlessCurrent($name, $url, $htmlOptions = array())
    {
        return $this->linkToUnless($this->isCurrentPage($url),
                                   $name, $url, $htmlOptions);
    }

    /**
     * Creates a link tag of the given +name+ using a URL created by the set of
     * +options+ unless +condition+ is true, in which case only the name is
     * returned. To specialize the default behavior (i.e., show a login link rather
     * than just the plaintext link text), you can pass a block that
     * accepts the name or the full argument list for link_to_unless.
     */
    public function linkToUnless($condition, $name, $url, $htmlOptions = array())
    {
        return $condition ? $name : $this->linkTo($name, $url, $htmlOptions);
    }

    /**
     * Creates a link tag of the given +name+ using a URL created by the set of
     * +options+ if +condition+ is true, in which case only the name is
     * returned. To specialize the default behavior, you can pass a block that
     * accepts the name or the full argument list for link_to_unless (see the examples
     * in link_to_unless).
     */
    public function linkToIf($condition, $name, $url, $htmlOptions = array())
    {
        return $this->linkToUnless(!$condition, $name, $url, $htmlOptions);
    }

    /**
     * True if the current request URI is the same as the current URL.
     *
     * @TODO Get REQUEST_URI from somewhere other than the global environment.
     */
    public function isCurrentPage($url)
    {
        return $url == $_SERVER['REQUEST_URI'];
    }

    // @TODO Move these methods to a generic HTML/Tag helper

    /**
     * HTML attributes that get converted from boolean to the attribute name:
     * array('disabled' => true) becomes array('disabled' => 'disabled')
     *
     * @var array
     */
    private $_booleanAttributes = array('disabled', 'readonly', 'multiple', 'selected', 'checked');

    /**
     * Converts an associative array of $options into
     * a string of HTML attributes
     *
     * @param  array  $options  key/value pairs
     * @param  string           key1="value1" key2="value2"
     */
    public function tagOptions($options)
    {
        foreach ($options as $k => &$v) {
            if ($v === null || $v === false) {
                unset($options[$k]);
            } else {
                if (in_array($k, $this->_booleanAttributes)) {
                    $v = $k;
                }
            }
        }

        if (!empty($options)) {
            foreach ($options as $k => &$v) {
                $v = $k . '="' . $this->escapeOnce($v) . '"';
            }
            sort($options);
            return ' ' . implode(' ', $options);
        } else {
            return '';
        }
    }

    /**
     * Returns the escaped $html without affecting existing escaped entities.
     *
     *   $this->escapeOnce("1 > 2 &amp; 3")
     *     => "1 &lt; 2 &amp; 3"
     *
     * @param  string  $html    HTML to be escaped
     *
     * @return string           Escaped HTML without affecting existing escaped entities
     */
    public function escapeOnce($html)
    {
        return $this->fixDoubleEscape(htmlspecialchars($html, ENT_QUOTES, $this->getEncoding()));
    }

    /**
     * Fix double-escaped entities, such as &amp;amp;
     *
     * @param  string  $escaped  Double-escaped entities
     * @return string            Entities fixed
     */
    private function fixDoubleEscape($escaped)
    {
        return preg_replace('/&amp;([a-z]+|(#\d+));/i', '&\\1;', $escaped);
    }

}
