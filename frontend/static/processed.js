var app = null;

function main(){
    app = new Vue({
        el: '#app',
        data: {
            videos: [],
            previewName: null,
            previewFile: null
        },
        computed: {
            previewLink: function(){
                return '/files/cuts/' + this.previewName;
            },
            shareLink: function(){
                return location.protocol + '//' + location.host + '/play/' + this.previewName;
            }
        },
        methods: {
            fetchVideos: function(){
                fetch('/api/cuts/')
                .then(r => r.json())
                .then((response) => {
                    if(!response.success){
                        console.warn('Failed to fetch videos list');
                        return;
                    }
                    this.videos = response.cuts;
                })
            },
            previewVideo: function(videoName){
                this.previewName = videoName;
            },
            deleteVideo: function(videoId){
                fetch('/api/cuts/' + videoId, {
                    method: 'DELETE'
                })
                .then(r => r.json())
                .then((response) => {
                    if(!response.success){
                        console.warn('Failed to delete video ' + videoId);
                        return;
                    }
                    this.fetchVideos();
                })
            },
            copyShareLink: function(e){
                var linkInput = e.target;
                linkInput.select();
                document.execCommand('copy');
                //this.clipboardTooltip.show();
            }
        },
        mounted: function(){
            this.fetchVideos();
        }
    });
    tippy(document.querySelector('#shareVideoLink'), { trigger: 'click', content: 'Copied to clipboard' });
}
document.addEventListener('DOMContentLoaded', main);