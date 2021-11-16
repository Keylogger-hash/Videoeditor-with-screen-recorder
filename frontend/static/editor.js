var apiURL = '/api';
var videoBaseURL = '/files/uploads/';
var cutsBaseURL = '/files/cuts/';

var currentVideo = null;
var timeline = null;
var isSeeking = false;

var model = null;

function formatSeconds(n){
    var m = Math.floor(n / 60);
    var s = n % 60;
    return m + (s < 10 ? ':0' : ':') + s.toFixed(1);
}

function loadSelectedSource(){
    var selector = document.all.sourceSelector;
    var videoId = selector.options[selector.selectedIndex].value;
    loadSource(videoId);
}

function loadSource(videoId){
    model.selectedSource = videoId;
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
                model.processingProgress = data.result.progress;
                setTimeout(updateProgress.bind(null, outputFilename), 1000);
            } else {
                model.downloadLink = cutsBaseURL + outputFilename;
            }
        }
    })
}

function cutSelectedRange(){
    var startTime = model.timeline.leftBorder;
    var endTime = model.timeline.rightBorder;
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
            model.processingDialogVisible = true;
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
    model.timeline.setDuration(Math.floor(player.duration * 10) / 10);
}

function playerUpdate(){
    var player = document.all.editorPlayer;
    if(player.paused) return;
    if(!isSeeking){
        model.timeline.setPosition(Math.floor(player.currentTime * 10) / 10, true);
        if(player.currentTime >= model.timeline.rightBorder){
            player.pause();
            model.timeline.setPosition(model.timeline.rightBorder, true);
            model.timeline.render();
        }
    }
}

function playerSeeked(timeToSeek){
    var player = document.all.editorPlayer;
    if(player.currentTime != timeToSeek){
        player.currentTime = timeToSeek;
    } else {
        player.onseeked = null;
        model.timeline.setPosition(player.currentTime, true);
    }
}

function seek(n){
    var player = document.all.editorPlayer;
    player.onseeked = playerSeeked.bind(null, n);
    player.currentTime = n;
}

function main(){
    model = new Vue({
        el: '#app',
        data: {
            cutMode: 'both',
            sources: [],
            selectedSource: null,
            processingDialogVisible: false,
            processingProgress: 0,
            outputName: null,
            downloadLink: null,
            timeline: null,
            selectionStart: 0,
            selectionEnd: 0
        },
        methods: {
            fetchSources: function(){
                fetch(apiURL + '/downloads/')
                .then(r => r.json())
                .then(({ success, downloads: sources }) => {
                    this.sources = sources.filter((item) => { return item.status == 'COMPLETED' });
                })
            },
            startCutting: function(){
                var startTime = this.timeline.leftBorder;
                var endTime = this.timeline.rightBorder;
                var inputSource = this.selectedSource;
                fetch(apiURL + '/cuts/', {
                    method: 'post',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: inputSource, startAt: startTime, endAt: endTime, keepStreams: this.cutMode })
                }).then(r => r.json())
                .then((response) => {
                    if(response.success){
                        this.processingDialogVisible = true;
                        this.outputName = response.result.output;
                        updateProgress(response.result.output);
                    } else {
                        alert('Error: ' + response.error);
                    }
                })
            },
            cancelProcessing: function(){
                fetch(apiURL + '/cuts/' + this.outputName, { method: 'DELETE' })
                .then(r => r.json())
                .then((response) => {
                    if(!response.success){
                        console.warn(response.error);
                        return;
                    }
                    this.processingDialogVisible = false;
                });
            },
            trackProcessingStatus: function(){
                if(this.outputName == null) return;
                fetch(apiURL + '/cuts/' + this.outputName)
                .then(r => r.json())
                .then((data) => {
                    if(data.success){
                        if((data.result.status == 'QUEUED') || (data.result.status == 'WORKING') || (data.result.status == 'INACTIVE')){
                            this.processingProgress = data.result.progress;
                            setTimeout(this.trackProcessingStatus.bind(this), 2000);
                        } else {
                            this.downloadLink = cutsBaseURL + this.outputName;
                        }
                    }
                })
            }
        },
        mounted: function(){
            var canvas = this.$refs.timelineCanvas;
            canvas.width = canvas.parentNode.offsetWidth;
            this.timeline = new Timeline(canvas, 100, { followCursor: false });
            this.timeline.on('update', function(){
                seek(this.timeline.position);
            }.bind(this));
            this.timeline.on('rangeupdate', () => {
                this.selectionStart = formatSeconds(this.timeline.leftBorder);
                this.selectionEnd = formatSeconds(this.timeline.rightBorder);
            });
            this.timeline.render();
        }
    });

    document.querySelector('.dashboard').style.height = window.innerHeight + 'px';
    document.all.sourceLoadBtn.onclick = loadSelectedSource;
    document.all.sourceRefresh.onclick = model.fetchSources.bind(model);
    //document.all.editorCutBtn.onclick = cutSelectedRange;
    document.all.editorPlayer.onloadedmetadata = updateVideoMeta;
    document.all.editorPlayer.ontimeupdate = playerUpdate;
    document.all.editorPlayer.onpause = function(){
        document.all.controlsPlay.innerHTML = '<i class="fas fa-play"></i>';
    };
    document.all.editorPlayer.onplay = function(){
        document.all.controlsPlay.innerHTML = '<i class="fas fa-pause"></i>';
    };
    document.all.controlsCutStart.onclick = function(){
        model.timeline.setLeftBorder(model.timeline.position);
    };
    document.all.controlsCutEnd.onclick = function(){
        model.timeline.setRightBorder(model.timeline.position);
    };
    document.all.controlsCutReset.onclick = function(){
        model.timeline.setRightBorder(model.timeline.duration);
        model.timeline.setLeftBorder(0);
    }
    document.all.controlsSeekStart.onclick = function(){
        var player = document.all.editorPlayer;
        seek(model.timeline.leftBorder);
    };
    document.all.controlsSeekEnd.onclick = function(){
        var player = document.all.editorPlayer;
        seek(model.timeline.rightBorder);
    };
    document.all.controlsPlay.onclick = function(event){
        var player = document.all.editorPlayer;
        // TODO: fix icons
        if(player.paused){
            player.play();
        } else {
            player.pause();
        }
    };

    document.all.controlsZoomIn.onclick = function(){ model.timeline.zoomIn(); }
    document.all.controlsZoomOut.onclick = function(){ model.timeline.zoomOut(); }
    if(location.search.length > 1){
        var params = new URLSearchParams(location.search);
        var videoId = params.get('video');
        if(videoId !== null){
            model.selectedSource = videoId;
            loadSource(videoId);
        }
    }
    model.fetchSources();
}

Vue.component('cut-mode-selector', {
    template: '#cut-mode-selector',
    props: ['value'],
    data: function(){
        return {
        }
    }
});

document.addEventListener('DOMContentLoaded', main);
