#!/bin/sed -f
#
# Copyright 2012-2014 Univention GmbH
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
s%dojo\.isString(\([^)]*\))%typeof \1 == "string"%g
s%dojo\.isFunction(\([^)]*\))%typeof \1 == "function"%g
s%dojo\.isObject(\([^)]*\))%typeof \1 == "object"%g
s%dojo\.isArray(\([^)]*\))%\1 instanceof Array%g
s%dojo\.\(clone\|hitch\|mixin\|partial\|replace\|setObject\|getObject\|trim\)\>%lang.\1%g
s%dojo\.\(forEach\|map\|filter\|every\|some\|indexOf\)\>%/*REQUIRE:"dojo/_base/array"*/ array.\1%g
s%dojo\.isIE%/*REQUIRE:"dojo/sniff"*/ has(\'ie\')%g
s%dojo\.addOnLoad%/*REQUIRE:"dojo/ready"*/ ready%g
s%dojo\.ready%/*REQUIRE:"dojo/ready"*/ ready%g
s%dojo\.query%/*REQUIRE:"dojo/query"*/ query%g
s%dojo\.connect(%/*REQUIRE:"dojo/on"*/ /*TODO*/ on(%g
s%this\.connect(%/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(%g
s%dojo\.stopEvent%/*REQUIRE:"dojo/_base/event"*/ event.stop%g
s%dojo\.publish%/*REQUIRE:"dojo/topic"*/ topic.publish%g
s%dojo\.subscribe%/*REQUIRE:"dojo/topic"*/ topic.subscribe%g
s%dojo\.unsubscribe(\([^)]*\))%\1.remove()%g
s%dojo\.byId%/*REQUIRE:"dojo/dom"*/ dom.byId%g
s%dojo\.attr(\([^,]*\),\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-attr"*/ attr.set(\1,\2,\3)%g
s%dojo\.attr(\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-attr"*/ attr.get(\1,\2)%g
s%dojo\.hasAttr%/*REQUIRE:"dojo/dom-attr"*/ attr.has%g
s%dojo\.removeAttr%/*REQUIRE:"dojo/dom-attr"*/ attr.remove%g
s%dojo\.\(add\|remove\|replace\|toggle\)Class%/*REQUIRE:"dojo/dom-class"*/ domClass.\1%g
s%dojo\.hasClass%/*REQUIRE:"dojo/dom-class"*/ domClass.contains%g
s%dojo\.\(create\|destroy\|empty\|place\|toDom\)\>%/*REQUIRE:"dojo/dom-construct"*/ construct.\1%g
s%dojo\.contentBox(\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-geometry"*/ geometry.setContentSize(\1,\2)%g
s%dojo\.contentBox(\([^)]*\))%/*REQUIRE:"dojo/dom-geometry"*/ geometry.getContentBox(\1)%g
s%dojo\.marginBox(\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-geometry"*/ geometry.setMarginBox(\1,\2)%g
s%dojo\.marginBox(\([^)]*\))%/*REQUIRE:"dojo/dom-geometry"*/ geometry.getMarginBox(\1)%g
s%dojo\.position%/*REQUIRE:"dojo/dom-geometry"*/ geometry.position%g
s%dojo\.setContentSize%/*REQUIRE:"dojo/dom-geometry"*/ geometry.setContentSize%g
s%dojo\.style(\([^,]*\),\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-style"*/ style.set(\1,\2,\3)%g
s%dojo\.style(\([^,]*\),\([^)]*\))%/*REQUIRE:"dojo/dom-style"*/ style.get(\1,\2)%g
s%dojo\.\(body\|global\|doc\)\>%/*REQUIRE:"dojo/_base/window"*/ window.\1%g
s%dojo\.fromJson%/*REQUIRE:"dojo/json"*/ json.parse%g
s%dojo\.toJson%/*REQUIRE:"dojo/json"*/ json.stringify%g
s%dojo\.declare(%/*TODO*/ return declare(%g
s%dojo\.fadeIn%/*REQUIRE:"dojo/_base/fx"*/ baseFX.fadeIn%g
s%dojo\.fadeOut%/*REQUIRE:"dojo/_base/fx"*/ baseFX.fadeOut%g
s%dojo\.DeferredList%/*REQUIRE:"dojo/promise/all"*/ all%g
s%dojo\.Deferred%/*REQUIRE:"dojo/Deferred"*/ Deferred%g
s%dojo\.when%/*REQUIRE:"dojo/when"*/ when%g
s%dojo\.xhrPost%/*REQUIRE:"dojo/request"*/ /*TODO*/ request%g
s%dojo\.xhrGet%/*REQUIRE:"dojo/request"*/ /*TODO*/ request%g
s%dojo\.cookie%/*REQUIRE:"dojo/cookie"*/ cookie%g
s%dojo\.date\.locale\.format%/*REQUIRE:"dojo/date/locale"*/ locale.format%g
s%dojo\.date\.locale\.parse%/*REQUIRE:"dojo/date/locale"*/ locale.parse%g
s%this._\>%_%g
s%umc\.\(tools\|dialog\|render\|store\)%\1%g
s%^/\*global.*\<dojo\>.*\*/%/*global define*/%g
