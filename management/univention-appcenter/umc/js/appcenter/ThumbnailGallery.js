/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/Deferred",
	"dojox/html/styles",
	"umc/tools",
	"umc/widgets/ContainerWidget"
], function(declare, array, lang, kernel, baseWin, on, query, domConstruct, domStyle, domGeometry, domClass, Deferred, styles, tools, ContainerWidget) {
	return declare("umc.modules.appcenter.ThumbnailGallery", [ContainerWidget], {
		baseClass: 'umcThumbnailGallery',

		outerContainer: null,

		//is the viewport for the contentSlider
		contentSliderWrapper: null,

		//the contentSlider contains all thumbs
		//the offset of the contentSlider gets changed to show different thumbs
		contentSlider: null,

		//the current offset off the contentSlider as absolute value ignoring navButtons
		//used for calculations
		contentSliderOffset: null,

		//the currently displayed offset as absolute value
		//the navButtons lay on top of the contentSlider but the calculations ignore that fact. so the width of one or 
		//both navButtons have to be accounted after the fact
		_visibleOffset: null,

		//toggles thumb size
		scaleButton: null,

		//all ThumbNodes that are in the contentSlider
		itemNodes: null,

		//shownItemIndex: int
		//     The currently visible thumb (itemNodes[shownItemIndex]).
		//     In the small view the shownItemIndex is either the leftmost or rightmost thumb
		//     based on the last call of showPrevThumbs or showNextThumbs.
		//     In the big view it is the visible thumb.
		shownItemIndex: null,

		//the default height for gallery thumbs in the small view
		defaultThumbHeight: null,

		//heighestImg: {w: number, h: number}
		//     the natural width and height of the highest img in the contentSlider
		heighestImg: null,

		//heighestImgRatio = heighestImg.w / heighestImg.h
		//     If there are only videos in the contentSlider
		//     the heighestImgRatio defaults to the _youtubeIframeRatio
		//     to determine the height for big Thumbnails
		heighestImgRatio: null,

		//used to check if the contentSliderWrapper is to small for showNextThumbs and showPrevThumbs to work correctly
		//and change behavior accordingly
		widestDefaultThumbWidth: null,

		//_youtubeIframeRatio: defaults to 16/9
		_youtubeIframeRatio: null,

		// items: Array
		//     array of received objects({src: <src-string>})
		//     where <src-string> is either an image or a youtube video url 
		items: null,
		
		//preparedItems: Array
		//     array of objects derived from items.
		//     Duplicate youtube videos are removed and
		//     objects are marked as either 'img' or 'video'
		preparedItems: null,

		//allItemsLoaded: bool
		allItemsLoaded: null,

		_loadedThumbsCount: null,

		//isBigThumbnails: bool
		isBigThumbnails: null,

		//the margin each thumb has on either side
		_galleryThumbLeftRightMargin: null,
		//the whole left and right margin for thumbs
		_galleryThumbMarginExtents: null,

		//naturalThumbDimensions: object{<thumbIndex>: {w: <width>, h: <height>}}
		//    stores the unscaled width and height of the images.
		//    defaults to w: 1600, h: 900 for videos
		naturalThumbDimensions: null,

		//defaultThumbWidths: object{<thumbIndex>: <width + this._galleryThumbMarginExtents>}
		//    The default width for all thumbs in the small view including this._galleryThumbMarginExtents
		defaultThumbWidths: null,

		//defaultThumbOffsets: array
		//    contains the offset for every thumb so it is the leftmost first visible thumb
		defaultThumbOffsets: null,

		//ytPlayers: Array
		//     array of youtube Player objects for every video in the Gallery
		//     ( https://developers.google.com/youtube/iframe_api_reference?hl=de#Loading_a_Video_Player )
		//     used to pause videos if they are no longer visible
		ytPlayers: null,

		//thumbIndexToVideoId: object
		//     maps the id of the videoThumb to its youtube video_id
		thumbIndexToVideoId: null,
		videoIdToThumbIndex: null,

		//playingVideos: array
		playingVideos: null,

		//_insertedCssRules: Array
		//     contains array with objects with the selector and declaration inserted via styles.insertCssRule.
		//     {selector: <selector>, declaration: <declaration>}
		_insertedCssRules: null,

		_resizeDeferred: null,

		_firstResizeInterval: null,

		_stopFirstResize: null,

		//_baseTransitionDuration: int in ms
		_baseTransitionDuration: null,

		postMixInProperties: function() {
			this.preparedItems = [];
			this.defaultThumbHeight = this.defaultThumbHeight || 200;
			this.itemNodes = [];
			this.contentSliderOffset = 0;
			this._visibleOffset = 0;
			this.shownItemIndex = 0;
			this.allItemsLoaded = false;
			this.isBigThumbnails = false;
			this._youtubeIframeRatio = 16 / 9;
			//if there are only youtube videos in the contentslider
			//the height for big thumbnails is determined by the _youtubeIframeRatio
			this.heighestImgRatio = this._youtubeIframeRatio;
			this.heighestImg = {w: 0, h: 0};
			this.widestDefaultThumbWidth = 0;
			this._galleryThumbLeftRightMargin = 10;
			this._galleryThumbMarginExtents = 2 * this._galleryThumbLeftRightMargin;
			this.naturalThumbDimensions = {};
			this.defaultThumbWidths = {};
			this.ytPlayers = {};
			this.thumbIndexToVideoId = {};
			this.videoIdToThumbIndex = {};
			this.playingVideos = {};
			this._insertedCssRules = [];
			this._totalWidthOfSmallThumbs = 0;
			this._bigThumbDimensions = {};
			this._smallMaxOffset = 0;
			this._widthForThumbs = 0;
			this.loaded = false;
			this._smallViewHasNavButtons = false;
			this._stopFirstResize = false;
			this._baseTransitionDuration = 500;
		},

		postCreate: function() {
			//check if youtube iframe api is already loaded
			if (window.YT && window.YT.loaded) {
				//stub
			} else {
				//load youtube iframe api
				var tag = document.createElement('script');
				tag = domConstruct.create('script', {
					id: "youtubeAPI",
					src: "https://www.youtube.com/iframe_api"
				});
				var firstScriptTag = document.getElementsByTagName('script')[0];
				firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
			}
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._insertGalleryVideoDefaultDimensions();
			this._insertGalleryThumbCssRules();
			this._insertTransitionDurations();

			//style needed while thumbs are getting loaded
			domStyle.set(this.domNode, 'height', this.defaultThumbHeight + 'px');
			domStyle.set(this.domNode, 'overflow', 'hidden');

			this._scrollTarget = domConstruct.create('div', {
				'class': 'galleryScrollTarget',
				style: {
					'position': 'absolute'
				}
			}, this.domNode);

			this.galleryLoadingOverlay = domConstruct.create('div', {
				'class': 'galleryLoadingOverlay'
			}, this.domNode);

			this.outerContainer = new ContainerWidget({
				'class': 'galleryOuterContainer'
			});
			this.contentSliderWrapper = new ContainerWidget({
				'class': 'contentSliderWrapper'
			});

			this.outerContainer.addChild(this.contentSliderWrapper);
			this.addChild(this.outerContainer);
			this.own(this.outerContainer);

			this.renderNavButtons();
			this.renderScaleButton();
			this.renderContentSlider();
		},

		renderNavButtons: function() {
			//construct left and right navButtons
			this.leftButton = domConstruct.create('div', {
				'class': 'galleryNavButton leftGalleryNavButton disabled'
			}, this.contentSliderWrapper.domNode, 'before');
			on(this.leftButton, 'click', lang.hitch(this, function() {
				this.showPrevThumbs();
			}));
			domConstruct.create('div', {
				'class': 'galleryNavButtonImage'
			}, this.leftButton);

			this.rightButton = domConstruct.create('div', {
				'class': 'galleryNavButton rightGalleryNavButton disabled'
			}, this.contentSliderWrapper.domNode, 'after');
			on(this.rightButton, 'click', lang.hitch(this, function() {
				this.showNextThumbs();
			}));
			domConstruct.create('div', {
				'class': 'galleryNavButtonImage'
			}, this.rightButton);

			//insert Css Rule
			var selector = lang.replace('#{0} .galleryNavButton', [this.id]);
			var declaration = lang.replace('height: {0}px; transition-duration: {1}ms', [this.defaultThumbHeight, this._baseTransitionDuration]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssRules.push({selector: selector, declaration: declaration});
		},

		renderScaleButton: function() {
			this.scaleButton = domConstruct.create('div', {
				'class': 'scaleButton dijitDisplayNone',
				onclick: lang.hitch(this, function() {
					this.toggleThumbSize(this.shownItemIndex);
				})
			}, this.domNode);
		},

		renderContentSlider: function() {
			this.contentSlider = new ContainerWidget({
				'class': 'contentSlider'
			});

			this.galleryThumbVerticalAlignHelper = domConstruct.create('div', {
				'class': 'galleryThumb verticalAlignHelper'
			}, this.contentSlider.domNode);

			this.contentSliderWrapper.addChild(this.contentSlider);

			this._renderThumbs();
		},

		_renderThumbs: function() {
			this._prepareItems();
			this._loadedThumbsCount = 0;

			array.forEach(this.preparedItems, lang.hitch(this, function(item, index) {
				if (item.type === 'video') {
					this._createVideoThumb(item, index);
				} else {
					this._createImgThumb(item, index);
				}
			}));
		},

		_prepareItems: function() {
			var uniqueYTVideoIds = [];

			array.forEach(this.items, lang.hitch(this, function(item, index) {
				if (this._srcIsYoutubeVideo(item.src)) {
					var videoId = this._getYoutubeUrlVideoId(item.src);
					if (uniqueYTVideoIds.indexOf(videoId) !== -1) {
						return;
					}
					uniqueYTVideoIds.push(videoId);
					this.preparedItems.push({type: 'video', videoId: videoId});
				} else {
					this.preparedItems.push({type: 'img', src: item.src});
				}
			}));
		},

		_createVideoThumb: function(item, index) {
			var videoId = item.videoId;

			//get the thumbnail for the youtube video via the unique id
			var ytVideoThumbnailURL = lang.replace('https://img.youtube.com/vi/{0}/hqdefault.jpg', [videoId]);

			var galleryVideoWrapper = domConstruct.create('div', {
				id: 'galleryThumb_' + index,
				'class': 'galleryThumb galleryVideoThumb galleryVideoWrapper'
			}, this.contentSlider.domNode);

			//show the thumbnail of the video with a playbutton
			var thumbNailWrapper = domConstruct.create('div', {
				'class': 'galleryVideoThumbnailWrapper'
			}, galleryVideoWrapper);

			var thumbNail = domConstruct.create('div', {
				'class': 'galleryVideoThumbnail'
			}, thumbNailWrapper);
			var playButtonImg = domConstruct.create('div', {
				'class': 'galleryVideoPlayButtonIcon'
			}, thumbNailWrapper);

			//this div gets replaced by the youtube iframe
			var galleryVideo = domConstruct.create('div', {
				'class': 'galleryVideo dijitDisplayNone',
				id: videoId
			}, galleryVideoWrapper);

			//set the thumbnail of the ytVideo as Background
			var selector = lang.replace('#{0} #galleryThumb_{1} .galleryVideoThumbnail', [this.id, index]);
			var declaration = lang.replace('background-image: url({0})', [ytVideoThumbnailURL]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssRules.push({selector: selector, declaration: declaration});

			//load youtube video
			on(galleryVideoWrapper, 'click', lang.hitch(this, function() {
				this.shownItemIndex = index;
				if (window.YT && window.YT.loaded) {
					this.showThumb(this.shownItemIndex);
					domClass.add(galleryVideoWrapper, 'loaded');
					domClass.remove(galleryVideo, 'dijitDisplayNone');
					domClass.add(playButtonImg, 'dijitDisplayNone');
					domClass.add(thumbNailWrapper, 'dijitDisplayNone');
					setTimeout(lang.hitch(this, function() {
						this._renderYoutubeVideo(galleryVideo, index);
					}), 0);
				}
			}));

			this.naturalThumbDimensions[index] = {w: 1600, h: 900};
			var w = Math.round(this.defaultThumbHeight * this._youtubeIframeRatio);
			var h = this.defaultThumbHeight;
			this.defaultThumbWidths[index] = w + this._galleryThumbMarginExtents;
			this._updateWidestThumb(w);

			this.itemNodes.push(galleryVideoWrapper);
			item.domNode = galleryVideoWrapper;
			this.thumbLoaded();
		},

		_createImgThumb: function(item, index) {
			var imgUrl = item.src;
			var galleryImgThumb = domConstruct.create('div', {
				'class': 'galleryThumb galleryImgThumb',
				id: 'galleryThumb_' + index
			}, this.contentSlider.domNode);

			var img = domConstruct.create('img', {
				src: imgUrl,
				onload: lang.hitch(this, function() {
					this._updateHeighestImage(img);
					this.naturalThumbDimensions[index] = {w: img.naturalWidth, h: img.naturalHeight};

					//calc the width and height for the thumb in the small view
					var w = Math.round(this.defaultThumbHeight * (img.naturalWidth / img.naturalHeight));
					var h = this.defaultThumbHeight;
					this.defaultThumbWidths[index] = w + this._galleryThumbMarginExtents;
					this._updateWidestThumb(w);

					//insert img as background
					var selector = lang.replace('#{0} #{1}', [this.id, galleryImgThumb.id]);
					var declaration = lang.replace('width: {0}px; height: {1}px; background-image: url({2})', [w, h, img.src]);
					styles.insertCssRule(selector, declaration);
					this._insertedCssRules.push({selector: selector, declaration: declaration});

					this.thumbLoaded();
				}),
				onerror: lang.hitch(this, function() {
					//calc the width and height for the thumb in the small view
					var w = Math.round(this.defaultThumbHeight * (3/4));
					var h = this.defaultThumbHeight;
					this.naturalThumbDimensions[index] = {w: w, h: h};
					this.defaultThumbWidths[index] = w + this._galleryThumbMarginExtents;
					this._updateWidestThumb(w);

					//insert img as background
					var selector = lang.replace('#{0} #{1}', [this.id, galleryImgThumb.id]);
					var declaration = lang.replace('width: {0}px; height: {1}px;', [w, h]);
					styles.insertCssRule(selector, declaration);
					this._insertedCssRules.push({selector: selector, declaration: declaration});
					domClass.add(galleryImgThumb, 'brokenImg');

					this.thumbLoaded();
				})
			});

			on(galleryImgThumb, 'click', lang.hitch(this, function() {
				this.toggleThumbSize(index);
			}));
			this.itemNodes.push(galleryImgThumb);
			item.domNode = galleryImgThumb;
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

		_insertGalleryVideoDefaultDimensions: function() {
			//calc default width and height
			var width = Math.round(this.defaultThumbHeight * this._youtubeIframeRatio);
			var height = this.defaultThumbHeight;

			//insert Css Rule
			var selector = lang.replace('#{0}.{1} .contentSlider .galleryVideoWrapper', [this.id, this.baseClass]);
			var declaration = lang.replace('width: {0}px; height: {1}px', [width, height]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssRules.push({selector: selector, declaration: declaration});
		},

		_insertGalleryThumbCssRules: function() {
			var selector = lang.replace('#{0} .contentSlider .galleryThumb', [this.id]);
			var declaration = lang.replace('margin: 0 {0}px; transition-duration: {1}ms', [this._galleryThumbLeftRightMargin, this._baseTransitionDuration]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssRules.push({ selector: selector, declaration: declaration });
		},

		_insertTransitionDurations: function() {
			var selector;
			var declaration;
			//contentSlider
			selector = lang.replace('#{0} .contentSlider', [this.id]);
			declaration = lang.replace('transition-duration: {0}ms', [this._baseTransitionDuration]);
			styles.insertCssRule(selector, declaration);
			this._insertedCssRules.push({ selector: selector, declaration: declaration });
		},

		_renderYoutubeVideo: function(galleryVideo, index) {
			var player;
			var videoId = galleryVideo.id;
			//add the youtube video via the youtube iframe api
			player = new YT.Player(videoId, {
				videoId: videoId,
				events: {
					'onReady': lang.hitch(this, this.onPlayerReady),
					'onStateChange': lang.hitch(this, this.onPlayerStateChange)
				}
			});
			this.own(player);
			
			//safe a reference to the video id accessible through the thumbIndex and vice versa
			this.thumbIndexToVideoId[index] = videoId;
			this.videoIdToThumbIndex[videoId] = index;
			//safe the youtube player object
			this.ytPlayers[videoId] = {playerIndex: index};
		},

		onPlayerReady: function(evt) {
			evt.target.playVideo();
			var videoId = evt.target.getVideoData().video_id;
			this.ytPlayers[videoId].player = evt.target;
		},

		onPlayerStateChange: function(evt) {
			var videoId;
			if (evt.data && evt.data === YT.PlayerState.PLAYING) {
				//safe clicked video as playing video and center it
				videoId = evt.target.getVideoData().video_id;
				if (this.playingVideos[videoId]) {
					return;
				}
				this.playingVideos[videoId] = evt.target;
				var index = this.videoIdToThumbIndex[videoId];
				if (index !== this.shownItemIndex) {
					this.showThumb(index);
				}
			} else if (evt.data === YT.PlayerState.PAUSED || evt.data === YT.PlayerState.ENDED) {
				//remove paused video from playing videos
				videoId = evt.target.getVideoData().video_id;
				delete this.playingVideos[videoId];
			}
		},

		//checks if all divs in the contentSlider are ready
		thumbLoaded: function() {
			this._loadedThumbsCount++;
			if (this._loadedThumbsCount === this.preparedItems.length) {
				this.onAllThumbsLoaded();
			}
		},

		onAllThumbsLoaded: function() {
			this.allItemsLoaded = true;

			//calc offsets for all thumbs in the small view
			this.defaultThumbOffsets = [];
			var offset = 0;
			for (var i = 0; i < this.itemNodes.length; i++) {
				this.defaultThumbOffsets.push(offset);
				offset += this.defaultThumbWidths[i];
			}

			this._handleFirstResize();
		},

		//waits till the gallery is visible in the domTree
		//can be cancelled with _stopFirstResize=true (added for use in TitlePane)
		_handleFirstResize: function() {
			//avoid the 200ms interval if possible
			if (domGeometry.getMarginBox(this.domNode).w !== 0) {
				this._handleResize();
			} else {
				this._firstResizeInterval = setInterval(lang.hitch(this, function() {
					if (this._stopFirstResize) {
						clearInterval(this._firstResizeInterval);
					} else if (domGeometry.getMarginBox(this.domNode).w !== 0) {
						clearInterval(this._firstResizeInterval);
						this._handleResize();
					}
				}), 200);
			}
		},

		_updateHeighestImage: function(img) {
			if (img.naturalHeight > this.heighestImg.h) {
				this.heighestImg.w = img.naturalWidth;
				this.heighestImg.h = img.naturalHeight;
				this.heighestImgRatio = img.naturalWidth / img.naturalHeight;
			}
		},

		_updateWidestThumb: function(width) {
			if (width > this.widestDefaultThumbWidth) {
				this.widestDefaultThumbWidth = width;
			}
		},

		resizeGallery: function() {
			if (domGeometry.getMarginBox(this.domNode).w === 0) {
				return;
			}

			//calc all values needed for toggling thumbsize and showing items
			this._galleryWidth = domGeometry.getMarginBox(this.domNode).w;
			this._leftNavButtonWidth = domGeometry.getMarginBox(this.leftButton).w;
			this._rightNavButtonWidth = domGeometry.getMarginBox(this.rightButton).w;
			this._widthForThumbs = this._galleryWidth - (this._leftNavButtonWidth + this._rightNavButtonWidth);

			this._totalWidthOfSmallThumbs = 0;
			for (var i = 0; i < this.itemNodes.length; i++) {
				thumbWidth = this.defaultThumbWidths[i];
				this._totalWidthOfSmallThumbs += thumbWidth;
			}

			this._smallMaxOffset = Math.max(this._totalWidthOfSmallThumbs - this._widthForThumbs, 0);
			this._bigThumbDimensions = this._getMaxWidthHeightForBigThumbs();
			var _bigContentSliderWidth = this.itemNodes.length * (this._bigThumbDimensions.maxWidthForThumb + this._galleryThumbMarginExtents);
			this._bigMaxOffset = _bigContentSliderWidth - this._widthForThumbs;
			this._smallViewHasNavButtons = this._totalWidthOfSmallThumbs > this._galleryWidth;


			if (this.isBigThumbnails) {
				this.centerScrollGallery();
				this._resizeNavButtons();
			}
			//reshow the current thumb with new dimensions
			setTimeout(lang.hitch(this, function() {
				this.showThumb(this.shownItemIndex);
			}), 0);
		},

		_toggleNavButtonsVisibility: function(newOffset) {
			if (this.isBigThumbnails || this._smallViewHasNavButtons) {
				domClass.toggle(this.leftButton, 'disabled', (this.contentSliderOffset === 0 || this.shownItemIndex === 0));
				domClass.toggle(this.rightButton, 'disabled', ((this.isBigThumbnails && this.contentSliderOffset === this.defaultThumbOffsets[this.itemNodes.length-1]) || (!this.isBigThumbnails && this.contentSliderOffset === this._smallMaxOffset) || this.shownItemIndex === this.itemNodes.length - 1));
			} else {
				domClass.add(this.leftButton, 'disabled');
				domClass.add(this.rightButton, 'disabled');
			}
		},

		showThumb: function(thumbIndex) {
			if (thumbIndex < 0 || thumbIndex >= this.itemNodes.length) {
				return;
			}

			var newOffsetIgnoringNavButtons = 0;
			var newOffsetWithNavButtons = 0;

			if (this.isBigThumbnails) {
				////for big thumbnails
				this._hideVideosTemporarily(this._baseTransitionDuration + 50);

				var targetThumb = this.itemNodes[thumbIndex];

				//revert previously enlarged thumb and enlarge new thumb
				query('.galleryThumb.enlarged', this.contentSlider.domNode).style('width', '').style('height', '').removeClass('enlarged');
				////_width
				domStyle.set(targetThumb, 'width', lang.replace('{0}px', [this._bigThumbDimensions.maxWidthForThumb]));
				////_height
				var targetThumbIsVideo = domClass.contains(targetThumb, 'galleryVideoThumb');
				var maxHeight = targetThumbIsVideo ? this._bigThumbDimensions.maxHeightForVideoThumb : this._bigThumbDimensions.maxHeightForImgThumb;
				domClass.add(targetThumb, 'enlarged');
				domStyle.set(targetThumb, 'height', maxHeight + 'px');

				//get new offset
				newOffsetIgnoringNavButtons = this.defaultThumbOffsets[thumbIndex];
				newOffsetWithNavButtons = newOffsetIgnoringNavButtons - this._leftNavButtonWidth;
			} else { 
				////for small thumbnails
				if (!this._smallViewHasNavButtons) {
					newOffsetIgnoringNavButtons = -((this._widthForThumbs - this._totalWidthOfSmallThumbs) / 2) - domGeometry.getMarginBox(this.leftButton).w;
					newOffsetWithNavButtons = newOffsetIgnoringNavButtons;
				} else {
					//offset for target thumb so that it is just visible
					newOffsetIgnoringNavButtons = this.defaultThumbOffsets[thumbIndex];

					//calc offset so that targetThumb is centered
					var targetThumbWidth = this.defaultThumbWidths[thumbIndex];
					var newOffsetCentered = newOffsetIgnoringNavButtons - ((this._widthForThumbs - targetThumbWidth) / 2);

					//if the centered offset would show blank parts of the contentSlider revert to 0 or maxOffset
					//if the centered thumb would only be 50px away from 0 or maxOffset set them to 0 or maxOffset
					if (newOffsetCentered <= (this._galleryThumbMarginExtents + 30) ) {
						newOffsetIgnoringNavButtons = 0;
						newOffsetWithNavButtons = newOffsetIgnoringNavButtons;
					} else if (newOffsetCentered + (this._galleryThumbMarginExtents + 30) >= this._smallMaxOffset) {
						newOffsetIgnoringNavButtons = this._smallMaxOffset;
						newOffsetWithNavButtons = this._smallMaxOffset - this._leftNavButtonWidth - this._rightNavButtonWidth;
					} else {
						newOffsetIgnoringNavButtons = newOffsetCentered;
						newOffsetWithNavButtons = newOffsetIgnoringNavButtons - this._leftNavButtonWidth;
					}
				}
			}

			//set new offset and thumbIndex
			this.shownItemIndex = thumbIndex || 0;
			domStyle.set(this.contentSlider.domNode, 'transform', lang.replace('translate3d({0}px, 0, 0)', [(newOffsetWithNavButtons * (-1))]));
			domStyle.set(this.contentSlider.domNode, '-webkit-transform', lang.replace('translate3d({0}px, 0, 0)', [(newOffsetWithNavButtons * (-1))]));
			this.contentSliderOffset = newOffsetIgnoringNavButtons;
			this._visibleOffset = newOffsetWithNavButtons;

			this._toggleNavButtonsVisibility();
		},

		showNextThumbs: function() {
			maxOffset = this.isBigThumbnails ? this._bigMaxOffset : this._smallMaxOffset;
			if (this.contentSliderOffset === maxOffset || this.shownItemIndex === this.itemNodes.length - 1) {
				return;
			}

			//define functions
			_calcCurrentFullyVisibleThumbs = lang.hitch(this, function() {
				var lastFullyVisibleThumbIndex = 0;
				var totalThumbsWidth = 0;

				var tmpWidth = 0;
				var _widthForThumbs = this.shownItemIndex === 0 ? this._widthForThumbs + this._leftNavButtonWidth : this._widthForThumbs;
				for (var tmpIndex = 0; tmpIndex <= this.itemNodes.length -1; ++tmpIndex) {
					tmpWidth += this.defaultThumbWidths[tmpIndex];

					isCurrentThumbFullyVisible = (tmpWidth - this._galleryThumbLeftRightMargin) <= (_widthForThumbs + this.contentSliderOffset);
					if (!isCurrentThumbFullyVisible) {
						break;
					}
					totalThumbsWidth = tmpWidth;
					lastFullyVisibleThumbIndex = tmpIndex;
				}
				
				return {
					lastIndex: lastFullyVisibleThumbIndex,
					width: totalThumbsWidth
				};
			});

			_calcNewFullyVisibleThumbs = lang.hitch(this, function(currThumbs) {
				var lastFullyVisibleThumbIndex = currThumbs.lastIndex + 1;
				var totalThumbsWidth = 0;
				
				var tmpWidth = 0;
				var _widthForThumbs = this._widthForThumbs;
				for (var tmpIndex = lastFullyVisibleThumbIndex; tmpIndex <= this.itemNodes.length -1; ++tmpIndex) {
					tmpWidth += this.defaultThumbWidths[tmpIndex];

					if (tmpIndex === this.itemNodes.length-1) {
						_widthForThumbs += this._leftNavButtonWidth;
					}
					isCurrentThumbFullyVisible = tmpWidth < _widthForThumbs;
					if (!isCurrentThumbFullyVisible) {
						break;
					}
					totalThumbsWidth = tmpWidth;
					lastFullyVisibleThumbIndex = tmpIndex;
				}

				return {
					lastIndex: lastFullyVisibleThumbIndex,
					width: totalThumbsWidth
				};
			});

			_calcCenteringOffset = lang.hitch(this, function(currentThumbs, newThumbs) {
				//calc new offset so that all new thumbs are centered
				var offsetCentered = currentThumbs.width - ((this._widthForThumbs - newThumbs.width) / 2);

				//make sure to not exceed the maxOffset
				var offset = Math.min(offsetCentered, maxOffset);

				return offset;
			});


			//start
			this.pauseAllVideos();

			if (this.isBigThumbnails) {
				////for big thumbs
				this.showThumb(this.shownItemIndex + 1);
			} else {
				////for small thumbs
				var newOffsetIgnoringNavButtons = 0;
				var newIndex;

				//calc new offset and index
				var isGalleryTooSmall = !this.isBigThumbnails && this.widestDefaultThumbWidth + this._galleryThumbMarginExtents >= this._widthForThumbs;
				if (isGalleryTooSmall) {
					newIndex = this.shownItemIndex + 1;
					var thumbOffset = this.defaultThumbOffsets[newIndex];
					newOffsetIgnoringNavButtons = Math.min(thumbOffset, this._smallMaxOffset);
				} else {
					var isCurrentThumbFullyVisible;
					var currentFullyVisibleThumbs = _calcCurrentFullyVisibleThumbs();
					var newFullyVisibleThumbs = _calcNewFullyVisibleThumbs(currentFullyVisibleThumbs);

					newOffsetIgnoringNavButtons = _calcCenteringOffset(currentFullyVisibleThumbs, newFullyVisibleThumbs);
					newIndex = newFullyVisibleThumbs.lastIndex;
				}

				//set the new offset and index
				var newOffsetWithNavButtons = newIndex === this.itemNodes.length -1 ? newOffsetIgnoringNavButtons - ( this._leftNavButtonWidth  * 2) : newOffsetIgnoringNavButtons - this._leftNavButtonWidth;
				var _oldOffset = this._visibleOffset;

				//set transition duration based on distance
				this._setSliderTransitionDuration(newOffsetWithNavButtons, _oldOffset);

				domStyle.set(this.contentSlider.domNode, 'transform', lang.replace('translate3d({0}px, 0, 0)', [newOffsetWithNavButtons * (-1)]));
				domStyle.set(this.contentSlider.domNode, '-webkit-transform', lang.replace('translate3d({0}px, 0, 0)', [(newOffsetWithNavButtons * (-1))]));
				this.contentSliderOffset = newOffsetIgnoringNavButtons;
				this._visibleOffset = newOffsetWithNavButtons;
				this.shownItemIndex = newIndex;

				this._toggleNavButtonsVisibility();
			}
		},

		showPrevThumbs: function() {
			if (this.contentSliderOffset ===  0 || this.shownItemIndex === 0) {
				return;
			}

			//define functions
			var _findFirstFullyVisibleThumb = lang.hitch(this, function() {
				var totalWidth = 0;
				for (var ithumb = 0; ithumb <= this.itemNodes.length -1; ++ithumb) {
					totalWidth += this.defaultThumbWidths[ithumb];

					var isThumbFullyVisible = totalWidth - this.contentSliderOffset >= this.defaultThumbWidths[ithumb] - this._galleryThumbMarginExtents;
					if (isThumbFullyVisible) {
						break;
					}
				}
				return ithumb;
			});

			var _findNextFullyVisibleThumbs = lang.hitch(this, function(ifirstThumb) {
				var firstFullyVisibleThumbIndex = ifirstThumb -1;
				var totalThumbsWidth = 0;

				var tmpWidth = 0;
				var _widthForThumbs = this._widthForThumbs;
				for (var ithumb = firstFullyVisibleThumbIndex; ithumb >= 0; --ithumb) {
					tmpWidth += this.defaultThumbWidths[ithumb];

					if (ithumb === 0) {
						_widthForThumbs += this._leftNavButtonWidth;
					}
					isCurrentThumbFullyVisible = tmpWidth < _widthForThumbs;
					if (!isCurrentThumbFullyVisible) {
						break;
					}
					totalThumbsWidth = tmpWidth;
					firstFullyVisibleThumbIndex = ithumb;
				}
				return {
					width: totalThumbsWidth,
					firstIndex: firstFullyVisibleThumbIndex
				};
			});

			var _calcCenteringOffset = lang.hitch(this, function(newThumbs) {
				var offsetUntilNewThumbs = this.defaultThumbOffsets[newThumbs.firstIndex];
				var newOffsetCentered = offsetUntilNewThumbs - ((this._widthForThumbs - newThumbs.width) / 2);

				//make sure to not go lower than 0
				return Math.max(newOffsetCentered, 0);
			});


			//start
			this.pauseAllVideos();

			if (this.isBigThumbnails) {
				this.showThumb(this.shownItemIndex - 1);
			} else {
				////for small thumbs
				var newOffsetIgnoringNavButtons;
				var newIndex;

				//calc new offset and index
				var isGalleryTooSmall = !this.isBigThumbnails && this.widestDefaultThumbWidth + this._galleryThumbMarginExtents >= this._widthForThumbs;
				if (isGalleryTooSmall) {
					newIndex = this.shownItemIndex-1;
					newOffsetIgnoringNavButtons = this.defaultThumbOffsets[newIndex];
				} else {
					var isCurrentThumbFullyVisible;
					var currFirstFullyVisibleThumbIndex = _findFirstFullyVisibleThumb();
					var newFullyVisibleThumbs = _findNextFullyVisibleThumbs(currFirstFullyVisibleThumbIndex);

					newOffsetIgnoringNavButtons = _calcCenteringOffset(newFullyVisibleThumbs);
					newIndex = newFullyVisibleThumbs.firstIndex;
				}

				//set the new offset and index
				var newOffsetWithNavButtons = newIndex === 0 ? newOffsetIgnoringNavButtons : newOffsetIgnoringNavButtons - this._leftNavButtonWidth;
				var _oldOffset = this._visibleOffset;

				//set transition duration based on distance
				this._setSliderTransitionDuration(newOffsetWithNavButtons, _oldOffset);

				domStyle.set(this.contentSlider.domNode, 'transform', lang.replace('translate3d({0}px, 0, 0)', [(newOffsetWithNavButtons * (-1))]));
				domStyle.set(this.contentSlider.domNode, '-webkit-transform', lang.replace('translate3d({0}px, 0, 0)', [(newOffsetWithNavButtons * (-1))]));
				this.contentSliderOffset = newOffsetIgnoringNavButtons;
				this._visibleOffset = newOffsetWithNavButtons;
				this.shownItemIndex = newIndex;

				this._toggleNavButtonsVisibility();
			}
		},

		_setSliderTransitionDuration: function(newOffset, oldOffset) {
			var offsetDistance = Math.abs(oldOffset - newOffset);
			var isNewTransitionDuration = offsetDistance > this._baseTransitionDuration;
			if (isNewTransitionDuration) {
				domStyle.set(this.contentSlider.domNode, 'transition-duration', lang.replace('{0}ms', [offsetDistance]));
				setTimeout(lang.hitch(this, function() {
					domStyle.set(this.contentSlider.domNode, 'transition-duration', '');
				}), offsetDistance);
			}
		},

		_hideVideosTemporarily: function(duration) {
			//hide loaded youtube iframes during resize for performance reasons
			query('.galleryVideoThumb.loaded .galleryVideoThumbnailWrapper', this.contentSlider.domNode).removeClass('dijitDisplayNone');
			query('.galleryVideoThumb.loaded .galleryVideo', this.contentSlider.domNode).addClass('dijitDisplayNone');
			setTimeout(lang.hitch(this, function() {
				query('.galleryVideoThumb.loaded .galleryVideo', this.contentSlider.domNode).removeClass('dijitDisplayNone');
				query('.galleryVideoThumb.loaded .galleryVideoThumbnailWrapper', this.contentSlider.domNode).addClass('dijitDisplayNone');
			}), duration);
		},

		toggleThumbSize: function(newIndex) {
			newIndex = (newIndex === undefined) ? this.shownItemIndex : newIndex;

			var _isBigThumbnails = this.isBigThumbnails;
			this.isBigThumbnails = !this.isBigThumbnails;
			if (_isBigThumbnails) {
				this._toggleToSmallThumbs();
			} else {
				this._toggleToBigThumbs(newIndex);
			}

			domClass.toggle(this.scaleButton, 'minimize');

			this.showThumb(newIndex);
		},

		_toggleToSmallThumbs: function() {
			this._hideVideosTemporarily(this._baseTransitionDuration + 50);
			//remove height and width for thumbs and navButtons
			query('.galleryNavButton', this.outerContainer.domNode).style('height', '');
			query('.galleryThumb', this.contentSlider.domNode).style('width', '').style('height', '');
		},

		_toggleToBigThumbs: function(newIndex) {
			this.pauseAllVideos(newIndex);

			this.centerScrollGallery();

			this._resizeNavButtons();
		},

		_resizeNavButtons: function() {
			//enlarge navButtons and VerticalAlignHelperThumb
			var maxHeight = Math.max(this._bigThumbDimensions.maxHeightForImgThumb, this._bigThumbDimensions.maxHeightForVideoThumb, this.defaultThumbHeight);
			query('.galleryNavButton', this.outerContainer.domNode).style('height', lang.replace('{0}px', [maxHeight]));
			domStyle.set(this.galleryThumbVerticalAlignHelper, 'height', lang.replace('{0}px', [maxHeight]));
		},

		centerScrollGallery: function() {
			var height;
			if (this.isBigThumbnails) {
				//+15px from the stickyheader
				height = ((window.innerHeight - Math.max(this._bigThumbDimensions.maxHeightForImgThumb, this._bigThumbDimensions.maxHeightForVideoThumb)) /2) + 15;
			} else {
				height = ((window.innerHeight - this.defaultThumbHeight) / 2) + 15;
			}
			domStyle.set(this._scrollTarget, 'height', height + 'px');
			domStyle.set(this._scrollTarget, 'top', '-' + height + 'px');

			dojox.fx.smoothScroll({node: this._scrollTarget, win: window, duration: 400}).play();
		},

		_getMaxWidthHeightForBigThumbs: function() {
			//##get max width for a big thumb
			var maxWidthForThumb = this._widthForThumbs - this._galleryThumbMarginExtents;

			//##get the max height for a big thumb
			var maxHeight = dojo.window.getBox().h - 100;
			maxHeight = (maxHeight < this.defaultThumbHeight) ? this.defaultThumbHeight : maxHeight;
			var maxHeightForImgThumb = Math.min(maxWidthForThumb / this.heighestImgRatio, maxHeight, this.heighestImg.h);
			var maxHeightForVideoThumb = maxWidthForThumb / (this._youtubeIframeRatio);

			return {
				maxWidthForThumb: maxWidthForThumb, 
				maxHeightForImgThumb: maxHeightForImgThumb, 
				maxHeightForVideoThumb: maxHeightForVideoThumb
			};
		},

		_handleResize: function() {
			if (domGeometry.getMarginBox(this.domNode).w === 0) {
				return;
			}
			if (this._resizeDeferred && !this._resizeDeferred.isFulfilled()) {
				this._resizeDeferred.cancel();
			}

			this._resizeDeferred = tools.defer(lang.hitch(this, function() {
				this.resizeGallery();

				this._removeLoadingScreen();
			}), 200);

			this._resizeDeferred.otherwise(function() { /* prevent logging of exception */ });
		},

		_removeLoadingScreen: function() {
			if (!this.loaded) {
				//fade the loadingAnimationOverlay out over given transition duration
				var transitionDuration = 600;
				domStyle.set(this.galleryLoadingOverlay, 'transition', lang.replace('opacity {0}ms', [transitionDuration]));
				domClass.add(this.galleryLoadingOverlay, 'loaded');
				domClass.add(this.contentSlider.domNode, 'noTransition');
				domStyle.set(this.contentSlider.domNode, 'transform', lang.replace('translate3d({0}px, 0, 0)', [this._leftNavButtonWidth]));
				domStyle.set(this.contentSlider.domNode, '-webkit-transform', lang.replace('translate3d({0}px, 0, 0)', [this._leftNavButtonWidth]));

				//hide the loading overlay after transition duration
				tools.defer(lang.hitch(this, function() {
					domClass.add(this.galleryLoadingOverlay, 'dijitDisplayNone');
					domClass.remove(this.contentSlider.domNode, 'noTransition');
				}), transitionDuration);

				//remove styles needed for loading overlay
				domStyle.set(this.domNode, 'height', '');
				domStyle.set(this.domNode, 'overflow', '');

				domClass.remove(this.scaleButton, 'dijitDisplayNone');
				this.loaded = true;
			}
		},

		startup: function() {
			this.inherited(arguments);
			this.own(on(baseWin.doc, 'resize', lang.hitch(this, '_handleResize')));
			this.own(on(kernel.global, 'resize', lang.hitch(this, '_handleResize')));
			require(["dojox/fx/scroll"]);
		},

		destroy: function() {
			this.inherited(arguments);

			clearInterval(this._firstResizeInterval);

			//remove all inserted CssRules
			array.forEach(this._insertedCssRules, function(rule) {
				styles.removeCssRule(rule.selector, rule.declaration);
			});
		},

		pauseAllVideos: function(pauseExceptionIndex) {
			if (Object.keys(this.playingVideos).length === 0) {
				return;
			}
			
			//pause all playing videos
			//if a pauseExceptionIndex is given do not pause that video if it is playing
			tools.forIn(this.playingVideos, lang.hitch(this, function(_videoId, player) {
				if (this.videoIdToThumbIndex[_videoId] !== pauseExceptionIndex) {
					player.pauseVideo();
				}
			}));
		}, 
	});
});
