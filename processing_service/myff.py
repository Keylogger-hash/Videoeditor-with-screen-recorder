import subprocess, json

PROBE_TIMEOUT = 60


class Error(BaseException):

    def __init__(self, return_code):
        super().__init__()
        self.return_code = return_code


class FFmpeg:

    def __init__(self):
        self.global_opts = []
        self.sources = []
        self.outputs = []

    def input(self, location, *args, **kwargs):
        options = []
        for k, v in kwargs.items():
            if isinstance(v, list):
                for item in v:
                    options.append('-{}'.format(k))
                    if item is not None:
                        options.append(item)
            else:
                options.append('-{}'.format(k))
                if v is not None:
                    options.append(v)
        for item in args:
            options.append(item)
        self.sources.append({
            'location': location,
            'options': options
        })
        return self

    def output(self, location, *args, **kwargs):
        options = []
        for k, v in kwargs.items():
            if isinstance(v, list):
                for item in v:
                    options.append('-{}'.format(k))
                    if item is not None:
                        options.append(item)
            else:
                options.append('-{}'.format(k))
                if v is not None:
                    options.append(v)
        for item in args:
            options.append(item)
        self.outputs.append({
            'location': location,
            'options': options
        })
        return self

    def global_args(self, *args, **kwargs):
        self.global_opts += args
        for k, v in kwargs.items():
            self.global_opts.append('-{}'.format(k))
            self.global_opts.append(v)
        return self

    def args(self):
        result = ['/usr/bin/ffmpeg']
        result += self.global_opts
        for source in self.sources:
            for item in source['options']:
                result.append(item)
            result.append('-i')
            result.append(source['location'])
        for output in self.outputs:
            for item in output['options']:
                result.append(item)
            result.append(output['location'])
        return result

    def run(self, wait=True):
        if wait is True:
            # return subprocess.call(self.args())
            process = subprocess.Popen(self.args(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, errors = process.communicate()
            return_code = process.poll()
            if return_code != 0:
                print('Ffmpeg returned {}\nStdout: {}\nStderr: {}'.format(return_code, output.decode('utf-8'), errors.decode('utf-8')))
                raise Error(return_code)
            else:
                return return_code
        else:
            return subprocess.Popen(self.args(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class FFprobe:

    def __init__(self):
        self.global_opts = []
        self.source = 'null'

    def options(self, **kwargs):
        for k, v in kwargs.items():
            self.global_opts.append('-' + k)
            if v is not None and not isinstance(v, bool):
                self.global_opts.append(v)
        return self

    def input(self, location):
        self.source = location
        return self

    def args(self):
        result = ['/usr/bin/ffprobe']
        result += self.global_opts
        result.append(self.source)
        return result

    def json(self):
        self.global_opts += ['-of', 'json']
        probe = subprocess.Popen(
            self.args(),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
            )
        try:
            output, errors = probe.communicate(timeout=PROBE_TIMEOUT)
            exit_code = probe.poll()
            if exit_code != 0:
                print('Ffmpeg returned {}\nStdout: {}\nStderr: {}'.format(exit_code, output.decode('utf-8'), errors.decode('utf-8')))
                raise Error(exit_code)
            if output is None:
                raise Error(-1)
            return json.loads(output.decode('utf-8'))
        except subprocess.TimeoutExpired as e:
            probe.kill()
            raise Error(-1) from e
