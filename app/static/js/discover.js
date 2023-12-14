$('#createBtn').click(function() {

    check1 = $('#shortTerm').is(':checked');
    check2 = $('#mediumTerm').is(':checked');
    check3 = $('#longTerm').is(':checked');

    if (!check1 && !check2 && !check3) {
        alert('Please select at least one time period to create a playlist.');
        return;
    }

    var form = $('#playlist-form');
    var data = form.serialize();
    $.ajax({
        url: '/discover/create-playlist',
        type: 'POST',
        data: data,
        success: function(response) {
            window.location.href = response['playlist_uri'];
        },
        error: function(error) {
            console.log(error);
        }
    });

    // clear form
    $('#shortTerm').prop('checked', false);
    $('#mediumTerm').prop('checked', false);
    $('#longTerm').prop('checked', false);
    $('#shortTermName').val('top tracks last month');
    $('#mediumTermName').val('top tracks 6 months');
    $('#longTermName').val('top tracks all time');
    $('#updates').prop('checked', false);
    $('#updateCode').val('');
});