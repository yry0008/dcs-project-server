import fastapi
from threading import Thread,Event
import configloader
import logging
import random
import time
import uvicorn
import tools
from fastapi import Form
logging.basicConfig(
    level=getattr(logging,"INFO"), format="%(asctime)s [%(levelname)s][%(pathname)s:%(lineno)d]: %(message)s"
)
class makereq(Thread):
    def __init__(self,nodeid):
        Thread.__init__(self)
        self.c = configloader.config()
        self.has_stop = False
        self.event = Event()
        self.nodeid = nodeid
        self.ok=False
        self.start()



    def run(self):
        try:
            import requests
            r = requests.get(self.c.getkey("nodes")[self.nodeid]["host"]+"/getnum",timeout=5)
            if r.status_code == 200:
                self.ok=True
                self.lastnum = r.json()["num"]
            else:
                self.ok=False
        except:
            self.ok=False
            import traceback
            logging.error(traceback.format_exc())

app = fastapi.FastAPI()
c = configloader.config()
@app.post("/newserver")
async def newserver(myhost=Form(),myip=Form()):
    if not (myhost.startswith("http://") or myhost.startswith("https://")):
        return {"ret":1,"msg":"Invalid Host"}
    newid = tools.genuuid()
    c.dic["nodes"][newid]={
        "host":myhost,
        "lasttime":time.time(),
        "ip":myip
    }
    c.save()
    c.reload()
    return {"ret":0,"id":newid}

@app.post("/healcheck")
async def healcheck(nodeid=Form(),myhost=Form(),myip=Form()):
    if nodeid not in c.dic["nodes"]:
        return {"ret":1,"msg":"Invalid Node ID"}
    c.dic["nodes"][nodeid]["lasttime"] = time.time()
    c.dic["nodes"][nodeid]["host"] = myhost
    c.dic["nodes"][nodeid]["ip"] = myip
    c.save()
    c.reload()
    return {"ret":0}

@app.get("/getnums")
async def getnums():
    ret = []
    for i in c.dic["nodes"]:
        if c.dic["nodes"][i]["lasttime"]+c.getkey("timeout") > time.time():
            ret.append(makereq(i))
    ans = {

    }
    ans_sum = 0
    for i in ret:
        if i.is_alive():
            i.join()
        if i.ok:
            ans[i.nodeid] = i.lastnum
            ans_sum += i.lastnum
        else:
            ans[i.nodeid] = "Error"
            c.dic["nodes"][i.nodeid]["lasttime"]=0
    return {
        "ret":0,
        "server_data":ans,
        "sum":ans_sum
    }

if __name__ == "__main__":
    uvicorn.run(app,host=c.getkey("bind"),port=c.getkey("port"))