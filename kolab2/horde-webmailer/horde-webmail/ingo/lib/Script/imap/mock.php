<?php

require_once 'Mail/mimeDecode.php';

class Ingo_Script_imap_mock extends Ingo_Script_imap_api {

    var $_fixtures = array();

    var $_folders = array();

    function loadFixtures($dir)
    {
        $this->_fixtures = array();

        $dh = opendir($dir);
        while (($dent = readdir($dh)) !== false) {
            if ($dent == '.' || $dent == '..') {
                continue;
            }
            $name = $dir . '/' . $dent;
            $fh = fopen($name, 'r');
            $data = fread($fh, filesize($name));
            fclose($fh);

            $params = array('input'          => &$data,
                            'include_bodies' => true,
                            'decode_bodies'  => true,
                            'decode_headers' => true);
            $this->_fixtures[$dent] = Mail_mimeDecode::decode($params);
        }
        closedir($dh);

        $i = 0;
        foreach (array_keys($this->_fixtures) as $key) {
            $this->_folders['INBOX'][] = array('uid'     => ++$i,
                                               'fixture' => $key,
                                               'deleted' => false);
        }
    }

    function hasMessage($fixture, $folder = 'INBOX')
    {
        if (empty($this->_folders[$folder])) {
            return false;
        }
        foreach ($this->_folders[$folder] as $message) {
            if ($message['fixture'] == $fixture) {
                return !$message['deleted'];
            }
        }
        return false;
    }

    function search(&$query)
    {
        $result = array();
        foreach ($this->_folders['INBOX'] as $message) {
            if ($message['deleted']) {
                continue;
            }
            if ($query->matches($this->_fixtures[$message['fixture']])) {
                $result[] = $message['uid'];
            }
        }
        return $result;
    }

    function deleteMessages($sequence)
    {
        $uids = explode(',', $sequence);
        foreach (array_keys($this->_folders['INBOX']) as $i) {
            if (in_array($this->_folders['INBOX'][$i]['uid'], $uids)) {
                $this->_folders['INBOX'][$i]['deleted'] = true;
            }
        }
    }

    function moveMessages($sequence, $folder)
    {
        $uids = explode(',', $sequence);
        foreach (array_keys($this->_folders['INBOX']) as $i) {
            if (in_array($this->_folders['INBOX'][$i]['uid'], $uids)) {
                $this->_folders[$folder][] = $this->_folders['INBOX'][$i];
            }
        }
        return $this->deleteMessages($sequence);
    }

    function expunge($indices)
    {
        foreach (array_keys($this->_folders['INBOX']) as $i) {
            if (in_array($this->_folders['INBOX'][$i]['uid'], $indices)) {
                unset($this->_folders['INBOX'][$i]);
            }
        }

        // Force renumbering
        $this->_folders['INBOX'] = array_merge($this->_folders['INBOX'],
                                               array());
    }

    function fetchMessageOverviews($sequence)
    {
        $result = array();
        foreach (explode(',',$sequence) as $uid) {
            foreach (array_keys($this->_folders['INBOX']) as $i) {
                if ($this->_folders['INBOX'][$i]['uid'] == $uid) {
                    $fixture = $this->_fixtures[$this->_folders['INBOX'][$i]['fixture']];
                    $ob = new stdClass();
                    $ob->from = $fixture->headers['from'];
                    $ob->uid = $uid;
                    $result[] = $ob;
                }
            }
        }
        return $result;
    }

}
