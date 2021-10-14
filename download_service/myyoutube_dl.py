import subprocess
import youtube_dl

class Error(BaseException):

    def __init__(self, return_code):
        super().__init__()
        self.return_code = return_code


class YoutubeDl:
    def __init__(self):
        super().__init__()
        self.global_opts = []
        self.process_ids = {}
        self.link = ""

    def input(self, link):
        self.link = link
        print(self.link)
        return self

    def resume(self):
        self.global_args("-c")
        subprocess.run(self.args())

    def stop(self):
        proc = self.process_ids[self.link]
        proc.terminate()
        print(str(self.process_ids[self.link]))
        return proc
        #os.killpg(os.getpgid(self.process_ids[self.link]), signal.SIGINT)

    def global_args(self, *args, **kwargs):
        self.global_opts += args
        for k, v in kwargs.items():
            self.global_opts.append(k)
            self.global_opts.append(v)
        print(self.global_opts)
        return self

    def args(self):
        result = ["/usr/local/bin/youtube-dl"]
        result += self.global_opts
        result.append(self.link)
        return result

    def run(self, wait=True):
        if wait is True:
            print(self.args())
            process = subprocess.Popen(self.args(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
            self.process_ids[self.link] = process
            output, errors = process.communicate()
            return_code = process.poll()
            print(self.process_ids)
            print(return_code)
            if return_code != 0:
                print('YoutubeDl returned {}\nStdout: {}\nStderr: {}'.format(return_code, output.decode('utf-8'), errors.decode('utf-8')))
            return return_code
        else:
            return subprocess.Popen(self.args(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == "__main__":
    youtube_dl = YoutubeDl()
    youtube_dl.input("https://www.youtube.com/watch?v=INppOzzjUAY").global_args().run()
