// Get the modal
var modal = document.getElementById("timerModal");

// Get the button that opens the modal
var btn = document.getElementById("pomodoroTimer");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// Define timerInterval variable
var timerInterval;

// Define audio variable
var audio = document.getElementById("alarmSound");

// When the user clicks the button, open the modal
btn.onclick = function (e) {
    e.preventDefault();
    modal.style.display = "block";
};

// When the user clicks on <span> (x), close the modal
span.onclick = function () {
    modal.style.display = "none";
};

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
};

document.getElementById("minutes").addEventListener("keydown", function (e) {
    // Check if more than 3 digits are already entered
    if (
        this.value.length >= 3 &&
        /^\d$/.test(e.key) &&
        !["Backspace", "Delete", "ArrowLeft", "ArrowRight"].includes(e.key)
    ) {
        e.preventDefault();
    }

    // Allow: backspace, delete, tab, escape, enter, and numeric digits
    if (
        ["Backspace", "Delete", "Tab", "Escape", "Enter"].includes(e.key) ||
        // Allow: Ctrl+A, Ctrl+C, Ctrl+X
        ((e.key === "a" || e.key === "c" || e.key === "x") &&
            (e.ctrlKey || e.metaKey)) ||
        // Allow: navigation keys (arrows, home, end)
        e.key === "ArrowLeft" ||
        e.key === "ArrowRight" ||
        e.key === "ArrowUp" ||
        e.key === "ArrowDown" ||
        e.key === "Home" ||
        e.key === "End"
    ) {
        // Let it happen, don't do anything
        return;
    }

    // Ensure that it is a number and stop the keypress
    if (!/^\d$/.test(e.key)) {
        e.preventDefault();
    }
});

document.getElementById("minutes").addEventListener("blur", function (e) {
    if (this.value.length === 0) {
        this.value = 25;
    }
});

document.getElementById("minutes").addEventListener("focus", function (e) {
    if (this.value.length !== 0) {
        this.value = "";
    }
});

function setCookie(name, value, days) {
    var expires = "";
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(";");
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) === " ") c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0)
            return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function clearCookie(name) {
    document.cookie =
        name + "=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;";
}

function checkTimer() {
    var startTime = parseInt(getCookie("pomodoroStartTime"));
    var duration = parseInt(getCookie("pomodoroDuration"));

    if (startTime && duration) {
        var currentTime = Date.now();
        var timeElapsed = currentTime - startTime;
        timeElapsed = Math.floor(timeElapsed / 1000);
        var remainingTime = duration - timeElapsed;

        if (remainingTime > 0) {
            // Continue the timer with remainingTime
            var display = document.getElementById("pomodoroTimer");
            var modalContent = document.getElementById("timer-display");
            modalContent.style.display = "block";
            document.getElementById("startTimer").textContent = "stop";
            // Call startTimer with the remaining time
            startTimer(remainingTime, display, modalContent);
        } else {
            // Timer has finished
            clearInterval(timerInterval);
            clearCookie("pomodoroStartTime");
            clearCookie("pomodoroDuration");

            audio.play();
        }
    }
}

// Call checkTimer on page load
document.addEventListener("DOMContentLoaded", checkTimer);

document.getElementById("startTimer").addEventListener("click", function (e) {
    e.preventDefault();
    var modalContent = document.getElementById("timer-display");
    var form = document.getElementById("timerForm");
    var display = document.getElementById("pomodoroTimer");
    if (this.textContent === "start") {
        this.textContent = "stop";
        var minutes = document.getElementById("minutes").value;
        var seconds = minutes * 60;
        modalContent.style.display = "block";
        form.style.display = "none";
        startTimer(seconds, display, modalContent);
    } else {
        this.textContent = "start";
        modalContent.style.display = "none";
        form.style.display = "block";
        display.textContent = "timer";
        modalContent.innerHTML = "";
        audio.pause();
        audio.currentTime = 0;
        clearInterval(timerInterval);
        clearCookie("pomodoroStartTime");
        clearCookie("pomodoroDuration");
    }
});

function startTimer(duration, display, modalContent) {
    var startTime = Date.now();
    setCookie("pomodoroStartTime", startTime, 1); // Expires in 1 day
    setCookie("pomodoroDuration", duration, 1); // Expires in 1 day

    var timer = duration,
        minutes,
        seconds;
    timerInterval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);
        // Add leading 0 if seconds < 10
        seconds = seconds < 10 ? "0" + seconds : seconds;
        display.textContent = minutes + ":" + seconds;
        modalContent.innerHTML = "<h2>" + minutes + ":" + seconds + "</h2>";
        // If timer reaches 0, stop the timer and play the alarm

        if (--timer < 0) {
            clearInterval(timerInterval);
            // Pause all audio before playing
            var allAudioElements = document.getElementsByTagName("audio");
            for (var i = 0; i < allAudioElements.length; i++) {
                if (allAudioElements[i] != audio) {
                    allAudioElements[i].pause();
                    allAudioElements[i].currentTime = 0; // Reset the audio to the start
                }
            }
            if (window.spotifyPlayer) {
                window.spotifyPlayer
                    .pause()
                    .then(() => {
                        console.log("Spotify playback paused");
                    })
                    .catch((e) => {
                        console.error("Error pausing Spotify playback:", e);
                    });
            }

            audio.play();
        }
    }, 1000);
}
