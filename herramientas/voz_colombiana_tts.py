import sys, certifi, asyncio
certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
import edge_tts
async def main(text, voice, out, rate="+0%"):
    c = edge_tts.Communicate(text, voice, rate=rate)
    subs=[]
    with open(out,"wb") as f:
        async for ch in c.stream():
            if ch["type"]=="audio": f.write(ch["data"])
            elif ch["type"] in ("WordBoundary","SentenceBoundary"): subs.append((ch["type"],ch["offset"]/1e7,ch["duration"]/1e7,ch["text"]))
    import json; json.dump(subs, open(out+".json","w"), ensure_ascii=False)
asyncio.run(main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv)>4 else "+0%"))
