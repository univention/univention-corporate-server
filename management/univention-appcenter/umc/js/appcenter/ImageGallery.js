/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2020-2022 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/Deferred",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/tools",
	"umc/widgets/Button",
	"umc/widgets/Icon",
	"put-selector/put",
	"umc/i18n!umc/modules/appcenter",
], function(declare, lang, on, Deferred, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, tools, Button, Icon, put, _) {
	return declare("umc.modules.appcenter.ImageGallery", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		//// overwrites
		baseClass: 'imageGallery',

		templateString: `
			<div>
				<div class="imageGallery__aspectRatio">
					<div data-dojo-attach-point="viewportNode" class="imageGallery__viewport">
						<div
							data-dojo-attach-point="carouselNode"
							class="imageGallery__carousel"
						></div>
					</div>
				</div>
				<div data-dojo-attach-point="dotsWrapper" class="imageGallery__dotsWrapper dijitDisplayNone">
					<div data-dojo-attach-point="dotsNode" class="imageGallery__dots">
						<div class="imageGallery__dot imageGallery__dot--reticle"></div>
					</div>
				</div>
			</div>
		`,


		//// self
		carouselIdx: 0,
		_setCarouselIdxAttr: function(carouselIdx) {
			const maxIdx = this._items.length - 1;
			if (carouselIdx < 0) {
				carouselIdx = maxIdx;
			}
			if (carouselIdx > maxIdx) {
				carouselIdx = 0;
			}
			this.domNode.style.setProperty('--local-idx', carouselIdx);
			if (carouselIdx !== this.carouselIdx) {
				this.pauseAllVideos();
			}
			this._set('carouselIdx', carouselIdx);
		},
		navLeft: function() {
			this.set('carouselIdx', this.carouselIdx - 1);
		},
		navRight: function() {
			this.set('carouselIdx', this.carouselIdx + 1);
		},

		srcs: null,
		_items: null,
		_ytAPILoaded: null,
		_ytPlayers: null,

		_srcIsYoutubeVideo: function(src) {
			//taken from http://stackoverflow.com/questions/28735459/how-to-validate-youtube-url-in-client-side-in-text-box
			var p = /^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$/;
			if(src.match(p)){
				return true;
			}
			return false;
		},
		_getYoutubeUrlVideoId: function(src) {
			var p = /^(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$/;
			return src.match(p)[1];
		},
		_renderYoutubeVideo: function(videoNode) {
			var playerReady = evt => {
				evt.target.playVideo();
				this._ytPlayers.push(evt.target);
			};

			this._ytAPILoaded.then(() => {
				var videoId = videoNode.id;
				var player = new YT.Player(videoId, {
					videoId: videoId,
					events: {
						'onReady': playerReady
					}

				});
				this.own(player);
			});
		},
		pauseAllVideos: function() {
			for (let player of this._ytPlayers) {
				player.pauseVideo();
			}
		},


		//// lifecycle
		constructor: function() {
			this.srcs = [];
			this._ytPlayers = [];
		},

		postMixInProperties: function() {
			this.inherited(arguments);

			// make items from this.srcs
			const uniqueYTVideoIds = [];
			const items = [];
			for (let src of this.srcs) {
				if (this._srcIsYoutubeVideo(src)) {
					const videoId = this._getYoutubeUrlVideoId(src);
					if (!uniqueYTVideoIds.includes(videoId)) {
						uniqueYTVideoIds.push(videoId);
						items.push({type: 'video', videoId: videoId});
					}
				} else {
					items.push({type: 'img', src: src});
				}
			}
			this._items = items;
		},

		buildRendering: function() {
			this.inherited(arguments);
			for (const item of this._items) {
				if (item.type === 'video') {
					const videoId = item.videoId;

					//get the thumbnail for the youtube video via the unique id
					const ytVideoThumbnailURL = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;

					const wrapper = put(this.carouselNode, 'div.imageGallery__carouselItem');

					const videoNode = put(wrapper, `div#${videoId}.imageGallery__carouselVideo__video.dijitDisplayNone`);

					const thumbnail = put(wrapper, `img[src=${ytVideoThumbnailURL}]`);
					const playButton = new Button({
						iconClass: 'play',
						class: 'ucsIconButton imageGallery__navButton imageGallery__carouselVideo__playButton',
						onClick: () => {
							tools.toggleVisibility(thumbnail, false);
							tools.toggleVisibility(playButton, false);
							tools.toggleVisibility(videoNode, true);
							this._renderYoutubeVideo(videoNode);
						}
					});
					this.own(playButton);
					put(wrapper, playButton.domNode);
				} else if (item.type === 'img') {
					put(this.carouselNode, `div.imageGallery__carouselItem img[src=${item.src}]`);
				}
			}

			if (this._items.length >= 2) {
				tools.toggleVisibility(this.dotsWrapper, true);
				for (let x = 0; x < this._items.length; x++) {
					const dot = put(this.dotsNode, 'div.imageGallery__dot');
					on(dot, 'click', () => {
						this.set('carouselIdx', x);
					});
				}

				const navLeft = new Button({
					iconClass: 'chevron-left',
					class: 'ucsIconButton imageGallery__navButton imageGallery__navButton--left',
					onClick: lang.hitch(this, 'navLeft'),
				});
				const navRight = new Button({
					iconClass: 'chevron-right',
					class: 'ucsIconButton imageGallery__navButton imageGallery__navButton--right',
					onClick: lang.hitch(this, 'navRight'),
				});
				this.own(navLeft);
				this.own(navRight);
				put(this.viewportNode, navLeft.domNode);
				put(this.viewportNode, navRight.domNode);
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			// load YT API if not already loaded
			this._ytAPILoaded = new Deferred();
			if (window.YT && window.YT.loaded) {
				this._ytAPILoaded.resolve();
			} else {
				//load youtube iframe api
				var tag = document.createElement('script');
				tag.src = "https://www.youtube.com/iframe_api";
				var firstScriptTag = document.getElementsByTagName('script')[0];
				firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
				window.onYouTubeIframeAPIReady = () => {
					this._ytAPILoaded.resolve();
				}
			}
		}
	});
});

