var app = null;

function main(){
    app = new Vue({
        el: '#app',
        data: {
            videos: []
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
            }
        },
        mounted: function(){
            this.fetchVideos();
        }
    });
}

document.addEventListener('DOMContentLoaded', main);