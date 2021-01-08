#!/usr/bin/env python

import datetime
import uuid
import urllib
import asyncio
import websockets
import json
import hmac
import base64
import hashlib
import gzip
import traceback
import pprint

class RestClient:
    def __init__(self):
        ####  input your access_key and secret_key below:
        self.__access_key  = "f2643261-4cfd9d14-ca908a0f-dbye2sf5t7"
        self.__secret_key  = "34ae74a1-853da993-eac728aa-f812f"
        self.__market_url = 'wss://www.hbdm.vn/ws'
        self.__order_url = 'wss://api.hbdm.vn/notification'


    def generate_signature(self, host, method, params, request_path, secret_key):
        """Generate signature of huobi future.
        Args:
            host: api domain url.PS: colo user should set this host as 'api.hbdm.com',not colo domain.
            method: request method.
            params: request params.
            request_path: "/notification"
            secret_key: api secret_key

        Returns:
            singature string.

        """
        host_url = urllib.parse.urlparse(host).hostname.lower()
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)
        payload = [method, host_url, request_path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode(encoding="UTF8")
        secret_key = secret_key.encode(encoding="utf8")
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        signature = signature.decode()
        return signature

    async def subscribe(self, url, access_key, secret_key, subs, callback=None, auth=False):
        """ Huobi Future subscribe websockets.

        Args:
            url: the url to be signatured.
            access_key: API access_key.
            secret_key: API secret_key.
            subs: the data list to subscribe.
            callback: the callback function to handle the ws data received. 
            auth: True: Need to be signatured. False: No need to be signatured.

        """
        async with websockets.connect(url) as websocket:
            if auth:
                timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                data = {
                    "AccessKeyId": access_key,
                    "SignatureMethod": "HmacSHA256",
                    "SignatureVersion": "2",
                    "Timestamp": timestamp
                }
                sign = generate_signature(url,"GET", data, "/notification", secret_key)
                data["op"] = "auth"
                data["type"] = "api"
                data["Signature"] = sign
                msg_str = json.dumps(data)
                await websocket.send(msg_str)
                print(f"send: {msg_str}")
            for sub in subs:
                sub_str = json.dumps(sub)
                await websocket.send(sub_str)
                #print(f"send: {sub_str}")
            while True:
                rsp = await websocket.recv()
                data = json.loads(gzip.decompress(rsp).decode())
                #print(f"recevie<--: {data}")
                if "op" in data and data.get("op") == "ping":
                    pong_msg = {"op": "pong", "ts": data.get("ts")}
                    await websocket.send(json.dumps(pong_msg))
                    print(f"send: {pong_msg}")
                    continue
                if "ping" in data: 
                    pong_msg = {"pong": data.get("ping")}
                    await websocket.send(json.dumps(pong_msg))
                    #print(f"send: {pong_msg}")
                    continue
                rsp = await callback(data)

    async def handle_liquidation(self, *args, **kwargs):
        """ callback function
        Args:
            args: values
            kwargs: key-values.
        """
        #print("callback param", *args, **kwargs)
        pprint.pprint(*args)

    def subscribeLiquidation(self, callback):
        liquidation_subs = [
                {
                    "op": "sub",
                    "topic": "public.BTC.liquidation_orders",
                    "cid": str(uuid.uuid1())
                }
            ]
 
        while True: 
            try:
                asyncio.get_event_loop().run_until_complete(subscribe(self.__market_url, self.__access_key,  self.__secret_key, liquidation_subs, self.handle_liquidation, auth=False))
            except Exception as e:
                traceback.print_exc()
                print('websocket connection error. reconnect rightnow')

if __name__ == "__main__":
    print('')