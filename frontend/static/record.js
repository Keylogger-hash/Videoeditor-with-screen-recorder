function main() {
    model = new Vue({
        el: '#app',
        data: {
            canRecord: true,
            isRecord: false,
            isScreen: true,
            options: {
                audioBitsPerSecond: 128000,
                videoBitsPerSecond: 2500000,
                mimeType: 'video/webm'
            },
            displayMediaOptions: {
                video: {
                    cursor: "always"
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                },
            },
            mediaRecorder: {},
            stream: {},
            recordedChunks: [],
            file: null,
            fileReady: false,
            url: 'http://localhost:5000',
            bytes_processed: 0,
        },
        watch: {},
        computed: {},
        methods: {
            async uploadFileData() {

            },
            setFile(){

            },
            stopStream: function(){

            },
            download: function(){

            },
            
            getStream: async function(){

            },
            handleDataAvailable: function(event) {
                if (len(event.data) > 0) {
                    this.recordedChunks.push(event.data)
                } else {
                    // .... //
                }
            },
            
        },
    })
}



let videoElement = document.getElementById('main-player')
let startElement = document.getElementById("start")
let stopElement = document.getElementById("stop")

var options = {mimeType: 'video/webm; codecs=vp9'};


var displayMediaOptions = {
    video: {
        cursor: "always"
    },
    audio: true
}

startElement.addEventListener('click', function(event){
    startCapture()
    console.log('Recording was started')
})

stopElement.addEventListener('click', function(event){
    stopCapture()

})



async function startCapture(displayMediaOptions) {

      
    try {
        videoElement.srcObject = await navigator.mediaDevices.getDisplayMedia(displayMediaOptions)
        let recorder = new MediaRecorder(videoElement.srcObject, displayMediaOptions)
        var chunks = []
        recorder.ondataavailable = handleDataAvailable
        handleDataAvailable = e => chunks.push(videoElement.srcObject.getTracks())
        var blob = new Blob(chunks, {'type':'video/mp4'})
        var url = URL.createObjectURL(blob)
    var a = document.getElementById('download')
    a.href = url
    a.download = 'test.mp4'
    a.
    a.click()
    window.URL.revokeObjectURL(url);
    } catch(err) {   
        console.error("Error: "+err)
    }
}

async function stopCapture(displayMediaOptions) {
    let tracks = videoElement.srcObject.getTracks()
    

    tracks.forEach(track => {
        track.stop()
    });
    videoElement.srcObject = null;
    // return navigator.mediaDevices.getDisplayMedia(displayMediaOptions)
    // .catch(err => {console.error("Error: "+err); return null})
}