#!/bin/sh
#
# Copyright 2011-2012 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.
#
# console-data: /usr/share/console/lists/keymaps/console-data.keymaps
# is part of the package console-data, we use it to generate a list
# of default kmaps for a given country (or all kmaps for a given country)

usage () {
	echo "$(basename $0) --layout | --variant LOCALE"
	exit 1
}

cmd="$1"
locale="$2"

if [ -z "$cmd" ]; then
	usage
fi

if [ "$cmd" != "--layout" -a "$cmd" != "--variant" ]; then
	usage
fi

case "$locale" in
    # Keyboards for countries
    *_AL*)
	XKBLAYOUT=al  # Albania
	;;
    *_AZ*)
	XKBLAYOUT=az  # Azerbaijan
	;;
    *_BD*)
	XKBLAYOUT=us,bd  # Bangladesh
	;;
    *_BE*)
	XKBLAYOUT=be  # Belgium
	;;
    *_BG*)
	XKBLAYOUT=us,bg  # Bulgaria
	layout_priority=critical
	;;
    *_BR*)
	XKBLAYOUT=br  # Brazil
	;;
    *_BT*)
	XKBLAYOUT=us,bt  # Bhutan
	;;
    *_BY*)
	XKBLAYOUT=us,by  # Belarus
	;;
    fr_CA*)
	XKBLAYOUT=ca  # Canada
	;;
    *_CA*)
	XKBLAYOUT=us  # U.S. English
	;;
    de_CH*)
	XKBLAYOUT=ch  # Switzerland
	;;
    fr_CH*)
	XKBLAYOUT=ch  # Switzerland
	XKBVARIANT=fr # French
	;;
    *_CH*)
	XKBLAYOUT=ch  # Switzerland
	layout_priority=critical
	;;
    *_CZ*)
	XKBLAYOUT=cz  # Czechia
	layout_priority=critical
	;;
    *_DK*)
	XKBLAYOUT=dk  # Denmark
	;;
    *_EE*)
	XKBLAYOUT=ee  # Estonia
	;;
    ast_ES*)
	XKBLAYOUT=es  # Spain
	XKBVARIANT=ast # Asturian
	;;
    ca_ES*)
	XKBLAYOUT=es  # Spain
	XKBVARIANT=cat # Catalan
	;;
    *_ES*)
	XKBLAYOUT=es  # Spain
	;;
    *_ET*)
	XKBLAYOUT=et  # Ethiopia
	;;
    se_FI*)
	XKBLAYOUT=fi  # Finland
	XKBVARIANT=smi # Northern Saami
	;;
    *_FI*)
	XKBLAYOUT=fi  # Finland
	;;
    *_FR*)
	XKBLAYOUT=fr  # French
	XKBVARIANT=latin9
	;;
    *_GB*)
	XKBLAYOUT=gb  # United Kingdom
	;;
    *_GG*)
	XKBLAYOUT=gb  # United Kingdom
	;;
    *_HU*)
	XKBLAYOUT=hu  # Hungary
	;;
    *_IE*)
	XKBLAYOUT=ie  # Ireland
	;;
    *_IL*)
	XKBLAYOUT=us,il  # Israel
	layout_priority=critical
	;;
    *_IM*)
	XKBLAYOUT=gb  # United Kingdom
	;;
    *_IR*)
	XKBLAYOUT=us,ir  # Iran
	;;
    *_IS*)
	XKBLAYOUT=is  # Iceland
	;;
    *_IT*)
	XKBLAYOUT=it  # Italy
	;;
    *_JE*)
	XKBLAYOUT=gb  # United Kingdom
	;;
    *_JP*)
	XKBLAYOUT=jp  # Japan
	;;
    *_LT*)
	XKBLAYOUT=lt  # Lithuania
	layout_priority=critical
	;;
    *_LV*)
	XKBLAYOUT=lv  # Latvia
	;;
    *_KG*)
	XKBLAYOUT=us,kg  # Kyrgyzstan
	;;
    *_KH*)
	XKBLAYOUT=us,kh  # Cambodia
	;;
    *_KP*)
	XKBLAYOUT=kr  # Korea
	;;
    *_KZ*)
	XKBLAYOUT=us,kz  # Kazakhstan
	;;
    *_LK*)
	XKBLAYOUT=us,lk  # Sri Lanka
	;;
    *_MA*)
	XKBLAYOUT=us,ma  # Morocco
	;;
    *_MK*)
	XKBLAYOUT=us,mk  # Macedonia
	;;
    *_NL*)
	XKBLAYOUT=us  # Netherlands
	;;
    *_MN*)
	XKBLAYOUT=us,mn  # Mongolia
	;;
    *_MT*)
	XKBLAYOUT=mt  # Malta
	layout_priority=critical
	;;
    se_NO*)
	XKBLAYOUT=no  # Norway
	XKBVARIANT=smi # Northern Saami
	;;
    *_NO*)
	XKBLAYOUT=no  # Norway (se_NO is not in this case)
	;;
    *_NP*)
	XKBLAYOUT=us,np  # Nepal
	;;
    *_PL*)
	XKBLAYOUT=pl  # Poland
	;;
    *_PT*)
	XKBLAYOUT=pt  # Portugal
	;;
    *_RO*)
	XKBLAYOUT=ro  # Romania
	;;
    *_RU*)
	XKBLAYOUT=us,ru  # Russia
	layout_priority=critical
	;;
    se_SE*)
	XKBLAYOUT=se  # Sweden
	XKBVARIANT=smi # Northern Saami
	;;
    *_SK*)
	XKBLAYOUT=sk  # Slovakia
	;;
    *_SI*)
	XKBLAYOUT=si  # Slovenia
	;;
    *_TJ*)
	XKBLAYOUT=us,tj  # Tajikistan
	;;
    *_TH*)
	XKBLAYOUT=us,th  # Thailand
	layout_priority=critical
	;;
    *_TR*)
	XKBLAYOUT=tr  # Turkish
	layout_priority=critical
	;;
    *_UA*)
	XKBLAYOUT=us,ua  # Ukraine
	;;
    en_US*)
	XKBLAYOUT=us  # U.S. English
	;;
    *_VN*)
	XKBLAYOUT=vn  # Vietnam
	;;
    *_ZA*)
	XKBLAYOUT=za  # South Africa
	;;
    # Keyboards for specific languages and international keyboards:
    # TODO: Is the following list correct?
    *_AR*|*_BO*|*_CL*|*_CO*|*_CR*|*_DO*|*_EC*|*_GT*|*_HN*|*_MX*|*_NI*|*_PA*|*_PE*|es_PR*|*_PY*|*_SV*|es_US*|*_UY*|*_VE*)
	XKBLAYOUT=latam # Latin American
	;;
    ar_*)
	XKBLAYOUT=us,ara # Arabic
	;;
    bn_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,ben # Bengali
	;;
    bs_*)
	XKBLAYOUT=ba  # Bosnia and Herzegovina
	;;
    de_LI*)
	XKBLAYOUT=ch  # Liechtenstein
	;;
    de_*)
	XKBLAYOUT=de  # Germany
	;;
    el_*)
	XKBLAYOUT=gr  # Greece
	;;
    eo|eo.*|eo_*|eo\@*)
	XKBLAYOUT=epo  # Esperanto
	layout_priority=critical
	;;
    fr_*)
	XKBLAYOUT=fr  # France
	XKBVARIANT=latin9
	layout_priority=critical
	;;
    gu_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,guj # Gujarati
	;;
    hi_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,deva # Devanagari
	;;
    hr_*)
	XKBLAYOUT=hr  # Croatia
	;;
    hy_*)
	XKBLAYOUT=us,am  # Armenia
	;;
    ka_*)
	XKBLAYOUT=us,ge  # Georgia
	layout_priority=critical
	;;
    kn_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,kan # Kannada
	;;
    lo_*)
	XKBLAYOUT=us,la  # Laos
	;;
    ml_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,mal # Malayalam
	;;
    pa_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,guru # Gurmukhi
	;;
    si_*)
	XKBLAYOUT=us,si  # Sri Lanka
	XKBVARIANT=,sin_phonetic # Sinhala
	;;
    sr_*)
	XKBLAYOUT=cs,cs  # Serbia and Montenegro
	XKBVARIANT=latin,basic
	layout_priority=critical
	;;
    sv_*)
	XKBLAYOUT=se  # Sweden
	;;
    ta_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,tam # Tamil
	;;
    te_*)
	XKBLAYOUT=us,in  # India
	XKBVARIANT=,tel # Telugu
	;;
    zh_*)
	XKBLAYOUT=cn  # Chinese
	;;
    # Fallback
    *)
	XKBLAYOUT=us
	;;
esac


if [ "$cmd" = "--variant" ]; then
	echo $XKBVARIANT
elif [ "$cmd" = "--layout" ]; then
	echo $XKBLAYOUT
fi

exit 0
