#!/bin/sh
#
# Univention Thin Client Sound support
#  postinst script for the debian package
#
# Copyright (C) 2007-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	 02110-1301	 USA

eval $(univention-baseconfig shell univentionSoundEnabled thinclient/sound/daemon thinclient/sound/pulseaudio/resample thinclient/sound/pulseaudio/authentication)

if [ -z "$univentionSoundEnabled" -o "$univentionSoundEnabled" = "0" ]; then
	exit 0
fi

# start sound server (default: arts)
if [ "$thinclient_sound_daemon" = "esd" ]; then
	if test -e "/usr/bin/esd" -a -e "/dev/dsp"; then
		/usr/bin/esd -tcp -public -nobeeps -port 1601 &
		echo "setenv ESPEAKER $HOSTNAME.$(dnsdomainname):1601" >> ~/.univention-thin-client-session
	fi
elif [ "$thinclient_sound_daemon" = "pulseaudio" ]; then

	if [ -z "$thinclient_sound_pulseaudio_resample" ]; then
		resample=trivial
	else
		resample=$thinclient_sound_pulseaudio_resample
	fi

	if [ -z "$thinclient_sound_pulseaudio_authentication" ]; then
		auth="auth-anonymous=1"
	else
		auth=$thinclient_sound_pulseaudio_authentication
	fi

	# pulseaudio config
	alsaConfig=/tmp/${USER}-alsa.conf
	pulseConfig=/tmp/${USER}-pulse.pa
	echo "#!/usr/bin/pulseaudio -nF" > $pulseConfig
	echo "load-module module-native-protocol-tcp $auth" >> $pulseConfig
	echo "load-module module-alsa-sink device=hw:0" >> $pulseConfig
	echo "load-module module-alsa-source device=hw:0" >> $pulseConfig

	pulseaudio -D --resample-method=$resample --high-priority=1 --system -nF $pulseConfig
	
	# new pulse alsa config on terminal server
	echo "run /usr/share/univention-thin-client-sound/univention-thin-client-alsa-config ${USER}" >> ~/.univention-thin-client-session
	
	# alsa and pulse setup
	echo "setenv PULSE_SERVER $HOSTNAME.$(dnsdomainname)" >> ~/.univention-thin-client-session
	echo "setenv ALSA_CONFIG_PATH /tmp/${USER}-tc-alsa.conf" >> ~/.univention-thin-client-session

else
	if test -e "/usr/bin/artswrapper" -a -e "/dev/dsp"; then
		# be sure .mcoprc exists
		if [ ! -e ${HOME}/.mcoprc ]; then
			su - ${USER} -c "echo GlobalComm=Arts::X11GlobalComm > /${HOME}/.mcoprc"
		fi
		#be sure the directory exists, otherwise the artsd on the thinclient isn't able to start
		su - ${USER} -c "mkdir -p \"/tmp/ksocket-${USER}\""
		su - ${USER} -c "DISPLAY=${DISPLAY} /usr/bin/artswrapper -n -F 5 -S 8192 -u -p 1601 &"
		echo "setenv ARTS_SERVER $HOSTNAME.$(dnsdomainname):1601" >> ~/.univention-thin-client-session
	fi
fi

exit 0
