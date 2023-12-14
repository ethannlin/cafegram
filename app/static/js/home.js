const track = {
    name: "",
    album: {
        images: [
            { url: "" }
        ]
    },
    artists: [
        { name: "" }
    ]
}

// Get the access token and expiration time from the server
let accessToken = token;
let expirationTime = expires_in;

const tokenRefreshThreshold = 300; // Threshold in seconds

// Function to refresh the token via AJAX
function refreshAccessToken() {
    $.ajax({
        url: '/api/refresh', // Your server-side endpoint to refresh the token
        type: 'POST',
        success: function(response) {
            // Handle success response from the API if needed
            accessToken = response['token'];
            expirationTime = Math.floor(Date.now() / 1000) + response['expires_in'];
        },
        error: function(error) {
            // Handle errors if the API call fails
            console.error('Error refreshing token:', error);
        }
    });
}

// Function to check if the token is expired or needs refreshing
function tokenNeedsRefresh() {
    const currentTime = Math.floor(Date.now() / 1000); // Current time in seconds
    return !expirationTime || currentTime >= expirationTime - tokenRefreshThreshold;
}

// Function to ensure that the token is always valid before using it
function ensureValidToken(cb) {
    if (tokenNeedsRefresh()) {
        refreshAccessToken();
        console.log('Access token refreshed');
    }
    cb(accessToken);
}

// Spotify Web Playback SDK
window.onSpotifyWebPlaybackSDKReady = () => {
    const player = new Spotify.Player({
        name: 'cafégram',
        getOAuthToken: cb => {
            ensureValidToken(cb);
        },
        volume: 0.5
    });


    // Ready
    player.addListener('ready', ({ device_id }) => {
        console.log('Ready with Device ID', device_id);

        // transfer playback 
        const endpointURL = `/api/transfer/${device_id}`;
        $.ajax({
            url: endpointURL,
            type: 'PUT', 
            success: function(response) {
                // Handle success response from the API if needed
                console.log(response);
                $('#spotify-connect').hide();
                $('.player-container').show();
            },
            error: function(error) {
                // Handle errors if the API call fails
                console.error('Error transferring playback:', error);
            }
        });
    });

    // Not Ready
    player.addListener('not_ready', ({ device_id }) => {
        console.log('Device ID has gone offline', device_id);
    });

    player.addListener('initialization_error', ({ message }) => {
        console.error(message);
    });

    player.addListener('authentication_error', ({ message }) => {
        console.error(message);
    });

    player.addListener('account_error', ({ message }) => {
        console.error(message);
    });

    document.getElementById('prevTrack').onclick = function() {
    player.previousTrack();
    };

    document.getElementById('togglePlay').onclick = function() {
    player.togglePlay();
    };

    document.getElementById('nextTrack').onclick = function() {
    player.nextTrack();
    };

    // Playback status updates
    let track_duration = 0;
    function update_track_duration(duration) {
        track_duration = duration;
        $('#postion-slider').val(0);
    }

    // Add an event listener to handle slider input
    $('#postion-slider').on('input', function() {
        const position_percent = $(this).val();
        const position_ms = position_percent / 100 * track_duration;
        player.seek(position_ms);
    });
    
    // Check state every second
    setInterval( function() {
        player.getCurrentState().then(state => {
            if (!state) {
                return;
            }
            const position = state.position;
            const duration = state.duration;
            const position_percent = position / duration * 100;
            $('#postion-slider').val(position_percent);
        });
    }, 1000)

    // Update Track everytime it changes
    player.addListener('player_state_changed', state => {
        track.name = state.track_window.current_track.name;
        track.album.images[0].url = state.track_window.current_track.album.images[0].url;
        track.artists[0].name = state.track_window.current_track.artists[0].name;

        const shuffle = state.shuffle;
        const repeat = state.repeat_mode;
        const duration = state.duration;

        // Update button text based on playback state
        const isPlaying = !state.paused;
        $('#togglePlay').html(isPlaying ? '<span class="glyphicon glyphicon-pause"></span>' : '<span class="glyphicon glyphicon-play"></span>');
        
        // Update track information
        $('#track-info').text(state.track_window.current_track.name + ' by ' + state.track_window.current_track.artists[0].name);
        $('#album-art').attr('src', state.track_window.current_track.album.images[0].url);

        // Update shuffle and repeat button styles
        if (shuffle) {
            $('#shuffle').css('font-weight', 'bold');
        } else {
            $('#shuffle').css('font-weight', 'normal');
        }
        
        if (repeat === 0) {
            $('#repeat').css('font-weight', 'normal');
            $('#repeat').css('text-decoration', 'none');
        } else if (repeat === 1) {
            $('#repeat').css('font-weight', 'bold');
            $('#repeat').css('text-decoration', 'none');
        } else if (repeat === 2) {
            $('#repeat').css('font-weight', 'bold');
            $('#repeat').css('text-decoration', 'underline');
        }

        // update position slider
        if (duration != track_duration) {
            update_track_duration(duration);
        }
    });

    player.connect().then(success => {
        if (success) {
            console.log('The Web Playback SDK successfully connected to Spotify!');
            
            // Volume slider change event
            $('#volume-slider').on('input', function() {
                const volumeValue = $(this).val() / 100; // Normalize volume to a value between 0 and 1
                if (volumeValue > 0.5) {
                    $('#volume').removeClass('glyphicon glyphicon-volume-down');
                    $('#volume').addClass('glyphicon glyphicon-volume-up');
                } else if (volumeValue <= 0.5 && volumeValue > 0) {
                    $('#volume').removeClass('glyphicon glyphicon-volume-up');
                    $('#volume').addClass('glyphicon glyphicon-volume-down');
                } else if (volumeValue === 0) {
                    $('#volume').removeClass('glyphicon glyphicon-volume-down');
                    $('#volume').addClass('glyphicon glyphicon-volume-off');
                }
                player.setVolume(volumeValue).then(() => {
                    console.log('Volume updated');
                });
            });
        }
    });

    window.onbeforeunload = function() {
        player.disconnect();
    };
}

