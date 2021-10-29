var videoBaseURL = '/files/uploads/';
var cutsBaseURL = '/files/cuts/';

var sourcesList = null;
var modals = null;

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

function main(){
    sourcesList = new Vue({
        el: '#sourcesList',
        data: { sources: [] },
        methods: {
            fetchSources: function(){
                fetch('/api/downloads/')
                .then(r => r.json())
                .then(({ success, downloads }) => {
                    if(!success){
                        console.warn('Unable to fetch sources');
                        return;
                    }
                    this.sources = downloads;
                })
            },
            deleteVideo: function(id){
                fetch('/api/downloads/' + id + '/cancel', { method: 'delete' })
                .then(r => r.json())
                .then(() => {
                    this.fetchSources();
                })
            }
        }
    });
    sourcesList.fetchSources();
    modals = new Vue({
        el: '#modals',
        data: {
            uploadDialog: false,
            ytDownloadDialog: false,
            ytDownloadFormatsDialog: false
        },
        methods: {
            submitUpload: function(file){
                this.uploadDialog = false;
                sourcesList.fetchSources();
            },
            submitDownload: function(link, format){
                sourcesList.fetchSources();
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', main);
