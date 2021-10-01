import subprocess


def download(link: str):
    args = ["youtube-dl", link]
    subprocess.run(args)
    return "Success"