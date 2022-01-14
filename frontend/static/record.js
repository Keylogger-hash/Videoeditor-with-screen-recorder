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

function uploadRecord(blob, mimetype, filename){
    var fd = new FormData()
    if(mimetype == 'video/webm'){
        fd.append("video", blob, filename)
    } else if (mimetype == 'audio/webm'){
        fd.append("audio", blob, filename)
    }
    var request = new XMLHttpRequest()
    request.open('POST','/api/records/')
    request.send(fd)
}

function recordStream(stream, mimeType){
    var recordedChunks = []
    var startTime = Date.now()
    var stopped = false;

    var mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
    mediaRecorder.ondataavailable = function(event){
        if (event && event.data && event.data.size > 0) {
            recordedChunks.push(event.data);
        }
    };
    mediaRecorder.onstop = function(event){
        console.log('Recording stopped...', event);
        const superBuffer = new Blob(recordedChunks, { type: mimeType });
        var duration = Date.now() - startTime;
        ysFixWebmDuration(superBuffer, duration, function(fixedBlob){
            console.log('Foo?')
            var date = (new Date()).toISOString();
            filename = `Record-${date}.webm`;
            uploadRecord(fixedBlob, mimeType, filename);
        })
    };
    mediaRecorder.start(100); // TODO: move to const
    return mediaRecorder
}

async function startRecording(sources){
    //TODO: separate into capture/recorder parts
    var recorder = null;
    if(sources.video == 'camera'){
        var constraints = {
            audio: sources.audio,
            video: cameraVideoConstraints
        }
        var stream = await navigator.mediaDevices.getUserMedia(constraints);
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
            recorder: null
        },
        computed: {
            recordButtonCaption: function(){
                return this.isRecording ? 'Stop recording' : 'Start recording';
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
                    startRecording({ video: this.videoSource, audio: this.audioSource });
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', main);