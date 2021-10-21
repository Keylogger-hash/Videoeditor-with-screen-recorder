var videoBaseURL = '/files/uploads/';
var cutsBaseURL = '/files/cuts/';

function uploadVideo(){
    var fd = new FormData();
    var file = document.all.videoUploadInput.files[0];
    if(file === undefined){
        console.warn('No file selected');
        return;
    }
    fd.append('upload', file);
    fetch('/api/upload', {
        method: 'POST',
        body: fd
    })
    .then(r => r.json())
    .then(function(response){
        if(!response.success){
            document.all.videoUploadStatus.textContent = 'Failed to upload: ' + response.error;
        } else {
            document.all.videoUploadStatus.innerHTML = '<a href="/edit?video=' + response.result.videoId + '">Edit uploaded file</a>';
        }
    });
}

function fetchVideo(videoLink, videoFormat){
    fetch('/api/downloads/', { method: 'post', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ link: videoLink, format_id: videoFormat }) })
    .then(r => r.json())
    .then(function(response){
        if(!response.success){
            console.warn('Failed to start downloading')
            return;
        }
        trackDownloading(response.video_id);
    });
    closeFormatsList();
};

function fetchFormats(){
    var videoLink = document.all.videoDownloadUrl.value;
    fetch('/api/downloads/info', { method: 'post', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ link: videoLink }) })
    .then(r => r.json())
    .then(function(response){
        if(!response.success){
            console.warn('Failed to fetch video variants');
            return;
        }
        document.all.videoFormatsModal.classList.add('is-active');
        document.all.videoFormatsList.innerHTML = '';
        response.info.forEach(function(formatInfo){
            var item = document.createElement('li');
            var btn = document.createElement('a');
            btn.onclick = fetchVideo.bind(null, videoLink, formatInfo.format_id);
            btn.textContent = formatInfo.quality + '(' + formatInfo.ext + ')';
            item.appendChild(btn);
            document.all.videoFormatsList.appendChild(item);
        });
    });
}

function closeFormatsList(){
    document.all.videoFormatsModal.classList.remove('is-active');
}

function trackDownloading(videoId){
    fetch('/api/downloads/' + videoId + '/info')
    .then(r => r.json())
    .then(function(response){
        if(!response.success){
            console.warn('Failed to get downloading status');
            return;
        }
        switch(response.result.status){
            case 'FAILED':
                document.all.videoUploadStatus.textContent = 'Failed to upload: ' + response.error;
                break;
            case 'COMPLETED':
                document.all.videoUploadStatus.innerHTML = '<a href="/edit?video=' + videoId + '">Cut downloaded file</a>';
                break;
            default:
                document.all.videoUploadStatus.textContent = 'Downloading...';
                setTimeout(trackDownloading, 2000, videoId);
        }
    })
}

function displaySelectedFile(){
    document.all.videoUploadName.textContent = document.all.videoUploadInput.files[0].name;
}

function main(){
    document.all.videoUploadInput.onchange = displaySelectedFile;
    document.all.videoUploadButton.onclick = uploadVideo;
    document.all.videoFetchFormats.onclick = fetchFormats;
}

document.addEventListener('DOMContentLoaded', main);
