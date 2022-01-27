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

Vue.component('preview-modal', {
    template: '#preview-modal-template',
    props: ['name'],
    data: function(){
        return {}
    },
    computed: {
        directLink: function(){
            return '/files/cuts/' + this.name;
        },
        shareLink: function(){
            return location.protocol + '//' + location.host + '/play/' + this.name;
        }
    },
    methods: {
        copyShareLink: function(e){
            var linkInput = e.target;
            linkInput.select();
            document.execCommand('copy');
        }
    },
    mounted: function(){
        tippy(this.$refs.shareLinkInput, { trigger: 'click', content: 'Copied to clipboard' });
    }
})

function main(){
    sourcesList = new Vue({
        el: '#sourcesList',
        data: {
            showTypeFilter: false,
            showTypes: ['sources', 'clips', 'records'],
            sources: [],
            clips: [],
            records: [],
            progress:{},
        },
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
                });
                fetch('/api/cuts/')
                .then(r => r.json())
                .then((response) => {
                    if(!response.success){
                        console.warn('Failed to fetch videos list');
                        return;
                    }
                    this.clips = response.cuts;
                });
                fetch('/api/records/')
                .then(r => r.json())
                .then((response) => {
                    if(!response.success){
                        console.warn('Failed to fetch records');
                        return;
                    }
                    this.records = response.data;
                });
            },
            showPreview: function(id){
                console.log(id);
                modals.previewClip = id;
            },
            showPreviewRecord: function(filename){
                console.log(filename)
                filename = filename.split("/").join("_")
            },
            deleteVideo: function(title,id){
                message = `Are you sure to delete video:\n${title}?`
                result = window.confirm(message)
                if (result) {
                    fetch('/api/downloads/' + id + '/cancel', { method: 'delete' })
                    .then(r => r.json())
                    .then(() => {
                        this.fetchSources();
                    })
                }
            },
            deleteRecord: function(title, id){
                message = `Are you sure to delete record:\n${title}?`
                result = window.confirm(message);
                if (result) {
                    fetch('/api/records/'+id+'/',{method:'delete'})
                    .then(r=> r.json())
                    .then(()=>{
                        this.fetchSources();
                    })
                }
                
            },
            deleteClip: function(id){
                message = `Are you sure to delete clip:\n${id}?`
                result = window.confirm(message)
                if (result) {
                    fetch('/api/cuts/' + id, {
                        method: 'DELETE'
                    })
                    .then(r => r.json())
                    .then((response) => {
                        if(!response.success){
                            console.warn('Failed to delete video ' + id);
                            return;
                        }
                        this.fetchSources();
                    })
                }  
            },
            
        }
    });
    sourcesList.fetchSources();
    modals = new Vue({
        el: '#modals',
        data: {
            uploadDialog: false,
            ytDownloadDialog: false,
            ytDownloadFormatsDialog: false,
            previewClip: null
        },
        methods: {
            submitUpload: function(file){
                this.uploadDialog = false;
                sourcesList.fetchSources();
            },
            downloadCompleted: function(){
                sourcesList.fetchSources();
            },
            downloadCanceled: function(){
                sourcesList.fetchSources();
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', main);
