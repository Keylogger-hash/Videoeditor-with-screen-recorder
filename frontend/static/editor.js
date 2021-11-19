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
            processingError: null,
            outputName: null,
            downloadLink: null,
            timeline: null,
            selectionStart: 0,
            selectionEnd: 0,
            isPlaying: false,
            isMuted: false
        },
        watch: {
            processingDialogVisible: function(){
                this.processingError = null;
            }
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
                    this.processingError = null;
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
                        } else if(data.result.status == 'FAILED') {
                            this.processingError = data.error;
                        } else {
                            this.downloadLink = cutsBaseURL + this.outputName;
                        }
                    }
                })
            },
            /** playback methods **/
            toggleMute: function(){
                this.$refs.player.muted = !this.$refs.player.muted;
            },
            togglePlay: function(){
                var player = this.$refs.player;
                // TODO: fix icons
                if(player.paused){
                    player.play();
                } else {
                    player.pause();
                }
            },
            jumpToStart: function(){
                seek(this.timeline.leftBorder);
            },
            jumpToEnd: function(){
                seek(this.timeline.rightBorder);
            },
            /** cut methods **/
            setSelectionStart: function(){
                this.timeline.setLeftBorder(this.timeline.position);
            },
            setSelectionEnd: function(){
                this.timeline.setRightBorder(this.timeline.position);
            },
            resetSelection: function(){
                this.timeline.setLeftBorder(0);
                this.timeline.setRightBorder(this.timeline.duration);
            },
            /** zoom **/
            timelineZoomIn: function(){
                this.timeline.zoomIn();
            },
            timelineZoomOut: function(){
                this.timeline.zoomOut();
            }
        },
        mounted: function(){
            var canvas = this.$refs.timelineCanvas;
            canvas.width = canvas.parentNode.offsetWidth;
            window.addEventListener('resize', () => {
                canvas.width = canvas.parentNode.offsetWidth;
                this.timeline.render();
            });
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
    document.all.editorPlayer.onloadedmetadata = updateVideoMeta;
    //document.all.editorPlayer.ontimeupdate = playerUpdate;
    document.all.editorPlayer.onpause = function(){
        model.isPlaying = false;
        clearInterval(window.positionUpdateInterval);
    };
    document.all.editorPlayer.onplay = function(){
        model.isPlaying = true;
        window.positionUpdateInterval = setInterval(playerUpdate, 100);
    };
    document.all.editorPlayer.onvolumechange = function(event){
        model.isMuted = event.target.muted;
    };

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
