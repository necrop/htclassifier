/* General-purpose functions loaded for every page */

$(document).ready( function() {

	//========================================================
	// Update quicksearch mode (lemma or headword)
	//========================================================

	if (sessionStorage['htc_quicksearchMode'] == null) {
		sessionStorage['htc_quicksearchMode'] = 'headword';
	}
	changeQuicksearchMode(sessionStorage['htc_quicksearchMode']);


	//========================================================
	// popovers
	//========================================================

	$("a[rel='popover']").popover({trigger: 'hover', placement: 'right'});
	$("a[rel='popover-below']").popover({trigger: 'hover', placement: 'bottom'});


	//========================================================
	// functions for opening/closing the list of deprecated classifications in results pages
	//========================================================

	var editmode = $('body').attr('editmode');
	if (editmode === 'off') {
		$('.deprecatedOpen').hide();
	}
	else {
		$('.deprecatedClosed').hide();
		$('.deprecatedOpen').show();
	}

	$('.deprecatedClosed a').click( function(event) {
		$(this).closest('.deprecatedClosed').hide();
		$(this).closest('.deprecatedContainer').find('.deprecatedOpen').show();
		event.preventDefault();
	});

	$('.deprecatedOpen > a').click( function(event) {
		$(this).closest('.deprecatedOpen').hide();
		$(this).closest('.deprecatedContainer').find('.deprecatedClosed').show();
		event.preventDefault();
	});


	//========================================================
	// functions relating to checkbox selectors
	//========================================================

	$('a.checkboxButton').click( function (event) {
		var thesclass_container = $(this).closest('.thesclass');
		var existing_classes = $(this).attr('class');
		var status_code = $(this).attr('value');
		var wrapper = $(this).closest('.btn-group');

		// First remove any existing highlighting from all buttons in the group
		wrapper.children('a.btn').removeClass('btn-danger btn-warning btn-success');

		// ...then add highlighting to the button that was clicked
		var highlight_class;
		if (status_code === 'c') {
			highlight_class = 'btn-success';
		} else if (status_code === 'p') {
			highlight_class = 'btn-warning';
		} else if (status_code === 'i') {
			highlight_class = 'btn-danger';
		}
		// Check that the highlighting for this button is currently *off*
		if (existing_classes.indexOf(highlight_class) === -1) {
			$(this).addClass(highlight_class);
		}
		else {
			// If the button has been clicked to turn the existing highlighting *off*,
			//  then then status code should be set to 'u' for 'unset'
			status_code = 'u';
		}

		// Send request to the server to update the thesaurus class's status value
		var sense_id = thesclass_container.attr('senseid');
		var count = thesclass_container.attr('thesclasscount');
		var argument_string = 'id=' + sense_id + '&count=' + count + '&value=' + status_code;
		$.get(update_checkbox_ajax_url, argument_string);

		event.preventDefault();
	});


	$('.quicksearchswitch a').click( function (event) {
		var mode;
		if ($(this).text() === 'Search by lemma') {
			mode = 'lemma';
		} else {
			mode = 'headword';
		}
		changeQuicksearchMode(mode);
		// Update session info (so that this setting persists)
		sessionStorage['htc_quicksearchMode'] = mode;
		event.preventDefault();
	});

	$('a.changeclass').click( function (event) {
		showClasschangeModal($(this));
		event.preventDefault();
	});
});


function changeQuicksearchMode(mode) {
	// mode should be 'lemma' or 'headword'
	// Change the name of the input box (lemma/headword)
	$('.quicksearchinput').attr('name', mode);
	// Update the text of input box's label
	$('.quicksearchmode').html('<span class="caret"></span> ' + mode.charAt(0).toUpperCase() + mode.slice(1) + ':');
}



//--------------------------------------------------------------
// Modal used for changing class (in sense view only)
//--------------------------------------------------------------

function showClasschangeModal(node) {
	var thesclass_container = node.closest('.thesclass');
	var senseid = thesclass_container.attr('senseid');
	var count = thesclass_container.attr('thesclasscount');
	var classid = node.attr('classid');

	// Fill in the local-context tree
	var tree_container = $('#classChangeModalTree');
	tree_container.attr('senseid', senseid)
	tree_container.attr('count', count)
	$('#classchangeModal').modal({show: true});
	populateModalSenseDetails(senseid);
	populateModalTree(classid, classid);

	// Fill in the hidden values in the form
	var form = $('#classchangeModalForm');
	form.find('input[name="senseid"]').attr('value', senseid);
	form.find('input[name="count"]').attr('value', count);
	form.find('input[name="classid"]').attr('value', '');
}

function populateModalSenseDetails(senseid) {
	var url = sensedetails_ajax_url.replace('999', senseid);
	$.getJSON(url, {}, function(json) {
		$('#classChangeModalHeader').text(json.lemma);
		$('#classChangeModalDefinition').text(json.definition);
		$('#classChangeModalSenselink').attr('href', json.link);
	});
}

function populateModalTree(currentid, centralid) {
	var tree_container = $('#classChangeModalTree');
	var count = tree_container.attr('count');
	var senseid = tree_container.attr('senseid');
	var url = localtree_ajax_url
		.replace('/9/', '/' + senseid + '/')
		.replace('/8/', '/' + currentid + '/')
		.replace('/7/', '/' + centralid + '/')
		.replace('/0/', '/' + count + '/');
	$.get(url, {}, function(data) {
		tree_container.html(data);
		setModalListeners(tree_container);
	}, 'html');

}

function setModalListeners(tree_container) {
	tree_container.find('a.centreclass').click( function (event) {
		var currentid = $(this).attr('currentid');
		var centralid = $(this).attr('centralid');
		populateModalTree(currentid, centralid);
		event.preventDefault();
	});
}