const videoElement = document.getElementById('#main-player')
let recordElement = document.getElementById("#record")
let displayElementWithoutAudio = document.getElementById("#display")
let displayElementWithAudio = document.getElementById("#display-audio")
let webcameraElement = document.getElementById("#webcamera")
let microphoneElement = document.getElementById("#microphone")

let isScreen = 0;
let stopped = true
let shouldStop = false


displayElementWithoutAudio.addEventListener('click', function(event){
    isScreen = 0
    console.log(isScreen)
})
displayElementWithAudio.addEventListener('click', function(event){
    isScreen = 1
    console.log(isScreen)
})

webcameraElement.addEventListener('click', function(event){
    isScreen = 2
    console.log(isScreen)
})

microphoneElement.addEventListener('click', function(event){
    isScreen = 3
    console.log(isScreen)
})



recordElement.addEventListener('click', function(event){
    toggleRecording()
}, false)

function startCapture() {
    
    if (isScreen == 0){
        return new Promise(()=>{recordScreenWithoutAudio()})
    }
    if (isScreen == 1){
        return new Promise(()=>{recordScreenWithAudio()})
    }
    if (isScreen == 2){
        return new Promise(()=>{recordWebcamera()})
    }
    if (isScreen == 3){
        return new Promise(()=>{recordAudio()})
    }
}

function stopCapture() {
    shouldStop = true
    
}

function toggleRecording() {
    if (recordElement.textContent === 'Record') {
        startCapture()
    } else {
        stopCapture()
        videoElement.srcObject = null
        recordElement.textContent = "Record"
    }
} 

function download(fixedBlob, filename){
    var url = URL.createObjectURL(fixedBlob)
    var a = document.getElementById('download')
    a.href = url
    var date = new Date()
    a.download = filename
    //a.click()
}
function upload_data(fixedBlob, filename) {
    fd = new FormData()
    if (isScreen === 0  || isScreen === 1 || isScreen == 2){
        fd.append("video", fixedBlob, filename)
    } 
    if (isScreen === 3 ){
        fd.append("audio", fixedBlob, filename)
    }
    var request = new XMLHttpRequest()
    request.open('POST','/api/record/')
    request.send(fd)
}

const handleRecord = function({stream, mimetype}){
    let recordChunks = []
    var startTime = null

    startTime = Date.now()
    stopped = false
    options = {mimeType: mimetype}
    const mediaRecorder = new MediaRecorder(stream, options)
    recordElement.textContent = "Stop recording"
    mediaRecorder.ondataavailable = function(event){
        if (event && event.data && event.data.size > 0) {
            recordChunks.push(event.data)
        }
        if (shouldStop == true && stopped == false) {
            
            mediaRecorder.stop()
            stopped=true
        }
    }
    mediaRecorder.onstop = function(event){
        console.log('Recording stopped...', event)
        const superBuffer = new Blob(recordChunks, {type:mimetype})
        var duration = Date.now()-startTime
        console.log(duration)
        ysFixWebmDuration(superBuffer, duration, function(fixedBlob){
            var date = Date()
            filename = `${date}.webm`
            download(fixedBlob, filename)
            upload_data(fixedBlob, filename)
        })
    }
    mediaRecorder.start(100)

}

async function recordAudio() {
    var microphoneMediaOptions = {
        audio: true
    }
    shouldStop = false
    stream = await navigator.mediaDevices.getUserMedia(microphoneMediaOptions);
    mimetype = "audio/webm"
    videoElement.srcObject = stream
    handleRecord({stream, mimetype})
}

async function recordWebcamera() {
    var webcameraMediaOptions = {
        audio: true,
        video: { 
            width: {min: 1024, ideal:1280, max:1920}, 
            height: {min:576, ideal: 720, max: 1080} },
    }
    shouldStop = false
    stream = await navigator.mediaDevices.getUserMedia(webcameraMediaOptions);
    mimetype = "video/webm"
    videoElement.srcObject = stream
    handleRecord({stream, mimetype})
}

async function recordScreenWithAudio() {
    const mimeType = 'video/webm'
    var displayMediaOptions = {
        video: {
            cursor: "motion"
        },
        audio: {
            "echoCancellation":true
        },
    }
    var microphoneMediaOptions = {
        audio: true
    }
    shouldStop = false
    if (!(navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia)) {
        return window.alert('Record not supported')
    }
    let stream = null;
    const displayStream = await navigator.mediaDevices.getDisplayMedia(displayMediaOptions)
    if (window.confirm("Record with screen")) {
        const audioContext = new AudioContext()
        const voiceStream = await navigator.mediaDevices.getUserMedia(microphoneMediaOptions)
        const userAudio = audioContext.createMediaStreamSource(voiceStream)
        const audioDestination = audioContext.createMediaStreamDestination()
        userAudio.connect(audioDestination)
        if (displayStream.getAudioTracks().length > 0){
            const displayAudio = audioContext.createMediaStreamSource(displayStream)
            displayAudio.connect(audioDestination)
        }
        const tracks = [...displayStream.getVideoTracks(), ...audioDestination.stream.getTracks()]
        stream = new MediaStream(tracks)
        handleRecord({stream, mimeType})
    } else {
        stream = displayStream
        handleRecord({stream, mimeType})
    }
    videoElement.srcObject = stream
}
async function recordScreenWithoutAudio(){
    var displayMediaOptions = {
        video: {
            cursor: "always"
        },
        audio :false,
    }
    shouldStop = false
    stream = await navigator.mediaDevices.getDisplayMedia(displayMediaOptions);
    mimetype = "video/webm"
    videoElement.srcObject = stream
    handleRecord({stream, mimetype})   
}