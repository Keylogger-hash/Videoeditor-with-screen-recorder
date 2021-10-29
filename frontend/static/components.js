Vue.component('bulma-modal', {
    template: '#base-modal-template',
    props: ['is-shown'],
    data: function(){ return {  } },
    methods: {
        close: function(){
            this.$emit('close');
        }
    }
});
Vue.component('upload-modal', {
    template: '#upload-modal-template',
    props: ['is-shown', 'upload-url'],
    data: function(){ return {
        dialogShown: this.isShown,
        file: null,
        errorMessage: null,
        isStarted: false,
        progress: null
    } },
    watch: {
        isShown: function(value){
            this.dialogShown = value;
        }
    },
    computed: {
        filename: function(){
            if(this.file === null)
                return '';
            return this.file.name;
        }
    },
    methods: {
        setUploadFile: function(event){
            this.file = event.target.files[0]
        },
        submitUpload: function(){
            if(this.file == null){
                this.errorMessage = 'No file selected';
                console.warn('No file selected');
                return;
            }
            var fd = new FormData();
            fd.append('upload', this.file);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', this.uploadUrl)
            xhr.onreadystatechange = () => {
                if(xhr.readyState == XMLHttpRequest.DONE){
                    this.isStarted = false;
                    if(xhr.status == 200){
                        this.$emit('submit-upload');
                    } else {
                        this.errorMessage = 'Failed to complete upload, server respond with error code ' + xhr.status;
                    }
                }
            };
            xhr.onprogress = (event) => {
                this.progress = Math.floor(100 * event.loaded / event.total);
            };
            xhr.onerror = () => {
                this.errorMessage = 'Failed to complete upload, network error';
                this.isStarted = false;
            };
            xhr.send(fd);
            this.isStarted = true;
            /*
            fetch('/api/upload', {
                method: 'POST',
                body: fd
            })
            .then(r => r.json())
            .then((response) => {
                this.$emit('submit-upload');
            });
            */
        }
    }
});
Vue.component('yt-download-modal', {
    template: '#yt-download-modal-template',
    props: ['is-shown'],
    data: function(){
        return {
            mainDialog: this.isShown,
            stage: 1,
            availableFormats: [],
            downloadLink: null,
            downloadFormat: null,
            videoId: null,
            errorMessage: null
        }
    },
    watch: {
        isShown: function(value){
            this.stage = 1;
            this.mainDialog = value;
            this.videoId = null;
        }
    },
    methods: {
        fetchFormats: function(){
            fetch('/api/downloads/info', { method: 'post', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ link: this.downloadLink }) })
            .then(r => r.json())
            .then((response) => {
                if(!response.success){
                    this.errorMessage = 'Failed to fetch video variants: ' + response.error;
                    console.warn('Failed to fetch video variants');
                    return;
                }
                this.stage = 2;
                this.availableFormats = response.info;
            })
            .catch((error) => {
                this.errorMessage = 'Failed to fetch variants: ' + error.toString();
            });
        },
        submitDownload: function(formatId){
            fetch('/api/downloads/', {
                method: 'post',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify({ link: this.downloadLink, format_id: formatId })
            })
            .then(r => r.json())
            .then((response) => {
                if(!response.success){
                    this.errorMessage = 'Failed to start downloading: ' + response.error;
                    console.warn('Failed to start downloading');
                    return;
                }
                this.videoId = response.video_id;
                this.trackDownloading();
                this.stage = 3;
                this.$emit('download-submit');
            })
            .catch((error) => {
                this.errorMessage = 'Failed to start downloading: ' + error.toString();
            });
        },
        trackDownloading: function(){
            var videoId = this.videoId;
            if(videoId == null) return;
            fetch('/api/downloads/' + videoId + '/info')
            .then(r => r.json())
            .then((response) => {
                if(!response.success){
                    this.errorMessage = 'Failed to get download status: ' + response.error;
                    return;
                }
                switch(response.result.status){
                    case 'FAILED':
                        this.errorMessage = 'Failed to download video'
                        break;
                    case 'COMPLETED':
                        this.stage = 4;
                        break;
                    default:
                        setTimeout(this.trackDownloading, 5000);
                }
            })
            .catch((error) => {
                this.errorMessage = 'Failed to fetch status: ' + error.toString();
            });
        }
    }
});
