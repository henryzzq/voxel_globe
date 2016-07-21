/*
 * The Tie point editor is the main class for an individual OL3 imageviewer
 */

function EventTriggerEditor(imageContainerDivName, editorCount) {
	this.planetDivName = "planetWrapper" + editorCount;
	this.divName = "imageWrapper" + editorCount;
	this.toolbarDivName = "imageToolbar" + editorCount;
	this.imageDivName = "image" + editorCount;
	this.imageNameField = "imageName" + editorCount;
	this.bannerDivName = "imgBanner" + editorCount;
	this.containerDivName = imageContainerDivName;
	this.editorId = editorCount;
	this.img = null;
	this.isInitializing = false;

	var divText = '<div id="' + this.planetDivName + '" class="planetWidget">' +
			'<div id="' + this.divName + '" class="imageWidget"><div id="' + this.imageDivName
			+ '" class="imageContents"></div><div id="' + this.toolbarDivName
			+ '" class="imageToolbar"></div></div>' +
			'<div id="' + this.bannerDivName + '" class="imgBanner"></div></div>';
	$('#' + imageContainerDivName).append(divText);

	$('#' + this.bannerDivName).html('<img src="' + iconFolderUrl + 'planet.svg">' + 
		'<div class="p1">Includes material ©2016 Planet Labs Inc. All rights reserved.</div>' +
		'<div class="p2">DISTRIBUTION STATEMENT C: Distribution authorized to U.S. Government Agencies and their contractors (Administrative or Operational Use) Other requests for this document shall be referred to AFRL/RYAA, Wright-Patterson Air Force Base, OH 45433-7321.</div>');

  	this.initializeContainerSize();
  	this.bannerHeight += 5;
  	this.imageHeight -= 5;
  	
  	console.log("STARTUP: Banner height " + this.bannerHeight + " image height " + this.imageHeight);
// 	var that = this;
// 	$('#' + this.bannerImageId).load(function(e) {
// 		var bheight = $('#' + that.bannerDivName).height();
// 		var cheight = $('#' + that.containerDivName).height();
// //		document.getElementById(that.imageId);
// 		$('#' + that.divName).css("height", (cheight - bheight));
// 		console.log("Adjusting height of " + that.divName + " to " + (cheight - bheight));
// 	});

}

