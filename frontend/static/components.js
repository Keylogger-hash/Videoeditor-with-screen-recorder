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
    props: ['is-shown'],
    data: function(){ return {
        dialogShown: this.isShown,
        file: null
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
            this.$emit('submit-upload', this.file);
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
                    console.warn('Failed to fetch video variants');
                    return;
                }
                this.stage = 2;
                this.availableFormats = response.info;
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
                    console.warn('Failed to start downloading')
                    return;
                }
                this.videoId = response.video_id;
                this.trackDownloading();
                this.stage = 3;
                this.$emit('download-submit');
            });
        },
        trackDownloading: function(){
            var videoId = this.videoId;
            if(videoId == null) return;
            fetch('/api/downloads/' + videoId + '/info')
            .then(r => r.json())
            .then((response) => {
                if(!response.success){
                    this.errorMessage = 'Failed to get download status'
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
                        setTimeout(this.trackDownloading, 2000);
                }
            })
        }
    }
});
Vue.component('cut-mode-selector', {
    template: '#cut-mode-selector',
    props: ['value'],
    data: function(){
        return {
        }
    }
});