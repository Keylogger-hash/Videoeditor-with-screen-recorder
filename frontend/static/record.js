var cameraVideoConstraints = {
    width: {
        min: 1024,
        ideal: 1280,
        max: 1920
    },
    height: {
        min: 576,
        ideal: 720,
        max: 1080
    }
};
var recordBaseURL='/files/uploads/'

function uploadRecord(blob, mimetype, filename){
    var fd = new FormData()
    if(mimetype == 'video/webm'){
        fd.append("video", blob, filename)
    } else if (mimetype == 'audio/webm'){
        fd.append("audio", blob, filename)
    }
    var request = new XMLHttpRequest();
    request.open('POST','/api/records/');
    request.onreadystatechange = function(){
        if((request.readyState == XMLHttpRequest.DONE) && (request.status == 200)){
            var data = JSON.parse(request.responseText);
            app.recordingDone(data.result.id);
        }
    };
    request.send(fd);
}

function recordStream(stream, mimeType){
    var recordedChunks = []
    var startTime = Date.now()

    var mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
    mediaRecorder.ondataavailable = function(event){
        if (event && event.data && event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };
    mediaRecorder.onstop = function(event){
        stream = mediaRecorder.stream
        stream.getTracks().forEach(track=>track.stop())
        console.log('Recording stopped...', event);
        const superBuffer = new Blob(recordedChunks, { type: mimeType });
        var duration = Date.now() - startTime;
        ysFixWebmDuration(superBuffer, duration, function(fixedBlob){
            console.log('Foo?')
            var date = (new Date()).toISOString();
            filename = `Record-${date}.webm`;
            uploadRecord(fixedBlob, mimeType, filename);
        })
        window.open('/')
    };
    mediaRecorder.start(100); // TODO: move to const
    return mediaRecorder
}
function processStream(stream){
  setTimeout(()=> stopStream(stream), 5000)
}

function stopStream(stream){
  stream.getTracks().forEach( track => track.stop() );
  };
async function startRecording(sources){
    //TODO: separate into capture/recorder parts
    var recorder = null;
    if(sources.video == 'camera'){
        var constraints = {
            audio: sources.audio,
            video: cameraVideoConstraints
        }
        var stream = await navigator.mediaDevices.getUserMedia(constraints)
       
        app.$refs.player.srcObject = stream
        recorder = recordStream(stream, 'video/webm');
    } else if(sources.video == null) {
        var constraints = {
            audio: sources.audio
        }
        var stream = await navigator.mediaDevices.getUserMedia(constraints);
       
        app.$refs.player.srcObject = stream
        recorder = recordStream(stream, 'audio/webm');
    } else if(sources.video == 'screen'){
        //TODO: check if audio constraint is supported
        var constraints = {
            video: true
        }
        var combinedStream = new MediaStream();
        var vstream = await navigator.mediaDevices.getDisplayMedia(constraints);
        for(var track of vstream.getVideoTracks()){
            combinedStream.addTrack(track);
        }
        if(sources.audio){
            var astream = await navigator.mediaDevices.getUserMedia({ audio: true });
            for(var track of astream.getAudioTracks()){
                combinedStream.addTrack(track);
            }
        }
        
        app.$refs.player.srcObject = combinedStream
        recorder = recordStream(combinedStream, 'video/webm');
    }
    app.recorder = recorder;
    app.isRecording = true;
}

function main(){
    app = new Vue({
        el: '#recorderForm',
        data: {
            videoSource: null,
            audioSource: false,
            isRecording: false,
            recorder: null,
            encodingProgress: 0,
            encodingDone: true,
            isShowButton: false,
            outputName: ""
        },
        computed: {
            recordButtonCaption: function(){
                return this.isRecording ? 'Stop recording' : 'Start recording';
            },
            shareLink: function(){
                outputNameSplit = this.outputName
                outputNameSplit = outputNameSplit.split("/").join("_")
                return location.protocol + '//' + location.host + '/play/record/' + outputNameSplit;
            },
            downloadLink: function(){
                return  recordBaseURL+this.outputName
            }
        },
        methods: {
            toggleCamera: function(){
                this.videoSource = (this.videoSource == 'camera') ? null : 'camera';
            },
            toggleScreen: function(){
                this.videoSource = (this.videoSource == 'screen') ? null : 'screen';
            },
            toggleMic: function(){
                this.audioSource = !this.audioSource;
            },
            toggleRecording: function(){
                if(this.isRecording){
                    this.recorder.stop();
                    this.$refs.player.srcObject = null;
                    this.isRecording = false;
                } else {
                    this.isShowButton=false
                    startRecording({ video: this.videoSource, audio: this.audioSource });
                }
            },
            recordingDone: function(id){
                this.encodingDone = false;
                this.watchProcessing(id);
            },
            watchProcessing: function(id){
                fetch('/api/records/' + id + '/info')
                .then(r => r.json())
                .then((data) => {
                    if(data.success){
                        if((data.result.status == 'QUEUED') || (data.result.status == 'WORKING') || (data.result.status == 'INACTIVE')){
                            this.encodingProgress = Math.floor(data.result.progress);
                            setTimeout(this.watchProcessing.bind(this, id), 1000);
                        } else if(data.result.status == 'FAILED') {
                            console.error('error');
                            this.encodingDone = true;
                            this.encodingProgress = 0;
                            this.isShowButton = false;
                        } else {
                            this.outputName=data.result.output_name
                            this.encodingDone = true;
                            this.encodingProgress = 0;
                            this.isShowButton = true;
                        }
                    }
                })
            },
            copyShareLink: function(e){
                var linkInput = e.target;
                linkInput.select();
                document.execCommand('copy');
                //this.clipboardTooltip.show();
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', main);