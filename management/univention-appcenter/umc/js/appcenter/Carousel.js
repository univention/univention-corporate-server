/*
 * Copyright 2011-2015 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global define,console,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/window",
	"dojo/on",
	"dojo/query",
	"dojo/dom-construct",
	"dojo/dom-style",
	"dojo/dom-geometry",
	"dojo/dom-class",
	"dojox/html/styles",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_RegisterOnShowMixin",
	"dojo/domReady!"
], function(declare, array, lang, kernel, baseWin, on, query, domConstruct, domStyle, domGeometry, domClass, styles, tools, ContainerWidget, _RegisterOnShowMixin) {
	return declare("umc.modules.appcenter.Carousel_new", [ContainerWidget, _RegisterOnShowMixin], {
		baseClass: 'umcCarouselWidget',

		outerContainer: null,
		contentSlider: null,
		contentSliderOffset: null,

		shownItemIndex: null,

		itemHeight: null,
		heighestImg: null,

		// items: Array
		//     array of objects({src: <src-string>})
		//     where <src-string> is either an image or a youtube video url 
		items: null,
		itemNodes: null,

		allItemsLoaded: null,

		bigThumbnails: null,

		_resizeDeferred: null,

		postMixInProperties: function() {
			this.itemHeight = this.itemHeight || 200;
			this.itemNodes = [];
			this.contentSliderOffset = 0;
			this.shownItemIndex = 0;
			this.allItemsLoaded = false;
			this.bigThumbnails = false;
		},

		buildRendering: function() {
			this.inherited(arguments);

			this.outerContainer = new ContainerWidget({
				'class': 'carouselOuterContainer'
			});

			this.addChild(this.outerContainer);
			this.own(this.outerContainer);

			this.renderContentSlider();
			this.renderNavButtons();
			this.renderScaleButton();
			
		},

		postCreate: function() {
			if (window.YT && window.YT.loaded) {
				setTimeout(lang.hitch(this, function() {
					this._renderYoutubeVideos();
				}), 500);
			} else {
				//load youtube api
				var tag = document.createElement('script');
				tag = domConstruct.create('script', {
					id: "youtubeAPI",
					src: "https://www.youtube.com/iframe_api"
				});
				var firstScriptTag = document.getElementsByTagName('script')[0];
				firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

				window.onYouTubeIframeAPIReady = lang.hitch(this, function() {
					this._renderYoutubeVideos();
				});
			}
			onPlayerReady = lang.hitch(this, function() {
				this.imagesLoaded();
			});
		},

		renderContentSlider: function() {
			this.contentSliderWrapper = new ContainerWidget({
				'class': 'contentSliderWrapper'
			});
			this.contentSlider = new ContainerWidget({
				'class': 'contentSlider'
			});
			this.contentSliderWrapper.addChild(this.contentSlider);
			this.outerContainer.addChild(this.contentSliderWrapper);

			this._renderThumbs();
		},

		_renderThumbs: function() {
			this.loadedImagesCount = 0;
			var index = 0;

			array.forEach(this.items, lang.hitch(this, function(item) {
				if (this._srcIsYoutubeVideo(item.src)) {
					var videoId = this._getYoutubeUrlVideoId(item.src);

					var videoWrapper = domConstruct.create('div', {'class': 'galleryVideo'}, this.contentSlider.domNode);
					var div = domConstruct.create('div', {
						id: videoId
					}, videoWrapper);

					this.itemNodes.push(videoWrapper);
				} else {
					var imgWrapper = domConstruct.create('div', {}, this.contentSlider.domNode);
					var img = domConstruct.create('img', {
						src: item.src,
						index: index,
						'class': 'carouselScreenshot',
						onload: lang.hitch(this, function() {
							this._updateHeighestImage(img);
							this.imagesLoaded();
						}),
						onclick: lang.hitch(this, function(evt) {
							this.togglePreviewSize(parseInt(evt.target.getAttribute('index')));
						})
					}, imgWrapper);
					this.itemNodes.push(imgWrapper);
				}
				index++;
			}));
		},

		_renderYoutubeVideos: function() {
			query('.galleryVideo', this.contentSlider.domNode).forEach(lang.hitch(this, function(videoWrapper) {
				var player;
				var videoId = videoWrapper.firstChild.id;
				player = new YT.Player(videoId, {
					height: this.itemHeight.toString(),
					width: 'auto',
					videoId: videoId,
					events: {
						'onReady': onPlayerReady
					}
				});
				this.own(player);
			}));
		},

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
		
		_setDefaultThumbsHeight: function() {
			if (!styles.getStyleSheet('defaultItemHeightImage')) {
				styles.insertCssRule('.contentSlider .carouselScreenshot', lang.replace('max-height: {0}px', [this.itemHeight]), 'defaultItemHeightImage');
			}
			if (!styles.getStyleSheet('defaultItemHeightWrapper')) {
				styles.insertCssRule('.contentSlider div', lang.replace('height: {0}px', [this.itemHeight]), 'defaultItemHeightWrapper');
			}
		},

		renderNavButtons: function() {
			this.leftButton = domConstruct.create('div', {
				'class': 'carouselButton leftCarouselButton',
				onclick: lang.hitch(this, function() {
					this.showItem(this.shownItemIndex - 1);
				})
			}, this.contentSliderWrapper.domNode, 'before');
			domConstruct.create('div', {
				'class': 'carouselButtonImage'
			}, this.leftButton);

			this.rightButton = domConstruct.create('div', {
				'class': 'carouselButton rightCarouselButton',
				onclick: lang.hitch(this, function() {
					this.showItem(this.shownItemIndex + 1);
				})
			}, this.contentSliderWrapper.domNode, 'after');
			domConstruct.create('div', {
				'class': 'carouselButtonImage'
			}, this.rightButton);
		},

		renderScaleButton: function() {
			this.scaleButton = domConstruct.create('div', {
				'class': 'scaleButton',
				onclick: lang.hitch(this, function() {
					this.togglePreviewSize(this.shownItemIndex);
				})
			}, this.domNode);
		},

		imagesLoaded: function() {
			this.loadedImagesCount++;
			if (this.loadedImagesCount === this.items.length) {
				this.allItemsLoaded = true;
				this.heighestImg = this.heighestImg.cloneNode();
				domConstruct.place(this.heighestImg, this.domNode);
				domClass.add(this.heighestImg, 'dijitHidden');
				
				this._setDefaultThumbsHeight();
				this.resizeCarousel();
				this.calcDefaultSliderWidth();
				this.calcOffsets();
			}
		},

		_updateHeighestImage: function(img) {
			if (!this.heighestImg) {
				this.heighestImg = img;
			}
			if ((img.height > img.width) && (img.height > this.heighestImg.height)) {
				this.heighestImg = img;
			}
		},

		calcDefaultSliderWidth: function() {
			this.defaultSliderWidth = domGeometry.getMarginBox(this.contentSlider.domNode).w;
			this.defaultItemWidths = [];
			array.forEach(this.itemNodes, lang.hitch(this, function(itemNode) {
				this.defaultItemWidths.push(domGeometry.getMarginBox(itemNode).w);
			}));
		},

		calcOffsets: function() {
			this.offsets = [0];
			var maxOffset = Math.max(0, this.defaultSliderWidth - domGeometry.getMarginBox(this.contentSliderWrapper.domNode).w);

			for (var i = 1; i < this.itemNodes.length; i++) {
				var offset = 0;
				for (var c = 0; c < i; c++) {
					offset += this.defaultItemWidths[c];
				}
				if (offset >= maxOffset) {
					this.offsets.push(maxOffset);
				} else {
					this.offsets.push(offset);
				}
			}
		},

		resizeCarousel: function() {
			if (this.bigThumbnails) {
				this._resizeBigThumbnails();
			}
			var totalItemsWidth = 0;
			array.forEach(this.itemNodes, function(imgWrapper) {
				var imgWrapperWidth = domGeometry.getMarginBox(imgWrapper).w;
				totalItemsWidth += imgWrapperWidth;
			});
			
			var contentSliderHeight = domGeometry.getMarginBox(this.contentSlider.domNode).h;
			domStyle.set(this.outerContainer.domNode, 'height', contentSliderHeight + 'px');

			var availableWidth = domGeometry.getMarginBox(this.domNode).w;

			if (availableWidth >= totalItemsWidth) {
				domClass.add(this.leftButton, 'dijitHidden');
				domClass.add(this.rightButton, 'dijitHidden');
				domStyle.set(this.outerContainer.domNode, 'width', totalItemsWidth + 'px');
				domStyle.set(this.contentSliderWrapper.domNode, 'width', totalItemsWidth + 'px');
			} else {
				domClass.remove(this.leftButton, 'dijitHidden');
				domClass.remove(this.rightButton, 'dijitHidden');

				var widthForThumbs = availableWidth - 
					  (domGeometry.getMarginBox(this.leftButton).w  + domGeometry.getMarginBox(this.rightButton).w);
				domStyle.set(this.outerContainer.domNode, 'width', availableWidth + 'px');
				domStyle.set(this.contentSliderWrapper.domNode, 'width', widthForThumbs + 'px');
			}
			this._toggleNavButtonsVisibility();
		},

		_resizeBigThumbnails: function(newIndex) {
			var maxHeight = dojo.window.getBox().h - 200;
			maxHeight = (maxHeight < this.itemHeight) ? this.itemHeight : maxHeight;

			var marginOfThumbs = domGeometry.getMarginExtents(this.itemNodes[0]).w;
			domClass.remove(this.leftButton, 'dijitHidden'); //make sure navButton is visible for sizing calculations
			domClass.remove(this.rightButton, 'dijitHidden');
			var maxWidth = domGeometry.getMarginBox(this.domNode).w - (domGeometry.getMarginBox(this.leftButton).w * 2) - marginOfThumbs;
			domStyle.set(this.outerContainer.domNode, 'width', '');
			domStyle.set(this.contentSliderWrapper.domNode, 'width', maxWidth + 'px');

			styles.disableStyleSheet('defaultItemHeightWrapper');
			
			domStyle.set(this.heighestImg, 'position', 'absolute');
			domStyle.set(this.heighestImg, 'right', '1000000px');
			domClass.toggle(this.heighestImg, 'dijitHidden');


			domStyle.set(this.heighestImg, 'max-height', maxHeight + 'px');
			domStyle.set(this.heighestImg, 'max-width', maxWidth + 'px');
			var heighestImgHeight = domGeometry.getMarginBox(this.heighestImg).h;
			domClass.toggle(this.heighestImg, 'dijitHidden');

			array.forEach(this.itemNodes, lang.hitch(this, function(imgWrapper) {
				domStyle.set(imgWrapper.firstChild, 'max-width', maxWidth + 'px');
				domStyle.set(imgWrapper.firstChild, 'max-height', maxHeight + 'px');
				domStyle.set(imgWrapper, 'height', heighestImgHeight + 'px');
				domStyle.set(imgWrapper, 'width', maxWidth + 'px');
			}));
			query('.galleryVideo', this.contentSlider.domNode).forEach(lang.hitch(this, function(videoWrapper) {
				domStyle.set(videoWrapper.firstChild, 'height', '100%');
				domStyle.set(videoWrapper.firstChild, 'width', '100%');
			}));
			domStyle.set(this.outerContainer.domNode, 'height', heighestImgHeight + 'px');

			var newOffset = newIndex * (maxWidth + marginOfThumbs);
			domStyle.set(this.contentSlider.domNode, 'left', (newOffset * (-1)) + 'px');
		},

		_toggleNavButtonsVisibility: function(newOffset) {
			var _contentSliderOffset;
			if (newOffset === undefined) {
				_contentSliderOffset = Math.abs(domStyle.get(this.contentSlider.domNode, 'left'));
			} else {
				_contentSliderOffset = newOffset;
			}
			
			var maxOffset = domGeometry.getMarginBox(this.contentSlider.domNode).w - domGeometry.getMarginBox(this.contentSliderWrapper.domNode).w;

			domClass.toggle(this.leftButton, 'disabled', (_contentSliderOffset === 0 || this.shownItemIndex === 0));
			domClass.toggle(this.rightButton, 'disabled', (_contentSliderOffset === maxOffset || this.shownItemIndex === this.items.length-1));
		},

		togglePreviewSize: function(newIndex) {
			if (this.bigThumbnails) {
				styles.enableStyleSheet('defaultItemHeightWrapper');
				var availableWidth = domGeometry.getMarginBox(this.domNode).w;

				if (availableWidth >= this.defaultSliderWidth) {
					domClass.add(this.leftButton, 'dijitHidden');
					domClass.add(this.rightButton, 'dijitHidden');
					domStyle.set(this.outerContainer.domNode, 'transition', 'height 0.5s, width 0.5s');
					domStyle.set(this.contentSliderWrapper.domNode, 'transition', 'height 0.5s, width 0.5s');
					domStyle.set(this.outerContainer.domNode, 'width', this.defaultSliderWidth + 'px');
					domStyle.set(this.contentSliderWrapper.domNode, 'width', this.defaultSliderWidth + 'px');
				}


				query('.carouselScreenshot', this.contentSlider.domNode).forEach(lang.hitch(this, function(imgNode) {
					domStyle.set(imgNode, 'max-height', '');
					domStyle.set(imgNode, 'max-width', '');
					domStyle.set(imgNode.parentNode, 'width', '');
					domStyle.set(imgNode.parentNode, 'height', '');
				}));
				query('.galleryVideo', this.contentSlider.domNode).forEach(lang.hitch(this, function(videoWrapper) {
					domStyle.set(videoWrapper, 'height', '');
					domStyle.set(videoWrapper, 'width', '');
					domStyle.set(videoWrapper.firstChild, 'height', '');
					domStyle.set(videoWrapper.firstChild, 'width', '');
				}));
				domStyle.set(this.outerContainer.domNode, 'height', this.itemHeight + 'px');
				domStyle.set(this.contentSlider.domNode, 'left', Math.abs(this.offsets[newIndex]) * (-1) + 'px');
				
			} else {
				domStyle.set(this.outerContainer.domNode, 'transition', '');
				domStyle.set(this.contentSliderWrapper.domNode, 'transition', '');
				this._resizeBigThumbnails(newIndex);
			}
			this.bigThumbnails = !this.bigThumbnails;
			domClass.toggle(this.scaleButton, 'minimize');
			this.shownItemIndex = newIndex;

			setTimeout(lang.hitch(this, function() {
				this.resizeCarousel();
			}), 600);

			//scroll to the top of the image
			//var scrollTarget = domGeometry.position(this.domNode, true).y - 50;
			//window.scrollTo(0, scrollTarget);
		},

		showItem: function(newIndex) {
			if (newIndex < 0 || newIndex >= this.itemNodes.length) {
				return;
			}

			var newOffset = 0;

			var neededOffset = 0;
			for (var i = 0; i < newIndex; i++) {
				var itemWidth = domGeometry.getMarginBox(this.itemNodes[i]).w;
				neededOffset += itemWidth;
			}
			
			var maxOffset = domGeometry.getMarginBox(this.contentSlider.domNode).w - domGeometry.getMarginBox(this.contentSliderWrapper.domNode).w;
			if (neededOffset >= maxOffset) {
				newOffset = maxOffset;
			} else {
				newOffset = neededOffset;
			}

			var oldOffset = Math.abs(domStyle.get(this.contentSlider.domNode, 'left'));
			
			//if the new index would not change the offset
			//take the next lower index till a new offset is found
			if (oldOffset === newOffset && newIndex < this.shownItemIndex) {
				this.showItem(newIndex -1);
				return;
			}

			this.shownItemIndex = newIndex;
			domStyle.set(this.contentSlider.domNode, 'left', (newOffset * (-1)) + 'px');

			this._toggleNavButtonsVisibility(newOffset);
		},

		_handleResize: function() {
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}
			this._resizeDeferred = tools.defer(lang.hitch(this, function() {
				this.resizeCarousel();
				this.calcOffsets();
				this.showItem(this.shownItemIndex);
			}), 200);
			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		startup: function() {
			this.inherited(arguments);
			this._registerAtParentOnShowEvents(lang.hitch(this, function() {
				if (this.defaultSliderWidth === 0 && !this.bigThumbnails) {
					this.calcDefaultSliderWidth();
				}
				if (this.allItemsLoaded) {
					this.resizeCarousel();
					this.showItem(this.shownItemIndex);
				}
			}));
			this.own(on(baseWin.doc, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
			styles.enableStyleSheet('defaultItemHeightWrapper');
		}
	});
});
