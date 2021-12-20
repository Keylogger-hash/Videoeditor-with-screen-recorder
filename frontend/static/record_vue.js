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
