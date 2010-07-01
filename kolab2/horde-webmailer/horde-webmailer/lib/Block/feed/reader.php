<?php
/**
 * $Horde: horde/lib/Block/feed/reader.php,v 1.1.2.2 2008-09-08 16:22:09 chuck Exp $
 *
 * PHP 5 specific code for Horde_Block_Horde_feed segregated in a file
 * that isn't included by default to avoid fatal errors on PHP 4.
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_feed_reader {

    public static function read($uri, $interval)
    {
        require_once 'Horde/Loader.php';

        $key = md5($uri);

        $GLOBALS['cache'] = &Horde_Cache::singleton($GLOBALS['conf']['cache']['driver'],
                                                    Horde::getDriverConfig('cache', $GLOBALS['conf']['cache']['driver']));

        $feed = $GLOBALS['cache']->get($key, $interval);
        if (!empty($feed)) {
            return unserialize($feed);
        }

        try {
            if (!empty($GLOBALS['conf']['http']['proxy']['proxy_host'])) {
                $client = new Horde_Http_Client;
                $client->proxyServer = $GLOBALS['conf']['http']['proxy']['proxy_host'] . ':' . $GLOBALS['conf']['http']['proxy']['proxy_port'];
                if (!empty($GLOBALS['conf']['http']['proxy']['proxy_user'])) {
                    $client->proxyUser = $GLOBALS['conf']['http']['proxy']['proxy_user'];
                    $client->proxyPass = empty($GLOBALS['conf']['http']['proxy']['proxy_pass']) ? $GLOBALS['conf']['http']['proxy']['proxy_pass'] : '';
                }
                Horde_Feed::setHttpClient($client);
            }

            $feed = Horde_Feed::readUri($uri);
            $GLOBALS['cache']->set($key, serialize($feed));
            return $feed;
        } catch (Exception $e) {
            return $e->getMessage();
        }
    }

}
