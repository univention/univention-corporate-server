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


/* Net_DNS_RR_AAAA object definition {{{ */
/**
 * A representation of a resource record of type <b>AAAA</b>
 *
 * @package Net_DNS
 */
class Net_DNS_RR_AAAA extends Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
    var $address;

    /* }}} */
    /* class constructor - Net_DNS_RR_AAAA(&$rro, $data, $offset = '') {{{ */
    function Net_DNS_RR_AAAA(&$rro, $data, $offset = '')
    {
        $this->name = $rro->name;
        $this->type = $rro->type;
        $this->class = $rro->class;
        $this->ttl = $rro->ttl;
        $this->rdlength = $rro->rdlength;
        $this->rdata = $rro->rdata;

        if ($offset) {
			$this->address = Net_DNS_RR_AAAA::ipv6_decompress(substr($this->rdata, 0, $this->rdlength));
        } else {
            if (strlen($data)) {
                if (count($adata = explode(':', $data, 8)) >= 3) {
                    foreach($adata as $addr)
                        if (!preg_match('/^[0-9A-F]{0,4}$/i', $addr)) return;
                    $this->address = trim($data);
                }
            }
        } 
    }

    /* }}} */
    /* Net_DNS_RR_AAAA::rdatastr() {{{ */
    function rdatastr()
    {
        if (strlen($this->address)) {
            return($this->address);
        }
        return('; no data');
    }
    /* }}} */
    /* Net_DNS_RR_AAAA::rr_rdata($packet, $offset) {{{ */
    function rr_rdata($packet, $offset)
    {
		return Net_DNS_RR_AAAA::ipv6_compress($this->address);
    }

    /* }}} */
    /* Net_DNS_RR_AAAA::ipv6_compress($addr) {{{ */
    function ipv6_compress($addr)
    {
        $numparts = count(explode(':', $addr));
        if ($numparts < 3 || $numparts > 8 ||
            !preg_match('/^([0-9A-F]{0,4}:){0,7}(:[0-9A-F]{0,4}){0,7}$/i', $addr)) {
            /* Non-sensical IPv6 address */
            return pack('n8', 0, 0, 0, 0, 0, 0, 0, 0);
        }
        if (strpos($addr, '::') !== false) {
            /* First we have to normalize the address, turn :: into :0:0:0:0: */
            $filler = str_repeat(':0', 9 - $numparts) . ':';
            if (substr($addr, 0, 2) == '::') {
                $filler = "0$filler";
            }
            if (substr($addr, -2, 2) == '::') {
                $filler .= '0';
            }
            $addr = str_replace('::', $filler, $addr);
        }
        $aparts = explode(':', $addr);
        return pack('n8', hexdec($aparts[0]), hexdec($aparts[1]), hexdec($aparts[2]), hexdec($aparts[3]),
                          hexdec($aparts[4]), hexdec($aparts[5]), hexdec($aparts[6]), hexdec($aparts[7]));
    }
    /* }}} */

    /* Net_DNS_RR_AAAA::ipv6_decompress($pack) {{{ */
    function ipv6_decompress($pack)
    {
        if (strlen($pack) != 16) {
            /* Must be 8 shorts long */
            return '::';
        }
        $a = unpack('n8b', $pack);
        foreach($a as $idx => $value)
            $a[$idx] = dechex($value);
        $addr = implode(':', $a);
        /* Shorthand the first :0:0:0: set into a :: */
        /* TODO: Make this is a single replacement pattern */
        if (substr($addr, -4, 4) == ':0:0') {
            return preg_replace('/((:0){2,})$/', '::', $addr);
        } else {
            return preg_replace('/(:?(0:){2,})/', '::', $addr);
        }
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
 * End:
 * vim600: sw=4 ts=4 sts=4 cindent fdm=marker et
 * vim<600: sw=4 ts=4
 * }}} */
?>
