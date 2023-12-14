$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

// Activated when user attempts to create a new playlist
$('#createBtn').click(function() {
    // Get all elements within the div with the ID selectedItems
    const selectedItems = document.getElementById('selectedItems').querySelectorAll('[data-id]');

    // Iterate through the elements and access their data-id attribute
    var counter = 0;
    var data = {};
    data['update'] = $('#updates').is(':checked');

    selectedItems.forEach(item => {
        const dataId = item.getAttribute('data-id');
        data[counter] = dataId;
        counter++;
    });
    data['seed_count'] = counter;

    // Make sure at least one track or artist was entered
    if (counter == 0) {
        alert('A minimum of one track or artist must be entered to create the playlist.');
    } else {
        // Get only slider values that are checked
        const sliders = document.querySelectorAll('.slider-range');
        sliders.forEach(slider => {
            const sliderName = slider.getAttribute('name');
            const sliderValue = slider.value;
            if (slider.disabled == false) {
                data[sliderName] = sliderValue;
                counter++;
            }
            // Reset slider values to default
            if (sliderName == 'slider_popularity') {
                slider.value = 50;
            } else if (sliderName == 'slider_limit') {
                slider.value = 25;
            } else {
                slider.value = 0.5;
            }
        });
        
        // Reset slider values to default
        const slider_values = document.querySelectorAll('.slider-value');
            slider_values.forEach(slider => {
                if (slider.getAttribute('name') === 'popularity_val') {
                    slider.innerHTML = 50;
                } else if (slider.getAttribute('name') === 'limit_val') {
                    slider.innerHTML = 25;
                } else {
                    slider.innerHTML = 0;
                }
        });

        // Reset checkbox values to default
        const checkboxes = document.querySelectorAll('.form-check-input');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.parentNode.nextElementSibling.firstElementChild.disabled = true;
        });

        // remove all items from the selectedItems div
        $('#selectedItems').empty();

        data['name'] = $('#playlist-name').val();

        // Reset playlist name to default
        $('#playlist-name').val('cafégram recs :)');

        // make ajax call to create playlist
        $.ajax({
            url: '/recommend',
            type: 'POST',
            data: data,
            success: function(response) {
                // console.log(response);
                window.location.href = response['playlist_uri'];
            },
            error: function(error) {
                console.log(error);
            }
        })
    }

});

// Show/hide sliders when attributes in form are selected/unselected
$('input.form-check-input').change(function(){
    if ($(this).is(':checked')) {
        $(this).parent().next().find('.slider-range').prop('disabled', false);
    }
    else {
        $(this).parent().next().find('.slider-range').prop('disabled', true);
    }
}).change();

// Show value of slider next to slider bar
const $limitVal = $('#sliderLimitValue');
const $limitRange = $('#sliderLimitRange');
$limitVal.html($limitRange.val());
$limitRange.on('input change', () => {
    $limitVal.html($limitRange.val());
});

// Show value of slider next to slider bar
const $acousticVal = $('#sliderAcousticValue');
const $acousticRange = $('#sliderAcousticRange');
$acousticVal.html($acousticRange.val());
$acousticRange.on('input change', () => {
    $acousticVal.html($acousticRange.val());
});

// Show value of slider next to slider bar
const $danceabilityVal = $('#sliderDanceabilityValue');
const $danceabilityRange = $('#sliderDanceabilityRange');
$danceabilityVal.html($danceabilityRange.val());
$danceabilityRange.on('input change', () => {
    $danceabilityVal.html($danceabilityRange.val());
});

// Show value of slider next to slider bar
const $instrumentalVal = $('#sliderInstrumentalValue');
const $instrumentalRange = $('#sliderInstrumentalRange');
$instrumentalVal.html($instrumentalRange.val());
$instrumentalRange.on('input change', () => {
    $instrumentalVal.html($instrumentalRange.val());
});

// Show value of slider next to slider bar
const $livelyVal = $('#sliderLivelyValue');
const $livelyRange = $('#sliderLivelyRange');
$livelyVal.html($livelyRange.val());
$livelyRange.on('input change', () => {
    $livelyVal.html($livelyRange.val());
});

// Show value of slider next to slider bar
const $energyVal = $('#sliderEnergyValue');
const $energyRange = $('#sliderEnergyRange');
$energyVal.html($energyRange.val());
$energyRange.on('input change', () => {
    $energyVal.html($energyRange.val());
});

// Show value of slider next to slider bar
const $popularityVal = $('#sliderPopularityValue');
const $popularityRange = $('#sliderPopularityRange');
$popularityVal.html($popularityRange.val());
$popularityRange.on('input change', () => {
    $popularityVal.html($popularityRange.val());
});

// Show value of slider next to slider bar
const $speechVal = $('#sliderSpeechValue');
const $speechRange = $('#sliderSpeechRange');
$speechVal.html($speechRange.val());
$speechRange.on('input change', () => {
$speechVal.html($speechRange.val());
});

// Show value of slider next to slider bar
const $valenceVal = $('#sliderValenceValue');
const $valenceRange = $('#sliderValenceRange');
$valenceVal.html($valenceRange.val());
$valenceRange.on('input change', () => {
    $valenceVal.html($valenceRange.val());
});

// Autocomplete search
$(document).ready(function() {
    $('#search-input').autocomplete({
        source: function(request, response) {
            // console.log('request: ', request.term)
            // console.log('response: ', response)

            $.getJSON('/api/autocomplete', {
                query: request.term,
                type: 'create'
            }, function(data) {
                response(data);
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $('#search-input').val('');
            createSelected(ui.item.label, ui.item.value);
            return false;
        }
    });
});

// Show user selected track and artist names
function createSelected (label, value) {
    // Check if the data-id already exists
    if ($('#selectedItems').find('[data-id="' + value + '"]').length === 0) {
        // Check if the number of items is less than 5
        if ($('#selectedItems').children().length < 5) {
            // Append new item if conditions are met
            $('#selectedItems').append('<a class="list-group-item"><span data-id="' + value + '">' + label + '</span><span><span class="btn btn-xs btn-default" style="float: right;" onclick="removeSelected(this);">&times;</span></span></a>');
        } else {
            // If the maximum number of items (5) is reached, show an alert
            alert('You can only select up to 5 items.');
        }
    } else {
        // If the data-id already exists, show an alert
        alert('This item is already selected.');
    }
};

// Remove user selected track and artist names
removeSelected = function(span) {
    span.parentNode.parentNode.remove();
};