EventTriggerEditor.prototype.initialize = function(img) {
	if (this.isInitialzing) {
		return;
	}
	this.isInitializing = true;
	console.log("Initializing image " + img.name);

  	this.initializeContainerSize();
  	console.log("Banner height " + this.bannerHeight + " image height " + this.imageHeight);
	$('#' + this.divName).css("height", this.imageHeight + "px");
	$('#' + this.imageDivName).html("");
	$('#' + this.toolbarDivName).html("");
	$('#' + this.toolbarDivName).toggle(true);
	$('#' + this.bannerDivName).toggle(true);
	$('#' + this.planetDivName).toggle(true);

	this.imgWidth = img.width;
	this.imgHeight = img.height;
	this.imgUrl = img.url;
	this.img = img;

	var imgWidth = this.imgWidth;
	var imgHeight = this.imgHeight;
	this.imgName = img.name;
	var url = this.imgUrl;
	var crossOrigin = 'anonymous';
	var that = this;
	this.selectedFeature = null;

	var imgCenter = [ imgWidth / 2, -imgHeight / 2 ];

	// Maps always need a projection, but Zoomify layers are not geo-referenced,
	// and
	// are only measured in pixels. So, we create a fake projection that the map
	// can use to properly display the layer.
	var proj = new ol.proj.Projection({
		code : 'ZOOMIFY',
		units : 'pixels',
		extent : [ 0, 0, imgWidth, imgHeight ]
	});

	//Zoomify image source
	var imgsource = new ol.source.Zoomify({
		url : url,
		size : [ imgWidth, imgHeight ],
		crossOriginKeyword : crossOrigin
	});

	//Creates the actual layer to get rendered, for tiled images
	var imgtile = new ol.layer.Tile({
		source : imgsource
	});

	//a vector of features, start with no features
	this.drawsource = new ol.source.Vector();

  //Styles for tie points
	var inactiveStyle = new ol.style.Style({
		image : new ol.style.Circle({
			radius : 7,
			stroke : new ol.style.Stroke({
				color : INACTIVE_COLOR,
				width : 3
			})
		})
	});
	var activeStyle = new ol.style.Style({
		image : new ol.style.Circle({
			radius : 7,
			stroke : new ol.style.Stroke({
				color : ACTIVE_COLOR,
				width : 3
			})
		})
	});
	
	//Creates the actual layer to get rendered, for tiled images
	var vector = new ol.layer.Vector({
		source : that.drawsource,
		style : inactiveStyle
	});

  //This seems to handle events on the entire map, not just a feature?
	this.select = new ol.interaction.Select({
		condition : ol.events.condition.singleClick,
		addCondition : ol.events.condition.singleClick,
		removeCondition : ol.events.condition.never,
		toggleCondition : ol.events.condition.never,
		style : activeStyle
	});

	this.modify = new ol.interaction.Modify({
		features : that.select.getFeatures(),
		style : activeStyle
	});

	this.modify.on('modifyend', function(e) {	
		mainViewer.completeTiePointEdit();
	});

	this.map = new ol.Map({
		interactions : ol.interaction.defaults().extend(
				[ that.select, that.modify ]),
		layers : [ imgtile, vector ],
		target : this.imageDivName,
		controls : [], // Disable default controls
		view : new ol.View({
			projection : proj,
			center : imgCenter,
			zoom : 1
		})
	});
	//I have NO clue what I'm doing here https://groups.google.com/forum/#!topic/ol3-dev/SEu5Js8OurU
  this.map.renderSync();
  //If I don't do this, coordinate will turn up null deep in ol because the mapping of
  //pixels to coordinates is not yet initialized. This then breaks a lot of code
  //By renderSync here, the pixel conversion code works and everything is happy.
}

EventTriggerEditor.prototype.blank = function() {
	this.img = null;
	this.isInitializing = false;
	this.editorState = {};
	$('#' + this.imageDivName).html("");
	$('#' + this.toolbarDivName).toggle(false);
	$('#' + this.planetDivName).toggle(false);
//	$('#' + this.bannerDivName).hide();
	// $('#' + this.divName).toggle(false);
}

EventTriggerEditor.prototype.show = function(width, height, scale) {
	$('#' + this.planetDivName).css("height", '100%');
	$('#' + this.planetDivName).css("width", width + '%');
	$('#' + this.bannerDivName).css("font-size", scale + '%');
	$('#' + this.planetDivName).toggle(true);
}

EventTriggerEditor.prototype.hide = function() {
	$('#' + this.planetDivName).toggle(false);
}

EventTriggerEditor.prototype.initializeContainerSize = function() {		
	// $('#' + this.bannerDivName).html('<img src="' + iconFolderUrl + 'planet.svg">' + 
	// 	'<div class="p1">Includes material ©2016 Planet Labs Inc. All rights reserved.</div>' +
	// 	'<div class="p2">DISTRIBUTION STATEMENT C: Distribution authorized to U.S. Government Agencies and their contractors (Administrative or Operational Use) Other requests for this document shall be referred to AFRL/RYAA, Wright-Patterson Air Force Base, OH 45433-7321.</div>');

	var bheight = document.getElementById(this.bannerDivName).clientHeight;
	if (bheight > 0) {
		this.bannerHeight = bheight;
	}

	var cheight = $('#editorContentDiv').height();
	this.imageHeight = cheight - this.bannerHeight;
}

EventTriggerEditor.prototype.getDebugInfo = function() {
	if (this.map) {
		var center = this.map.getView().getCenter();
		var zoom = this.map.getView().getZoom();
		
		return "Center - " + center + " Zoom - "+ this.map.getView().getZoom() + "<br>";
	} else {
		return "No image displayed.<br>";
	}
}

