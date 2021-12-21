const videoElement = document.getElementById('#main-player')
let recordElement = document.getElementById("#record")
let displayElement = document.getElementById("#display")
let webcameraElement = document.getElementById("#webcamera")
let isScreen = true;
//let stopElement = document.getElementById("stop")
let mediaRecorder
let recordChunks = []
var startTime = null




var displayMediaOptions = {
    video: {
        cursor: "always"
    },
    audio: true
}

var webcameraMediaOptions = {
    audio: true,
    video: { 
        width: {min: 1024, ideal:1280, max:1920}, 
        height: {min:576, ideal: 720, max: 1080} },
}

displayElement.addEventListener('click', function(event){
    isScreen = true
    console.log(isScreen)
})

webcameraElement.addEventListener('click', function(event){
    isScreen = false
    console.log(isScreen)
})


recordElement.addEventListener('click', function(event){
    toggleRecording()
}, false)


function toggleRecording() {
    if (recordElement.textContent === 'Record') {
        startCapture()
    } else {
        stopCapture()
        recordElement.textContent = 'Record'
    }
} 


function handleDataAvailable(event) {
    if (event && event.data) {
        recordChunks.push(event.data)
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
    fd.append("upload", fixedBlob, filename)
    var request = new XMLHttpRequest()
    request.open('POST','http://localhost:4040/api/upload')
    request.send(fd)
}

function handleStop(event) {
    console.log('Recording stopped...', event)
    const superBuffer = new Blob(recordChunks, {type:'video/webm'})
    var duration = Date.now()-startTime
    console.log(duration)
    ysFixWebmDuration(superBuffer, duration, function(fixedBlob){
        var date = Date()
        filename = `${date}.webm`
        download(fixedBlob, filename)
        upload_data(fixedBlob, filename)
    })

}



async function startCapture(displayMediaOptions) {
    let stream = null
    recordChunks = []
    let options = {mimeType: 'video/webm; codecs=vp9'};
    try {
        if (isScreen) {
            stream = await navigator.mediaDevices.getDisplayMedia(displayMediaOptions);
        } else {
            stream = await navigator.mediaDevices.getUserMedia(webcameraMediaOptions);
        }   
        
        try {
            mediaRecorder = new MediaRecorder(stream, options);
        } catch (e0) {
            console.log('Unable to create MediaRecorder with options Object: ', e0);
            try {
                options = {mimeType: 'video/webm; codecs=vp9'};
                mediaRecorder = new MediaRecorder(stream, options);
            } catch (e1) {
                console.log('Unable to create MediaRecorder with options Object: ', e1);
                try {
                    options = {mimeType: 'video/webm; codecs=vp8'};; // Chrome 47
                    mediaRecorder = new MediaRecorder(stream, options);
                } catch (e2) {
                    alert('MediaRecorder is not supported by this browser.\n\n' +
                    'Try Firefox 29 or later, or Chrome 47 or later, ' +
                    'with Enable experimental Web Platform features enabled from chrome://flags.');
                    console.error('Exception while creating MediaRecorder:', e2);
                    return;
              }
            }
        }
        console.log(options)
        //mediaRecorder = new MediaRecorder(stream, displayMediaOptions)
        recordElement.textContent = "Stop recording"
        videoElement.srcObject = stream
        var chunks = []
        startTime = Date.now()
        console.log(startTime)
        mediaRecorder.onstop = handleStop
        mediaRecorder.ondataavailable = handleDataAvailable
        mediaRecorder.start(100)
    } catch(err) {   
        console.error("Error: "+err)
    }
}




async function stopCapture(displayMediaOptions) {
    let tracks = videoElement.srcObject.getTracks()
    tracks.forEach(track => track.stop());
    mediaRecorder.stop()
    videoElement.srcObject = null
}