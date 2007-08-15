# -*- coding: utf-8 -*-
#
# Univention Mail Cyrus Kolab2
#  listener module: create sieve scripts with rules for kolab and spam
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import listener
import os, time, string, pwd, grp, univention.debug, sys

name='cyrus-sieve'
description='Create sieve mail filters'
filter='(|(objectClass=kolabInetOrgPerson)(objectClass=univentionMail))'

def handler(dn, new, old):
	if not new and old:
		if old.has_key('mailPrimaryAddress') and old['mailPrimaryAddress'][0] and old['mailPrimaryAddress'][0].lower() != listener.baseConfig['mail/antispam/globalfolder'].lower():
			if old.has_key( 'univentionKolabDisableSieve' ) and old[ 'univentionKolabDisableSieve' ][0].lower( ) in [ 'true', 'yes' ]:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'Do not not remove the sieve script for user: %s' % old['mailPrimaryAddress'][0])
				return
			try:
				user_name = old['mailPrimaryAddress'][0]
				userpart=user_name.split('@')[0]
				userpart=string.lower(userpart)
				userpart=userpart.replace(".", "^")
				domainpart=user_name.split('@')[1]
				domainpart=string.lower(domainpart)
				sieve_path = '/var/spool/cyrus/sieve/domain/%s/%s/%s/%s' % (domainpart[0], domainpart, userpart[0], userpart)
				listener.setuid(0)
				if os.path.exists(sieve_path):
					os.remove(sieve_path)
				listener.unsetuid()
			except:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not remove Sieve-Script from User: %s' % user_name)
	else:
		if new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0] and new['mailPrimaryAddress'][0].lower() != listener.baseConfig['mail/antispam/globalfolder'].lower():

			if new.has_key( 'univentionKolabDisableSieve' ) and new[ 'univentionKolabDisableSieve' ][0].lower( ) in [ 'true', 'yes' ]:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'Do not not write a  sieve script for user: %s' % new['mailPrimaryAddress'][0])
				return

			cyrus_id=pwd.getpwnam('cyrus')[2]
			mail_id=grp.getgrnam('mail')[2]

			user_name = new['mailPrimaryAddress'][0]
			userpart=user_name.split('@')[0]
			userpart=string.lower(userpart)
			userpart=userpart.replace(".", "^")
			domainpart=user_name.split('@')[1]
			domainpart=string.lower(domainpart)

			univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'User: %s' % user_name)

			sieve_path = '/var/spool/cyrus/sieve/domain/%s/%s/%s/%s/sieve.siv' % (domainpart[0], domainpart, userpart[0], userpart)

			## Standard elements
			sc_header='# Univention Sieve Script - generated on %s' %time.asctime(time.localtime())
			#require list
			sc_require='require ["fileinto", "vacation"];'
			sc_require_simple='require ["fileinto"];'
			#carriage return
			sc_cr='\n'
			sc_stop='stop;'
			sc_end='}'
			sc_else='} else {'
			#regular delivery
			try:
				if new.has_key('univentionKolabDeliveryToFolderActive') and new['univentionKolabDeliveryToFolderActive'][0] == 'TRUE':
					univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DeliveryToFolderActive: %s' %new['univentionKolabDeliveryToFolderActive'][0])
					if new.has_key('univentionKolabDeliveryToFolderName') and new['univentionKolabDeliveryToFolderName'][0]:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'DeliveryToFolderName: %s' %new['univentionKolabDeliveryToFolderName'][0])
						sc_deliver='fileinto "INBOX/%s";' %new['univentionKolabDeliveryToFolderName'][0]
					else:
						sc_deliver='keep;'
				else:
					sc_deliver='keep;'
			except:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not set deliver method')
			#/regular delivery


			##FIXME: Kolab scheduling information
			#for some reason, the check only appears in kolab script example
			#for regular delivery. Might be worth beeing kept in mind if problems occur.
			#sc_kolsched='if not header :contains ["X-Kolab-Scheduling-Message"] ["FALSE"] {'


			## Spam-Rules
			sc_spamline='if header :matches "X-Spam-Status" "Yes,*" {'
			#global spam folder
			if listener.baseConfig.has_key('mail/antispam/globalfolder'):
				sc_spamglo='redirect "%s";' %(listener.baseConfig['mail/antispam/globalfolder'])
			else:
				sc_spamglo=''
			#local spam folder
			sc_spamloc='fileinto "INBOX/Spam";'
			#Forward Spam?
			sc_spamfwd=''


			#forwarding
			sc_forward=''
			try:
				if new.has_key('univentionKolabForwardActive') and new['univentionKolabForwardActive'][0] == 'TRUE':
					if new.has_key('kolabForwardAddress') and new['kolabForwardAddress'][0]:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabForwardAddress: %s' %new['kolabForwardAddress'][0])
						sc_forward+='redirect "%s";' %new['kolabForwardAddress'][0]
						if new.has_key('kolabForwardKeepCopy') and new['kolabForwardKeepCopy'][0] == 'TRUE':
							univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabForwardKeepCopy')
							#Keeping copy in sc_deliver
							sc_forward+='\n'
							sc_forward+=sc_deliver
						#Forward Spam to?
						if new.has_key('kolabForwardUCE') and new['kolabForwardUCE'][0] == 'TRUE':
							univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabForwardUCE')
							sc_spamfwd='redirect "%s";' %new['kolabForwardAddress'][0]
			except:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not set forwarding method')
			#/forwarding

			#Vacation
			try:
				#Vacation in use?
				sc_vacinuse='0'
				#Vacation to Spam?
				sc_vactospam='0'
				#Vacation Address
				sc_vacaddr=[]
				#React domains
				sc_vacreactdom=[]
				#Non-react domains
				sc_vacnoreactdom=[]
				#Resend intervall
				sc_vacresend=''
				#Text
				sc_vactext=''

				#Line for react domains
				sc_reactline=''
				#Line for non-react domains
				sc_noreactline=''
				#Vacation Line (followed by sc_vactext)
				sc_vacline=''

				if new.has_key('univentionKolabVacationActive') and new['univentionKolabVacationActive'][0] == 'TRUE':
					sc_vacinuse='1'
					univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'univentionKolabVacationActive')

					if new.has_key('kolabVacationReplyToUCE') and new['kolabVacationReplyToUCE'][0] == 'TRUE':
						sc_vactospam='1'
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabVacationReplyToUCE')
					if new.has_key('kolabVacationResendInterval') and new['kolabVacationResendInterval'][0]:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabVacationResendInterval: %s' %new['kolabVacationResendInterval'][0])
						sc_vacresend=new['kolabVacationResendInterval'][0]
					#VACATIONADDR
					if new.has_key('kolabVacationAddress') and new['kolabVacationAddress'][0]:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabVacationAddress: %s' %new['kolabVacationAddress'])
						for addr in new['kolabVacationAddress']:
							sc_vacaddr.append(addr)
						i=0
						alladdr=''
						while i < len(sc_vacaddr):
							if i == len(sc_vacaddr)-1:
								alladdr+='"%s"'%sc_vacaddr[i]
							else:
								alladdr+='"%s", ' %sc_vacaddr[i]
							i+=1
					#If no kolabVacationAddress is set use the primary mail address and all alternative addresses
					elif new.has_key('mailPrimaryAddress') and new['mailPrimaryAddress'][0]:
						alladdr=''
						if new.has_key('mailAlternativeAddress') and new['mailAlternativeAddress'][0]:
							alladdr+='"%s", ' %new['mailPrimaryAddress'][0]
							altaddr=[]
							for addr in new['mailAlternativeAddress']:
								altaddr.append(addr)
							i=0
							while i < len(altaddr):
								if i == len(altaddr)-1:
									alladdr+='"%s"' %altaddr[i]
								else:
									alladdr+='"%s", ' %altaddr[i]
								i+=1
						else:
							alladdr+='"%s"' %new['mailPrimaryAddress'][0]
					else:
						return 1
						univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not write vacation. No kolabVacationAddress and/or mailPrimaryAddress set!')
					if sc_vacresend == '0' or sc_vacresend == '':
						sc_vacline='vacation :addresses [ %s ] text:' %alladdr
					else:
						sc_vacline='vacation :addresses [ %s ] :days %s text:' %(alladdr, sc_vacresend)
					univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'Vacation: %s' %sc_vacline)
					#/VACATIONADDR
					if new.has_key('univentionKolabVacationText') and new['univentionKolabVacationText'][0]:
						sc_vactext=new['univentionKolabVacationText'][0]
						sc_vactext+='\n.\n;'
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'univentionKolabVacationText: %s' %new['univentionKolabVacationText'][0])

					if new.has_key('kolabVacationReactDomain') and new['kolabVacationReactDomain'][0]:
						for dom in new['kolabVacationReactDomain']:
							sc_vacreactdom.append(dom)
						for dom in sc_vacreactdom:
							sc_reactline+='if not address :domain :contains "From" "%s" { stop; }\n' %dom
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'kolabVacationReactDomain: %s' %sc_reactline)

					if new.has_key('univentionKolabVacationNoReactDomain') and new['univentionKolabVacationNoReactDomain'][0]:
						for dom in new['univentionKolabVacationNoReactDomain']:
							sc_vacnoreactdom.append(dom)
						for dom in sc_vacnoreactdom:
							sc_noreactline+='if address :domain :contains "From" "%s" { stop; }\n' %dom
						univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO, 'univentionKolabVacationNoReactDomain: %s' %sc_noreactline)
			except:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not set Vacation')
			#/Vacation

			#Build the script in one string
			class sievescr:
				def __init__(self):
					self.thescript=''

				def append(self, line):
					self.thescript+='%s\n' %line

				def write(self, where):
					listener.setuid(0)
					try:
						scr=open(where, 'w')
						scr.write(self.thescript)
						scr.close()

						where_default=where.replace('sieve.siv', 'defaultbc')
						os.system('/usr/lib/cyrus/bin/sievec %s %s' % (where, where_default))
						os.chown(os.path.dirname(where), cyrus_id, mail_id)
						os.chown(where, cyrus_id, mail_id)
						os.chown(where_default, cyrus_id, mail_id)
					except:
						univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not write Sieve-Script to: %s' %where)
					listener.unsetuid()


			def writevacation(sieve_script, sc_reactline, sc_noreactline, sc_vacline, sc_vactext):
				if sc_reactline != '':
					sieve_script.append(sc_reactline)
				if sc_noreactline != '':
					sieve_script.append(sc_noreactline)
				sieve_script.append(sc_vacline)
				sieve_script.append(sc_vactext)


			try:
				fqdn = '%s.%s' % (listener.baseConfig['hostname'], listener.baseConfig['domainname'])
				if new.has_key('kolabHomeServer') and new['kolabHomeServer'][0] == fqdn:

					#Complete Script as a string
					sieve_script=sievescr()
					sieve_script.append(sc_header)
					sieve_script.append(sc_require)
					sieve_script.append(sc_cr)

					## Spam handling
					sieve_script.append(sc_spamline)

					#kobalForwardUCE
					if sc_spamfwd != '':
						sieve_script.append(sc_spamfwd)

					if new.has_key('mailGlobalSpamFolder') and new['mailGlobalSpamFolder'][0] == '1':
						sieve_script.append(sc_spamglo)
					else:
						sieve_script.append(sc_spamloc)

					#Reply to spam with vacation msg?
					if sc_vacinuse == '1' and sc_vactospam == '1':
						writevacation(sieve_script, sc_reactline, sc_noreactline, sc_vacline, sc_vactext)

					sieve_script.append(sc_stop)
					sieve_script.append(sc_end)
					## /Spam handling

					sieve_script.append('if header :contains ["X-Kolab-Scheduling-Message"] ["TRUE"] { stop; }')

					#sieve_script.append(sc_kolshed)
					#sieve_script.append(sc_else)

					#Forward or just deliver?
					if new.has_key('univentionKolabForwardActive') and new['univentionKolabForwardActive'][0] == 'TRUE':
						sieve_script.append(sc_forward)
					else:
						sieve_script.append(sc_deliver)

					## Vacation
					if sc_vacinuse == '1':
						writevacation(sieve_script, sc_reactline, sc_noreactline, sc_vacline, sc_vactext)
					## /Vacation

					#depends on sc_kolshed
					#sieve_script.append(end)

					sieve_script.write(sieve_path)
					#sieve_script.write('/tmp/sieve^')

				elif not new.has_key('kolabHomeServer'):
					#Complete Script as a string
					sieve_script=sievescr()
					sieve_script.append(sc_header)
					sieve_script.append(sc_require_simple)
					sieve_script.append(sc_cr)

					# Spam handling
					sieve_script.append(sc_spamline)
					if new.has_key('mailGlobalSpamFolder') and new['mailGlobalSpamFolder'][0] == '1':
						sieve_script.append(sc_spamglo)
					else:
						sieve_script.append(sc_spamloc)
					sieve_script.append(sc_stop)
					sieve_script.append(sc_end)
					## /Spam handling

					sieve_script.append(sc_deliver)
					sieve_script.write(sieve_path)

			except:
				univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Could not create Sieve-Script.')
