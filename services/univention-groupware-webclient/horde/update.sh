#!/bin/sh -e

export URL="http://ftp.horde.org/pub/snaps/"
export V_year=2007
export V_month=08
export V_day=03
export Branch="HEAD"


export Main_packages="framework gollem  kronolith turba horde imp ingo mnemo nag"
export All_packages="	framework gollem turba horde imp ingo mnemo nag \
						agora ansel chora dimp forwards genie giapeto \
						goops hermes jeta jonah juno klutz luxor \
						merk midas mimp mottle nic occam passwd \
						sam scry sesha skeleton swoosh trean \
						ulaform vacation vilma whups wicked "

for p in $Main_packages; do
	wget ${URL}/${V_year}-${V_month}-${V_day}/${p}-${Branch}-${V_year}-${V_month}-${V_day}.tar.gz
done


