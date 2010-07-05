<?php
/**
 * $Horde: framework/NLS/NLS.php,v 1.82.4.26 2009-08-28 09:01:53 jan Exp $
 *
 * @package Horde_NLS
 */

/** String */
require_once 'Horde/String.php';

/**
 * The NLS:: class provides Native Language Support. This includes common
 * methods for handling language detection and selection, timezones, and
 * hostname->country lookups.
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jon Parise <jon@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jan Schneider <jan@horde.org>
 * @author  Michael Slusarz <slusarz@horde.org>
 * @since   Horde 3.0
 * @package Horde_NLS
 */
class NLS {

    /**
     * Selects the most preferred language for the current client session.
     *
     * @return string  The selected language abbreviation.
     */
    function select()
    {
        global $nls, $prefs;

        $lang = Util::getFormData('new_lang');

        /* First, check if language pref is locked and, if so, set it to its
         * value */
        if (isset($prefs) && $prefs->isLocked('language')) {
            $language = $prefs->getValue('language');
        /* Check if the user selected a language from the login screen */
        } elseif (!empty($lang) && NLS::isValid($lang)) {
            $language = $lang;
        /* Check if we have a language set in the session */
        } elseif (isset($_SESSION['horde_language'])) {
            $language = $_SESSION['horde_language'];
        /* Use site-wide default, if one is defined */
        } elseif (!empty($nls['defaults']['language'])) {
            $language = $nls['defaults']['language'];
        /* Try browser-accepted languages. */
        } elseif (!empty($_SERVER['HTTP_ACCEPT_LANGUAGE'])) {
            /* The browser supplies a list, so return the first valid one. */
            $browser_langs = explode(',', $_SERVER['HTTP_ACCEPT_LANGUAGE']);
            foreach ($browser_langs as $lang) {
                /* Strip quality value for language */
                if (($pos = strpos($lang, ';')) !== false) {
                    $lang = substr($lang, 0, $pos);
                }
                $lang = NLS::_map(trim($lang));
                if (NLS::isValid($lang)) {
                    $language = $lang;
                    break;
                }

                /* In case there's no full match, save our best guess. Try
                 * ll_LL, followed by just ll. */
                if (!isset($partial_lang)) {
                    $ll_LL = String::lower(substr($lang, 0, 2)) . '_' . String::upper(substr($lang, 0, 2));
                    if (NLS::isValid($ll_LL)) {
                        $partial_lan = $ll_LL;
                    } else {
                        $ll = NLS::_map(substr($lang, 0, 2));
                        if (NLS::isValid($ll))  {
                            $partial_lang = $ll;
                        }
                    }
                }
            }
        }

        if (!isset($language)) {
            if (isset($partial_lang)) {
                $language = $partial_lang;
            } else {
                /* No dice auto-detecting, default to US English. */
                $language = 'en_US';
            }
        }

        return basename($language);
    }

    /**
     * Sets the language.
     *
     * @param string $lang  The language abbreviation.
     */
    function setLang($lang = null)
    {
        Horde::loadConfiguration('nls.php', null, 'horde');

        if (empty($lang) || !NLS::isValid($lang)) {
            $lang = NLS::select();
        }

        $_SESSION['horde_language'] = $lang;

        if (isset($GLOBALS['language'])) {
            if ($GLOBALS['language'] == $lang) {
                return;
            } else {
                $GLOBALS['registry']->clearCache();
            }
        }
        $GLOBALS['language'] = $lang;

        /* First try language with the current charset. */
        $lang_charset = $lang . '.' . NLS::getCharset();
        if ($lang_charset != setlocale(LC_ALL, $lang_charset)) {
            /* Next try language with its default charset. */
            global $nls;
            $charset = !empty($nls['charsets'][$lang]) ? $nls['charsets'][$lang] : 'ISO-8859-1';
            $lang_charset = $lang . '.' . $charset;
            NLS::_cachedCharset(0, $charset);
            if ($lang_charset != setlocale(LC_ALL, $lang_charset)) {
                /* At last try language solely. */
                $lang_charset = $lang;
                setlocale(LC_ALL, $lang_charset);
            }
        }

        @putenv('LC_ALL=' . $lang_charset);
        @putenv('LANG=' . $lang_charset);
        @putenv('LANGUAGE=' . $lang_charset);
    }

