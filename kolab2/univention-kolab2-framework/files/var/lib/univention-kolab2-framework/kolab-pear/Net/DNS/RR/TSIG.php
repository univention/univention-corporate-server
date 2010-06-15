<?php
/*
 *  License Information:
 *
 *    Net_DNS:  A resolver library for PHP
 *    Copyright (c) 2002-2003 Eric Kilfoil eric@ypass.net
 *
 *    This library is free software; you can redistribute it and/or
 *    modify it under the terms of the GNU Lesser General Public
 *    License as published by the Free Software Foundation; either
 *    version 2.1 of the License, or (at your option) any later version.
 *
 *    This library is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *    Lesser General Public License for more details.
 *
 *    You should have received a copy of the GNU Lesser General Public
 *    License along with this library; if not, write to the Free Software
 *    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

define('NET_DNS_DEFAULT_ALGORITHM', 'hmac-md5.sig-alg.reg.int');
define('NET_DNS_DEFAULT_FUDGE', 300);

/* Net_DNS_RR_TSIG definition {{{ */
/**
 * A representation of a resource record of type <b>TSIG</b>
 *
 * @package Net_DNS
 */
class Net_DNS_RR_TSIG extends Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
    var $time_signed;
    var $fudge;
    var $mac_size;
    var $mac;
    var $original_id;
    var $error;
    var $other_len;
    var $other_data;
    var $key;

    /* }}} */
    /* class constructor - RR(&$rro, $data, $offset = '') {{{ */
    function Net_DNS_RR_TSIG(&$rro, $data, $offset = '')
    {
        $this->name = $rro->name;
        $this->type = $rro->type;
        $this->class = $rro->class;
        $this->ttl = $rro->ttl;
        $this->rdlength = $rro->rdlength;
        $this->rdata = $rro->rdata;

        if ($offset) {
            if ($this->rdlength > 0) {
                list($alg, $offset) = Net_DNS_Packet::dn_expand($data, $offset);
                $this->algorithm = $alg;

                $d = unpack("\@$offset/nth/Ntl/nfudge/nmac_size", $data);
                $time_high = $d['th'];
                $time_low = $d['tl'];
                $this->time_signed = $time_low;
                $this->fudge = $d['fudge'];
                $this->mac_size = $d['mac_size'];
                $offset += 10;

                $this->mac = substr($data, $offset, $this->mac_size);
                $offset += $this->mac_size;

                $d = unpack("@$offset/noid/nerror/nolen", $data);
                $this->original_id = $d['oid'];
                $this->error = $d['error'];
                $this->other_len = $d['olen'];
                $offset += 6;

                $odata = substr($data, $offset, $this->other_len);
                $d = unpack('nodata_high/Nodata_low', $odata);
                $this->other_data = $d['odata_low'];
            }
        } else {
            if (strlen($data) && preg_match('/^(.*)$/', $data, $regs)) {
                $this->key = $regs[1];
            }

            $this->algorithm   = NET_DNS_DEFAULT_ALGORITHM;
            $this->time_signed = time();

            $this->fudge       = NET_DNS_DEFAULT_FUDGE;
            $this->mac_size    = 0;
            $this->mac         = '';
            $this->original_id = 0;
            $this->error       = 0;
            $this->other_len   = 0;
            $this->other_data  = '';

            // RFC 2845 Section 2.3
            $this->class = 'ANY';
        }
    }

    /* }}} */
    /* Net_DNS_RR_TSIG::rdatastr() {{{ */
    function rdatastr()
    {
        $error = $this->error;
        if (! $error) {
            $error = 'UNDEFINED';
        }

        if (strlen($this->algorithm)) {
            $rdatastr = $this->algorithm . '. ' . $this->time_signed . ' ' .
                $this->fudge . ' ';
            if ($this->mac_size && strlen($this->mac)) {
                $rdatastr .= ' ' . $this->mac_size . ' ' . base64_encode($this->mac);
            } else {
                $rdatastr .= ' 0 ';
            }
            $rdatastr .= ' ' . $this->original_id . ' ' . $error;
            if ($this->other_len && strlen($this->other_data)) {
                $rdatastr .= ' ' . $this->other_data;
            } else {
                $rdatastr .= ' 0 ';
            }
        } else {
            $rdatastr = '; no data';
        }

        return($rdatastr);
    }

    /* }}} */
    /* Net_DNS_RR_TSIG::rr_rdata($packet, $offset) {{{ */
    function rr_rdata($packet, $offset)
    {
        $rdata = '';
        $sigdata = '';

        if (strlen($this->key)) {
            $key = $this->key;
            $key = ereg_replace(' ', '', $key);
            $key = base64_decode($key);

            $newpacket = $packet;
            $newoffset = $offset;
            array_pop($newpacket->additional);
            $newpacket->header->arcount--;
            $newpacket->compnames = array();

            /*
             * Add the request MAC if present (used to validate responses).
             */
            if (isset($this->request_mac)) {
                $sigdata .= pack('H*', $this->request_mac);
            }
            $sigdata .= $newpacket->data();

            /*
             * Don't compress the record (key) name.
             */
            $tmppacket = new Net_DNS_Packet;
            $sigdata .= $tmppacket->dn_comp(strtolower($this->name), 0);

            $sigdata .= pack('n', Net_DNS::classesbyname(strtoupper($this->class)));
            $sigdata .= pack('N', $this->ttl);

            /*
             * Don't compress the algorithm name.
             */
            $tmppacket->compnames = array();
            $sigdata .= $tmppacket->dn_comp(strtolower($this->algorithm), 0);

            $sigdata .= pack('nN', 0, $this->time_signed);
            $sigdata .= pack('n', $this->fudge);
            $sigdata .= pack('nn', $this->error, $this->other_len);

            if (strlen($this->other_data)) {
                $sigdata .= pack('nN', 0, $this->other_data);
            }

            $this->mac = mhash(MHASH_MD5, $sigdata, $key);
            $this->mac_size = strlen($this->mac);

            /*
             * Don't compress the algorithm name.
             */
            unset($tmppacket);
            $tmppacket = new Net_DNS_Packet;
            $rdata .= $tmppacket->dn_comp(strtolower($this->algorithm), 0);

            $rdata .= pack('nN', 0, $this->time_signed);
            $rdata .= pack('nn', $this->fudge, $this->mac_size);
            $rdata .= $this->mac;

            $rdata .= pack('nnn',$packet->header->id,
                    $this->error,
                    $this->other_len);

            if ($this->other_data) {
                $rdata .= pack('nN', 0, $this->other_data);
            }
        }
        return($rdata);
    }
    /* }}} */
    /* Net_DNS_RR_TSIG::error() {{{ */
    function error()
    {
        if ($this->error != 0) {
            $rcode = Net_DNS::rcodesbyval($error);
        }
        return $rcode;
    }

    /* }}} */
}
/* }}} */
/* VIM settings {{{
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * soft-stop-width: 4
 * c indent on
 * expandtab on
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
