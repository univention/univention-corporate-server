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
	"umc/widgets/_RegisterOnShowMixin"
], function(declare, array, lang, kernel, baseWin, on, query, domConstruct, domStyle, domGeometry, domClass, styles, tools, ContainerWidget, _RegisterOnShowMixin) {
	return declare("umc.modules.appcenter.Carousel_new", [ContainerWidget, _RegisterOnShowMixin], {
		baseClass: 'umcCarouselWidget',

		outerContainer: null,
		contentSlider: null,
		contentSliderOffset: null,

		shownItemIndex: null,

		itemHeight: null,

		// items: Array
		//     array of objects({src: <src>})
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

			this.loadedImagesCount = 0;
			var index = 0;

			array.forEach(this.items, lang.hitch(this, function(item) {
				var imgWrapper = domConstruct.create('div', {}, this.contentSlider.domNode);
				var img = domConstruct.create('img', {
					src: item.src,
					index: index,
					'class': 'carouselScreenshot',
					onload: lang.hitch(this, function() {
						this.imagesLoaded();
					}),
					onclick: lang.hitch(this, function(evt) {
						this.togglePreviewSize(parseInt(evt.target.getAttribute('index')));
					})
				}, imgWrapper);
				this.itemNodes.push(imgWrapper);
				index++;
			}));

			if (!styles.getStyleSheet('defaultItemHeightWrapper')) {
				styles.insertCssRule('.contentSlider .carouselScreenshot', lang.replace('height: {0}px', [this.itemHeight]), 'defaultItemHeightWrapper');
			}
			if (!styles.getStyleSheet('defaultItemHeightImage')) {
				styles.insertCssRule('.contentSlider div', lang.replace('height: {0}px', [this.itemHeight]), 'defaultItemHeightImage');
			}

			this.scaleButton = domConstruct.create('div', {
				'class': 'scaleButton',
				onclick: lang.hitch(this, function(e) {
					//e.stopPropagation();
					this.togglePreviewSize();
				})
			}, this.domNode);
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

		imagesLoaded: function() {
			this.loadedImagesCount++;
			if (this.loadedImagesCount === this.items.length) {
				this.allItemsLoaded = true;
				this.resizeCarousel();
			}
		},

		resizeCarousel: function() {
			if (this.bigThumbnails) {
				this._resizeBigThumbnails();
			}
			var totalItemsWidth = 0;
			array.forEach(this.itemNodes, function(imgWrapper) {
				var imgWidth = domGeometry.getContentBox(imgWrapper.firstChild).w;
				//domStyle.set(imgWrapper, 'width', imgWidth + 'px');
				var imgWrapperWidth = domGeometry.getMarginBox(imgWrapper).w;
				totalItemsWidth += imgWrapperWidth;
			});
			domStyle.set(this.contentSlider.domNode, 'width', totalItemsWidth + 'px');
			
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

				var widthForItems = availableWidth - (domGeometry.getMarginBox(this.leftButton).w * 2);
				domStyle.set(this.outerContainer.domNode, 'width', availableWidth + 'px');
				domStyle.set(this.contentSliderWrapper.domNode, 'width', widthForItems + 'px');
			}
			this._toggleNavButtonsVisibility();
		},

		_resizeBigThumbnails: function() {
			var maxHeight = dojo.window.getBox().h - 200;
			maxHeight = (maxHeight < this.itemHeight) ? this.itemHeight : maxHeight;
			var marginWidth = domGeometry.getMarginExtents(this.itemNodes[0]).w;
			//make sure navButton is visible for sizing calculations
			domClass.remove(this.leftButton, 'dijitHidden');
			var maxWidth = domGeometry.getMarginBox(this.domNode).w - (domGeometry.getMarginBox(this.leftButton).w * 2) - marginWidth;

			styles.disableStyleSheet('defaultItemHeightWrapper');
			styles.disableStyleSheet('defaultItemHeightImage');

			var heighestImg = 0;
			query('.carouselScreenshot', this.contentSlider.domNode).forEach(lang.hitch(this, function(imgNode) {
				domStyle.set(imgNode, 'max-height', maxHeight + 'px');
				domStyle.set(imgNode, 'max-width', maxWidth + 'px');
				domStyle.set(imgNode.parentNode, 'width', maxWidth + 'px');
				domStyle.set(imgNode.parentNode, 'height', maxHeight + 'px');
				
				var imgHeight = domGeometry.getMarginBox(imgNode).h;
				heighestImg = (imgHeight > heighestImg) ? imgHeight : heighestImg;
			}));
			query('.carouselScreenshot', this.contentSlider.domNode).forEach(lang.hitch(this, function(imgNode) {
				domStyle.set(imgNode.parentNode, 'height', heighestImg + 'px');
			}));
		},

		_toggleNavButtonsVisibility: function(newOffset) {
			if (newOffset === undefined) {
				var contentSliderOffset = Math.abs(domStyle.get(this.contentSlider.domNode, 'left'));
			} else {
				var contentSliderOffset = newOffset;
			}
			
			var maxOffset = domGeometry.getMarginBox(this.contentSlider.domNode).w - domGeometry.getMarginBox(this.contentSliderWrapper.domNode).w;

			domClass.toggle(this.leftButton, 'disabled', (contentSliderOffset === 0 || this.shownItemIndex === 0));
			domClass.toggle(this.rightButton, 'disabled', (contentSliderOffset === maxOffset || this.shownItemIndex === this.items.length-1));
		},

		togglePreviewSize: function(indexAfterToggle) {
			if (indexAfterToggle === undefined) {
				indexAfterToggle = this.shownItemIndex;
			}
			domClass.add(this.contentSlider.domNode, 'noTransition');
			if (this.bigThumbnails) {
				styles.enableStyleSheet('defaultItemHeightWrapper');
				styles.enableStyleSheet('defaultItemHeightImage');
				query('.carouselScreenshot', this.contentSlider.domNode).forEach(lang.hitch(this, function(imgNode) {
					domStyle.set(imgNode, 'max-height', '');
					domStyle.set(imgNode, 'max-width', '');
					domStyle.set(imgNode.parentNode, 'width', '');
					domStyle.set(imgNode.parentNode, 'height', this.itemHeight + 'px');
				}));
			} else {
				this._resizeBigThumbnails();
			}
			this.bigThumbnails = !this.bigThumbnails;
			domClass.toggle(this.scaleButton, 'minimize');

			this.resizeCarousel();
			this.showItem(indexAfterToggle);
			domClass.remove(this.contentSlider.domNode, 'noTransition');

			//scroll to the top of the image
			var scrollTarget = domGeometry.position(this.domNode, true).y - 50;
			window.scrollTo(0, scrollTarget);
		},

		showItem: function(newIndex) {
			if (newIndex < 0 || newIndex > this.itemNodes.length || newIndex === this.itemNodes.length) {
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
			if (oldOffset === newOffset) {
				if (newIndex < this.shownItemIndex) {
					this.showItem(newIndex -1);
					return;
				}
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
				this.showItem(this.shownItemIndex);
			}), 200);
			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		startup: function() {
			this.inherited(arguments);
			this._registerAtParentOnShowEvents(lang.hitch(this, function() {
				if (this.allItemsLoaded) {
					this.resizeCarousel();
					this.showItem(this.shownItemIndex);
				}
			}));
			this.own(on(baseWin.doc, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
			styles.enableStyleSheet('defaultItemHeightWrapper');
			styles.enableStyleSheet('defaultItemHeightImage');
		}
	});
});