    /**
     * Sets the gettext domain.
     *
     * @param string $app        The application name.
     * @param string $directory  The directory where the application's
     *                           LC_MESSAGES directory resides.
     * @param string $charset    The charset.
     */
    function setTextdomain($app, $directory, $charset)
    {
        bindtextdomain($app, $directory);
        textdomain($app);

        /* The existence of this function depends on the platform. */
        if (function_exists('bind_textdomain_codeset')) {
            NLS::_cachedCharset(0, bind_textdomain_codeset($app, $charset));
        }

        if (!headers_sent()) {
            header('Content-Type: text/html; charset=' . $charset);
        }
    }

    /**
     * Sets the language and reloads the whole NLS environment.
     *
     * When setting the language, the gettext catalogs have to be reloaded
     * too, charsets have to be updated etc. This method takes care of all
     * this.
     *
     * @since Horde 3.2
     *
     * @param string $language  The new language.
     * @param string $app       The application for reloading the gettext
     *                          catalog. The current application if empty.
     */
    function setLanguageEnvironment($language = null, $app = null)
    {
        if (empty($app)) {
            $app = $GLOBALS['registry']->getApp();
        }
        NLS::setLang($language);
        NLS::setTextdomain(
            $app,
            $GLOBALS['registry']->get('fileroot', $app) . '/locale',
            NLS::getCharset());
        String::setDefaultCharset(NLS::getCharset());
    }

    /**
     * Determines whether the supplied language is valid.
     *
     * @param string $language  The abbreviated name of the language.
     *
     * @return boolean  True if the language is valid, false if it's not
     *                  valid or unknown.
     */
    function isValid($language)
    {
        return !empty($GLOBALS['nls']['languages'][$language]);
    }

    /**
     * Maps languages with common two-letter codes (such as nl) to the
     * full gettext code (in this case, nl_NL). Returns the language
     * unmodified if it isn't an alias.
     *
     * @access private
     *
     * @param string $language  The language code to map.
     *
     * @return string  The mapped language code.
     */
    function _map($language)
    {
        $aliases = &$GLOBALS['nls']['aliases'];

        // Translate the $language to get broader matches.
        // (eg. de-DE should match de_DE)
        $trans_lang = str_replace('-', '_', $language);
        $lang_parts = explode('_', $trans_lang);
        $trans_lang = String::lower($lang_parts[0]);
        if (isset($lang_parts[1])) {
            $trans_lang .= '_' . String::upper($lang_parts[1]);
        }

        // See if we get a match for this
        if (!empty($aliases[$trans_lang])) {
            return $aliases[$trans_lang];
        }

        // If we get that far down, the language cannot be found.
        // Return $trans_lang.
        return $trans_lang;
    }

    /**
     * Returns the charset for the current language.
     *
     * @param boolean $original  If true returns the original charset of the
     *                           translation, the actually used one otherwise.
     *
     * @return string  The character set that should be used with the current
     *                 locale settings.
     */
    function getCharset($original = false)
    {
        global $language, $nls;

        /* Get cached results. */
        $cacheKey = intval($original);
        $charset = NLS::_cachedCharset($cacheKey);
        if (!is_null($charset)) {
            return $charset;
        }

        if ($original) {
            $charset = empty($nls['charsets'][$language]) ? 'ISO-8859-1' : $nls['charsets'][$language];
        } else {
            require_once 'Horde/Browser.php';
            $browser = &Browser::singleton();

            if ($browser->hasFeature('utf') &&
                (Util::extensionExists('iconv') ||
                 Util::extensionExists('mbstring'))) {
                $charset = 'UTF-8';
            }
        }

        if (is_null($charset)) {
            $charset = NLS::getExternalCharset();
        }

        NLS::_cachedCharset($cacheKey, $charset);
        return $charset;
    }

