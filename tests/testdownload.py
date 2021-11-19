import requests

downloaded = 0
with requests.get("https://r3---sn-hpg5avbpj-n8ml.googlevideo.com/videoplayback?expire=1637243573&ei=VQaWYYfxFcq11gLu_b6IDg&ip=5.189.98.210&id=o-AIPmgPqejxZeg82c0cLHgeETmsrbGCgj4Nd8mGvsgAuQ&itag=298&aitags=133%2C134%2C135%2C136%2C160%2C242%2C243%2C244%2C247%2C278%2C298%2C302&source=youtube&requiressl=yes&mh=iS&mm=31%2C29&mn=sn-hpg5avbpj-n8ml%2Csn-n8v7kne7&ms=au%2Crdu&mv=m&mvi=3&pcm2cms=yes&pl=17&initcwndbps=1916250&vprv=1&mime=video%2Fmp4&ns=wIWipoOIYzgQdf3MHuas-NsG&gir=yes&clen=14435843&otfp=1&dur=74.020&lmt=1550544338918687&mt=1637221506&fvip=5&keepalive=yes&fexp=24001373%2C24007246&c=WEB&txp=2216222&n=773a3XCQRDJvKEm&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cns%2Cgir%2Cclen%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRQIhAIBWuckmCrYlRHoGTFFAadAaOA76THE8KbVSOS0xWOgkAiBVoF6MNCvN-VMNBhwd0pPvz2hjB5GhCWQOkIPuWCIReA%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRAIgFXcGS2fj-9QyCQ5T7cYLoGQgW4OF96FSDWmQgLhK6jwCIDKgaJShMyN2NZelMI-F6msx7rP2GsMEgwrsV2zwD4AM",stream=True) as r:
    total = int(r.headers['Content-Length'])
    print(total)
    for i in r.iter_content():
        downloaded += len(i)
        print(downloaded)