// Toggle shuffle
$('#shuffle').on('click', function() {
    // Get shuffle font weight
    const shuffleFontWeight = $(this).css('font-weight');

    if (shuffleFontWeight === '700') {
        state=false;
    } else {
        state=true;
    }

    // Construct the URL based on the state
    const endpointURL = `/api/shuffle/${state}`;

    // Make an AJAX request to toggle the shuffle
    $.ajax({
        url: endpointURL,
        type: 'PUT', 
        success: function(response) {
            // Handle success response from the API if needed
            console.log(response);
        },
        error: function(error) {
            // Handle errors if the API call fails
            console.error('Error toggling shuffle:', error);
        }
    });
        
});

// Toggle repeat
$('#repeat').on('click', function() {
    // Get repeat properties
    const repeatFontWeight = $(this).css('font-weight');
    const repeatTextDecoration = $(this).css('text-decoration');

    if (repeatFontWeight === '400') {
        state='context';
    } else if (repeatFontWeight === '700' && repeatTextDecoration.includes('none')) {
        state='track';
    } else if (repeatFontWeight === '700' && repeatTextDecoration.includes('underline')) {
        state='off';
    }

    // Construct the URL based on the state
    const endpointURL = `/api/repeat/${state}`;

    // Make an AJAX request to toggle the repeat
    $.ajax({
        url: endpointURL,
        type: 'PUT', 
        success: function(response) {
            // Handle success response from the API if needed
            console.log(response);
        },
        error: function(error) {
            // Handle errors if the API call fails
            console.error('Error toggling repeat:', error);
        }
    });
});

// Autocomplete search
$(document).ready(function() {
    $('#search-input').autocomplete({
        source: function(request, response) {
            // console.log('request: ', request.term)
            // console.log('response: ', response)

            $.getJSON('/api/autocomplete', {
                query: request.term,
                type: $('#search-type').val()
            }, function(data) {
                response(data);
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $(this).val(ui.item.label); 
            
            // Construct the URL based on the selected item
            endpointURL = `/api/play/${$('#search-type').val()}/${ui.item.value}`;
            
            // Make an AJAX request to play the selected item
            $.ajax({
                url: endpointURL,
                type: 'PUT', 
                success: function(response) {
                    // Handle success response from the API if needed
                    console.log(response);
                },
                error: function(error) {
                    // Handle errors if the API call fails
                    console.error('Error playing track:', error);
                }
            });

            return false;
        }
    });
});