    /**
     * Returns the current charset of the environment
     *
     * @return string  The character set that should be used with the current
     *                 locale settings.
     */
    function getExternalCharset()
    {
        global $language, $nls;

        /* Get cached results. */
        $charset = NLS::_cachedCharset(2);
        if (!is_null($charset)) {
            return $charset;
        }

        $lang_charset = setlocale(LC_ALL, 0);
        if (strpos($lang_charset, ';') === false &&
            strpos($lang_charset, '/') === false) {
            $lang_charset = explode('.', $lang_charset);
            if ((count($lang_charset) == 2) && !empty($lang_charset[1])) {
                NLS::_cachedCharset(2, $lang_charset[1]);
                return $lang_charset[1];
            }
        }

        return (!empty($nls['charsets'][$language])) ? $nls['charsets'][$language] : 'ISO-8859-1';
    }

    /**
     * Sets or returns the charset used under certain conditions.
     *
     * @access private
     *
     * @param integer $index   The ID of a cache slot. 0 for the UI charset, 1
     *                         for the translation charset and 2 for the
     *                         external charset.
     * @param string $charset  If specified, this charset will be stored in the
     *                         given cache slot. Otherwise the content of the
     *                         specified cache slot will be returned.
     */
    function _cachedCharset($index, $charset = null)
    {
        static $cache = array();

        if ($charset == null) {
            return isset($cache[$index]) ? $cache[$index] : null;
        } else {
            $cache[$index] = $charset;
        }
    }

    /**
     * Returns the charset to use for outgoing emails.
     *
     * @return string  The preferred charset for outgoing mails based on
     *                 the user's preferences and the current language.
     */
    function getEmailCharset()
    {
        global $prefs, $language, $nls;

        $charset = $prefs->getValue('sending_charset');
        if (!empty($charset)) {
            return $charset;
        }
        return isset($nls['emails'][$language]) ? $nls['emails'][$language] :
               (isset($nls['charsets'][$language]) ? $nls['charsets'][$language] : 'ISO-8859-1');
    }

    /**
     * Check to see if character set is valid for htmlspecialchars() calls.
     *
     * @param string $charset  The character set to check.
     *
     * @return boolean  Is charset valid for the current system?
     */
    function checkCharset($charset)
    {
        static $check;

        if (is_null($charset) || empty($charset)) {
            return false;
        }

        if (isset($check[$charset])) {
            return $check[$charset];
        } elseif (!isset($check)) {
            $check = array();
        }

        $valid = true;

        ini_set('track_errors', 1);
        @htmlspecialchars('', ENT_COMPAT, $charset);
        if (isset($php_errormsg)) {
            $valid = false;
        }
        ini_restore('track_errors');

        $check[$charset] = $valid;

        return $valid;
    }

    /**
     * Sets the charset.
     *
     * In general, the applied charset is automatically determined by browser
     * language and browser capabilities and there's no need to manually call
     * setCharset. However for headless (RPC) operations the charset may be
     * set manually to ensure correct character conversion in the backend.
     *
     * @param string $charset  If specified, this charset will be stored in the
     *                         given cache slot.
     * @param integer $index   The ID of a cache slot. 0 for the UI charset, 1
     *                         for the translation charset and 2 for the
     *                         external charset. Defaults to 0: this is the
     *                         charset returned by getCharset and used for
     *                         conversion.
     */
    function setCharset($charset, $index = 0)
    {
        NLS::_cachedCharset($index, $charset);
    }

    /**
     * Sets the charset and reloads the whole NLS environment.
     *
     * When setting the charset, the gettext catalogs have to be reloaded too,
     * to match the new charset, among other things. This method takes care of
     * all this.
     *
     * @since Horde 3.2
     *
     * @param string $charset  The new charset.
     */
    function setCharsetEnvironment($charset)
    {
        unset($GLOBALS['language']);
        NLS::setCharset($charset);
        NLS::setLang();
        $app = $GLOBALS['registry']->getApp();
        NLS::setTextdomain(
            $app,
            $GLOBALS['registry']->get('fileroot', $app) . '/locale',
            NLS::getCharset());
        String::setDefaultCharset(NLS::getCharset());
    }

    /**
     * Sets the current timezone, if available.
     */
    function setTimeZone()
    {
        global $prefs;

        $tz = $prefs->getValue('timezone');
        if (!empty($tz)) {
            @putenv('TZ=' . $tz);
        }
    }

