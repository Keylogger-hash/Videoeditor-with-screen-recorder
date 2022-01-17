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
    model.typeVideo='video'
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

function loadSourceRecord(recordId){
    model.selectedSource = recordId;
    model.typeVideo='record'
    fetch(apiURL + '/records/' + recordId + '/info')
    .then(r => r.json())
    .then(({ success, result }) => {
        if(!success){
            console.warn('Cannot get source video info');
            return;
        }
        var player = document.all.editorPlayer;
        player.src = videoBaseURL + result.output_name;
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
    model.audioOnly = (player.src.indexOf('.mp3') != -1);
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
            timeline: null,
            selectionStart: 0,
            selectionEnd: 0,
            isPlaying: false,
            isMuted: false,
            audioOnly: false
        },
        watch: {
            processingDialogVisible: function(){
                this.processingError = null;
            }
        },
        computed: {
            formattedStart: function(){
                return formatSeconds(this.selectionStart);
            },
            formattedEnd: function(){
                return formatSeconds(this.selectionEnd);
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
            fetchSourcesRecords: function(){
                fetch(apiURL + '/records/')
                .then(r => r.json())
                .then(({ success, data: sources }) => {
                    this.sources = sources.filter((item) => { return item.status == 'COMPLETED' });
                })
            },
            startCutting: function(){
                this.processingDialogVisible = true;
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
            jump: function(offset){
                if(this.timeline.position + offset < this.timeline.leftBorder){
                    seek(this.timeline.leftBorder);
                } else if(this.timeline.position + offset > this.timeline.rightBorder){
                    seek(this.timeline.rightBorder);
                } else {
                    seek(this.timeline.position + offset);
                }
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
                this.selectionStart = this.timeline.leftBorder;
                this.selectionEnd = this.timeline.rightBorder;
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
        var recordId = params.get('record')
        if(videoId !== null){
            model.selectedSource = videoId;
            loadSource(videoId);
            model.fetchSources();
        }
        if (recordId !== null){
            model.selectedSource = recordId;
            loadSourceRecord(recordId)
            model.fetchSourcesRecords();
        }
    }
    tippy(document.querySelector('#shareVideoLink'), { trigger: 'click', content: 'Copied to clipboard' });
}

Vue.component('cut-mode-selector', {
    template: '#cut-mode-selector',
    //props:['value'],
    props: ['value', 'disabled'],
    data: function(){
        return {
        }
    }
});

Vue.component('video-cut-form', {
    template: '#cut-form',
    props: ['source', 'start', 'end', 'mode'],
    data: function(){
        return {
            stage: 'describe',
            error: null,
            progress: null,
            outputName: null,
            description: '',
        }
    },
    computed: {
        shareLink: function(){
            return location.protocol + '//' + location.host + '/play/video/' + this.outputName;
        },
        downloadLink: function(){
            return cutsBaseURL + this.outputName;
        },
        startf: function(){
            return formatSeconds(this.start);
        },
        endf: function(){
            return formatSeconds(this.end);
        },
        progressRound: function(){
            return this.progress == null ? 0 : this.progress.toFixed(0);
        }
    },
    methods: {
        reset: function(){
            this.stage = 'describe';
            this.error = null;
            this.progress = 0;
            this.outputName = null;
            this.description = '';
            this.type=''
        },
        startProcessing: function(){
            fetch(apiURL + '/cuts/', {
                method: 'post',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source: this.source,
                    startAt: this.start,
                    type: model.typeVideo,
                    endAt: this.end,
                    keepStreams: this.mode,
                    description: this.description,
                })
            }).then(r => r.json())
            .then((response) => {
                this.stage = 'process';
                if(response.success){
                    this.outputName = response.result.output;
                    this.watchProcessing();
                } else {
                    this.error = response.error;
                }
            })
        },
        watchProcessing: function(){
            if(this.outputName == null) return;
            fetch(apiURL + '/cuts/' + this.outputName)
            .then(r => r.json())
            .then((data) => {
                if(data.success){
                    if((data.result.status == 'QUEUED') || (data.result.status == 'WORKING') || (data.result.status == 'INACTIVE')){
                        if(data.result.progress > this.progress){
                            this.progress = data.result.progress;
                        } else {
                            this.progress += (1 / (1 + this.progress));
                        }
                        setTimeout(this.watchProcessing.bind(this), 1000);
                    } else if(data.result.status == 'FAILED') {
                        this.error = data.error;
                    } else {
                        this.stage = 'done';
                    }
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
                this.$emit('close');
                this.reset();
            });
        },
        copyShareLink: function(e){
            var linkInput = e.target;
            linkInput.select();
            document.execCommand('copy');
            //this.clipboardTooltip.show();
        }
    }
})

document.addEventListener('DOMContentLoaded', main);
