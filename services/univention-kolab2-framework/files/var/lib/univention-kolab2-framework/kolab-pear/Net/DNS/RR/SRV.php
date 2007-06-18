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

/* Net_DNS_RR_SRV definition {{{ */
/**
 * A representation of a resource record of type <b>SRV</b>
 *
 * @package Net_DNS
 */
class Net_DNS_RR_SRV extends Net_DNS_RR
{
    /* class variable definitions {{{ */
    var $name;
    var $type;
    var $class;
    var $ttl;
    var $rdlength;
    var $rdata;
    var $preference;
	var $weight;
	var $port;
    var $target;

    /* }}} */
    /* class constructor - RR(&$rro, $data, $offset = '') {{{ */
    function Net_DNS_RR_SRV(&$rro, $data, $offset = '')
    {
        $this->name = $rro->name;
        $this->type = $rro->type;
        $this->class = $rro->class;
        $this->ttl = $rro->ttl;
        $this->rdlength = $rro->rdlength;
        $this->rdata = $rro->rdata;

        if ($offset) {
            if ($this->rdlength > 0) {
                $a = unpack("@$offset/npreference/nweight/nport", $data);
                $offset += 6;
                list($target, $offset) = Net_DNS_Packet::dn_expand($data, $offset);
                $this->preference = $a['preference'];
                $this->weight = $a['weight'];
                $this->port = $a['port'];
                $this->target = $target;
            }
        } else {
            ereg("([0-9]+)[ \t]+([0-9]+)[ \t]+([0-9]+)[ \t]+(.+)[ \t]*$", $data, $regs);
            $this->preference = $regs[1];
            $this->weight = $regs[2];
            $this->port = $regs[3];
            $this->target = ereg_replace('(.*)\.$', '\\1', $regs[4]);
        }
    }

    /* }}} */
    /* Net_DNS_RR_SRV::rdatastr() {{{ */
    function rdatastr()
    {
        if ($this->port) {
            return(intval($this->preference) . ' ' . intval($this->weight) . ' ' . intval($this->port) . ' ' . $this->target . '.');
        }
        return('; no data');
    }

    /* }}} */
    /* Net_DNS_RR_SRV::rr_rdata($packet, $offset) {{{ */
    function rr_rdata($packet, $offset)
    {
        if ($this->preference) {
            $rdata = pack('nnn', $this->preference, $this->weight, $this->port);
            $rdata .= $packet->dn_comp($this->target, $offset + strlen($rdata));
            return($rdata);
        }
        return(NULL);
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