    /**
     * Get the locale info returned by localeconv(), but cache it, to
     * avoid repeated calls.
     *
     * @return array  The results of localeconv().
     */
    function getLocaleInfo()
    {
        static $lc_info;

        if (!isset($lc_info)) {
            $lc_info = localeconv();
        }

        return $lc_info;
    }

    /**
     * Get the language info returned by nl_langinfo(), but cache it, to
     * avoid repeated calls.
     *
     * @since Horde 3.1
     *
     * @param const $item  The langinfo item to return.
     *
     * @return array  The results of nl_langinfo().
     */
    function getLangInfo($item)
    {
        if (!function_exists('nl_langinfo')) {
            return false;
        }

        static $nl_info = array();

        if (!isset($nl_info[$item])) {
            $nl_info[$item] = nl_langinfo($item);
        }

        return $nl_info[$item];
    }

    /**
     * Get country information from a hostname or IP address.
     *
     * @param string $host  The hostname or IP address.
     *
     * @return mixed  On success, return an array with the following entries:
     *                'code'  =>  Country Code
     *                'name'  =>  Country Name
     *                On failure, return false.
     */
    function getCountryByHost($host)
    {
        /* List of generic domains that we know is not in the country TLD
           list. See: http://www.iana.org/gtld/gtld.htm */
        $generic = array(
            'aero', 'biz', 'com', 'coop', 'edu', 'gov', 'info', 'int', 'mil',
            'museum', 'name', 'net', 'org', 'pro'
        );

        $checkHost = $host;
        if (preg_match('/^\d+\.\d+\.\d+\.\d+$/', $host)) {
            if ((@include_once 'Net/DNS.php')) {
                $resolver = new Net_DNS_Resolver();
                $resolver->retry = isset($GLOBALS['conf']['dns']['retry']) ? $GLOBALS['conf']['dns']['retry'] : 1;
                $resolver->retrans = isset($GLOBALS['conf']['dns']['retrans']) ? $GLOBALS['conf']['dns']['retrans'] : 1;
                if ($response = $resolver->query($host, 'PTR')) {
                    foreach ($response->answer as $val) {
                        if (isset($val->ptrdname)) {
                            $checkHost = $val->ptrdname;
                            break;
                        }
                    }
                }
            } else {
                $checkHost = @gethostbyaddr($host);
            }
        }

        /* Get the TLD of the hostname. */
        $pos = strrpos($checkHost, '.');
        if ($pos === false) {
            return false;
        }
        $domain = String::lower(substr($checkHost, $pos + 1));

        /* Try lookup via TLD first. */
        if (!in_array($domain, $generic)) {
            require 'Horde/NLS/tld.php';
            if (isset($tld[$domain])) {
                return array('code' => $domain, 'name' => $tld[$domain]);
            }
        }

        /* Try GeoIP lookup next. */
        require_once 'Horde/NLS/GeoIP.php';
        $geoip = &NLS_GeoIP::singleton(!empty($GLOBALS['conf']['geoip']['datafile']) ? $GLOBALS['conf']['geoip']['datafile'] : null);
        return $geoip->getCountryInfo($checkHost);
    }

    /**
     * Returns a Horde image link to the country flag.
     *
     * @param string $host  The hostname or IP address.
     *
     * @return string  The image URL, or the empty string on error.
     */
    function generateFlagImageByHost($host)
    {
        global $registry;

        $data = NLS::getCountryByHost($host);
        if ($data !== false) {
            $img = $data['code'] . '.png';
            if (file_exists($registry->get('themesfs', 'horde') . '/graphics/flags/' . $img)) {
                return Horde::img($img, $data['name'], array('title' => $data['name']), $registry->getImageDir('horde') . '/flags');
            } else {
                return '[' . $data['name'] . ']';
            }
        }

        return '';
    }

    /**
     * Returns either a specific or all ISO-3166 country names.
     *
     * @param string $code  The ISO 3166 country code.
     *
     * @return mixed  If a country code has been requested will return the
     *                corresponding country name. If empty will return an
     *                array of all the country codes and their names.
     */
    function getCountryISO($code = '')
    {
        static $countries;
        if (!isset($countries)) {
            include 'Horde/NLS/countries.php';
        }

        if (empty($code)) {
            return $countries;
        }
        if (isset($countries[$code])) {
            return $countries[$code];
        }
        return false;
    }

}
