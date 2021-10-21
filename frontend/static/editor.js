var apiURL = '/api';
var videoBaseURL = '/files/uploads/';
var cutsBaseURL = '/files/cuts/';

var currentVideo = null;
var timeline = null;
var isSeeking = false;

function formatSeconds(n){
    var m = Math.floor(n / 60);
    var s = n % 60;
    return m + (s < 10 ? ':0' : ':') + s;
}

function loadSourceList(){
    fetch(apiURL + '/downloads/')
    .then(r => r.json())
    .then(({ success, downloads: sources }) => {
        var selector = document.all.sourceSelector;
        selector.options.length = 0;
        sources.forEach(function(item){
            if(item.status == 'COMPLETED'){
                selector.add(new Option(item.title, item.id));
            }
        });
    })
}

function loadSelectedSource(){
    var selector = document.all.sourceSelector;
    var videoId = selector.options[selector.selectedIndex].value;
    loadSource(videoId);
}

function loadSource(videoId){
    currentVideo = videoId;
    fetch(apiURL + '/downloads/' + videoId + '/info')
    .then(r => r.json())
    .then(({ success, result }) => {
        if(!success){
            console.warn('Cannot get source video info');
            return;
        }
        var player = document.all.editorPlayer;
        player.src = videoBaseURL + result.filename;
    })
}

function updateProgress(outputFilename){
    fetch(apiURL + '/cuts/' + outputFilename)
    .then(r => r.json())
    .then((data) => {
        if(data.success){
            if((data.result.status == 'QUEUED') || (data.result.status == 'WORKING') || (data.result.status == 'INACTIVE')){
                document.all.processingModalContent.innerText = data.result.progress + '%';
                setTimeout(updateProgress.bind(null, outputFilename), 1000);
            } else {
                document.all.processingModalContent.innerHTML = '<a class="button" target="_blank" href="' + cutsBaseURL + outputFilename + '">Download video</a>';
            }
        }
    })
}

function cutSelectedRange(){
    var startTime = timeline.leftBorder;
    var endTime = timeline.rightBorder;
    var inputSource = currentVideo;
    var outputStreams = document.all.editorCutStreams.options[document.all.editorCutStreams.selectedIndex].value;
    var outputFilename = Math.floor(Date.now()) + '.mp4';
    fetch(apiURL + '/cuts/', {
        method: 'post',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: inputSource, startAt: startTime, endAt: endTime, keepStreams: outputStreams })
    }).then(r => r.json())
    .then((response) => {
        if(response.success){
            showModal('processingModal');
            updateProgress(response.result.output);
        } else {
            alert('Error: ' + response.error);
        }
    })
}

function playSelectedRange(){
    var player = document.all.editorPlayer;
    document.all.editorPlayerProgress.max = Math.floor(selectionRange.end - selectionRange.start);
    player.currentTime = selectionRange.start;
    player.play();
}

function updateVideoMeta(){
    var player = document.all.editorPlayer;
    timeline.setDuration(Math.floor(player.duration));
}

function playerUpdate(){
    var player = document.all.editorPlayer;
    if(player.paused) return;
    if(!isSeeking){
        timeline.setPosition(Math.floor(player.currentTime), true);
        if(player.currentTime >= timeline.rightBorder){
            player.pause();
            player.currentTime = timeline.rightBorder;
        }
    }
}

function playerSeeked(timeToSeek){
    var player = document.all.editorPlayer;
    if(player.currentTime != timeToSeek){
        player.currentTime = timeToSeek;
    } else {
        player.onseeked = null;
        console.log('done!');
    }
}

function seek(n){
    var player = document.all.editorPlayer;
    player.onseeked = playerSeeked.bind(null, n);
    player.currentTime = n;
}

function main(){
    document.all.editorTimeline.width = document.all.editorTimeline.parentNode.offsetWidth;
    timeline = new Timeline(document.all.editorTimeline, 100, { followCursor: true });
    document.all.sourceLoadBtn.onclick = loadSelectedSource;
    document.all.sourceRefresh.onclick = loadSourceList;
    document.all.editorCutBtn.onclick = cutSelectedRange;
    document.all.editorPlayer.onloadedmetadata = updateVideoMeta;
    document.all.editorPlayer.ontimeupdate = playerUpdate;
    document.all.controlsCutStart.onclick = function(){
        timeline.setLeftBorder(timeline.position);
    };
    document.all.controlsCutEnd.onclick = function(){
        timeline.setRightBorder(timeline.position);
    };
    document.all.controlsCutReset.onclick = function(){
        timeline.setRightBorder(timeline.duration);
        timeline.setLeftBorder(0);
    }
    document.all.controlsSeekStart.onclick = function(){
        var player = document.all.editorPlayer;
        seek(timeline.leftBorder);
    };
    document.all.controlsSeekEnd.onclick = function(){
        var player = document.all.editorPlayer;
        seek(timeline.rightBorder);
    };
    document.all.controlsPlay.onclick = function(){
        var player = document.all.editorPlayer;
        if(player.paused)
            player.play();
        else
            player.pause();
    };
    document.all.controlsZoomIn.onclick = function(){ timeline.zoomIn(); }
    document.all.controlsZoomOut.onclick = function(){ timeline.zoomOut(); }
    timeline.on('update', function(){
        console.log(timeline.position);
        // document.all.editorPlayer.currentTime = timeline.position;
        seek(timeline.position);
    });
    loadSourceList();
    if(location.search.length > 1){
        var params = new URLSearchParams(location.search);
        var videoId = params.get('video');
        if(videoId !== null){
            loadSource(videoId);
        }
    }
}

document.addEventListener('DOMContentLoaded', main);
