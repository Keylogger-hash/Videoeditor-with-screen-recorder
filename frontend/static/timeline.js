function Timeline(element, duration, options) {
    this.element = element;
    this.duration = duration;
    this.position = 0;
    this.shadowPosition = null;
    this.leftBorder = 0;
    this.rightBorder = duration;
    this.scale = 1;
    this.offset = 0;
    this.followPlayCursor = options.followCursor === undefined ? false : options.followCursor;

    this.globalTimelineHeight = Math.floor(this.element.height / 4);

    this._listeners = {};

    this.formatSeconds = function(n){
        var m = Math.floor(n / 60);
        var s = n % 60;
        return m + (s < 10 ? ':0' : ':') + s;
    };
    this.zoomIn = function(){
        this.scale /= 2;
        this.render();
    };
    this.zoomOut = function(){
        if(this.scale < 1){
            this.scale *= 2;
        }
        this.render();
    };
    this.moveZoomLeft = function(){
        if(this.offset > 0){
            this.offset -= 10;
        }
        this.render();
    };
    this.moveZoomRight = function(){
        if((this.offset + this.duration * this.scale) < this.duration){
            this.offset += 10;
        }
        this.render();
    };
    this.setPosition = function(x, silent){
        if((x < 0) || (x > this.duration)){
            return false;
        }
        this.position = x;
        if(!silent)
            this.fire('update');
        if(this.followPlayCursor && (this.position > (this.offset + this.duration * this.scale))){
            this.offset = this.position;
        }
        this.render();
    };
    this.setDuration = function(x){
        this.duration = x;
        this.rightBorder = x;
        this.leftBorder = 0;
        this.offset = 0;
        this.scale = 1;
        this.setPosition(0);
    }
    this.setLeftBorder = function(x){
        if((x < 0) || (x > this.duration) || (x > this.rightBorder)){
            return false;
        }
        this.leftBorder = x;
        this.render();
    };
    this.setRightBorder = function(x){
        if((x < 0) || (x > this.duration) || (x < this.leftBorder)){
            return false;
        }
        this.rightBorder = x;
        this.render();
    };
    this.on = function(event, callback){
        if(event in this._listeners){
            this._listeners[event].push(callback);
        } else {
            this._listeners[event] = [callback];
        }
    }
    this.fire = function(event){
        for(event in this._listeners){
            this._listeners[event].forEach((f) => { f(this) });
        }
    };
    this.render = function(ctx){
        var w = this.element.width;
        var h = this.element.height;
        var ctx = this.element.getContext('2d');
        ctx.font = '400 11pt monospace';
        // timelines
        ctx.fillStyle = '#000';
        ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = '#222';
        ctx.fillRect(0, this.globalTimelineHeight, w, h - this.globalTimelineHeight);
        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, w, this.globalTimelineHeight - 4);
        // local cut area
        ctx.fillStyle = '#F004';
        ctx.fillRect(0, this.globalTimelineHeight, Math.floor(w * ((this.leftBorder - this.offset) / (this.duration * this.scale))), h);
        ctx.fillRect(Math.floor(w * ((this.rightBorder - this.offset) / (this.duration * this.scale))), this.globalTimelineHeight, w, h);
        // global cut area
        ctx.fillRect(0, 0, Math.floor(w * this.leftBorder / this.duration), this.globalTimelineHeight - 4);
        ctx.fillRect(Math.floor(w * this.rightBorder / this.duration), 0, w, this.globalTimelineHeight - 4);
        // local cursor
        ctx.fillStyle = '#FC0';
        var cursorX = Math.floor(w * ((this.position - this.offset) / (this.duration * this.scale)))
        ctx.fillRect(cursorX, this.globalTimelineHeight, 1, h - this.globalTimelineHeight);
        ctx.fillStyle = '#FFF';
        ctx.textAlign = 'left';
        ctx.fillText(self.formatSeconds(this.position), cursorX + 5, Math.floor(h / 2));
        // local timecodes
        ctx.textAlign = 'left';
        ctx.fillText(self.formatSeconds(self.offset), 5, h - 5);
        ctx.textAlign = 'right';
        ctx.fillText(self.formatSeconds(self.offset + this.scale * this.duration), w - 5, h - 5);
        // global cursor
        ctx.fillStyle = '#FF0';
        ctx.fillRect(Math.floor(w * (this.position / this.duration)), 0, 1, this.globalTimelineHeight - 4);
        // global window
        if(this.scale < 1){
            ctx.strokeStyle = '#FFF';
            ctx.strokeRect(Math.floor(w * (this.offset / this.duration)) + 0.5, 0.5, Math.floor(this.scale * w) - 1, this.globalTimelineHeight - 5);
        }
        // shadow cursor
        if(this.shadowPosition !== null){
            cursorX = Math.floor(w * ((this.shadowPosition - this.offset) / (this.duration * this.scale)));
            ctx.fillStyle = ((this.shadowPosition >= this.leftBorder) && (this.shadowPosition <= this.rightBorder)) ? '#080' : '#800';
            ctx.fillRect(cursorX, this.globalTimelineHeight, 1, h - this.globalTimelineHeight);
            ctx.fillStyle = '#888';
            ctx.textAlign = 'left';
            ctx.fillText(self.formatSeconds(this.shadowPosition), cursorX + 5, Math.floor(3 * h / 4));
        }
    };

    var self = this;
    element.addEventListener('mousedown', function(e){
        var w = self.element.width;
        var x = e.pageX - e.target.offsetLeft;
        var y = e.pageY - e.target.offsetTop;
        if(y > self.globalTimelineHeight){
            var position = self.offset + Math.round((x / w) * self.duration * self.scale);
            if((position < self.leftBorder) || (position > self.rightBorder)) return;
            self.setPosition(position);
        } else {
            var windowSize = w * self.scale;
            var windowPosition = x - windowSize / 2;
            if(windowPosition < 0){
                windowPosition = 0;
            } else if((w - windowPosition) < windowSize){
                windowPosition = w - windowSize;
            }
            self.offset = Math.floor(self.duration * windowPosition / w);
        }
        self.render();
    });
    element.addEventListener('mouseout', function(e){
        self.shadowPosition = null;
        self.render();
    });
    element.addEventListener('mouseup', function(e){
        /* var w = self.element.width;
        var x = e.pageX - e.target.offsetLeft;
        var y = e.pageY - e.target.offsetTop; */
    })
    element.addEventListener('mousemove', function(e){
        var w = self.element.width;
        var x = e.pageX - e.target.offsetLeft;
        var y = e.pageY - e.target.offsetTop;
        if(y > self.globalTimelineHeight){
            self.shadowPosition = self.offset + Math.round((x / w) * self.duration * self.scale);
        } else {
            self.shadowPosition = null;
        }
        self.render();
    });
}
