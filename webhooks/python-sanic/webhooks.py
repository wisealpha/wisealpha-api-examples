import base64
import binascii
import hashlib
import hmac
import json
import os

from sanic import Sanic
from sanic.response import json

app = Sanic()


@app.route("/")
async def home(request):
    return json({"hello": "world"})


@app.route("/webhooks", methods=['POST', 'GET'])
async def webhooks(request):
    calculated = None
    try:
        print('')
        print('-' * 120)

        signature = request.headers.get('x-wisealpha-signature', '')
        key_bytes = base64.b64decode(os.environ.get('WA_WEBHOOK_KEY', ''))
        calculated = base64.b64encode(hmac.new(key_bytes, request.body, digestmod=hashlib.sha256).digest()).decode(encoding='ascii')

        if signature == calculated:
            # Process request
            print('VALID WEBHOOK')
            print(request.body)
        else:
            print('SIGNATURE CHECK FAILED')
        
        print('-' * 120)
        print('')
    except Exception as ex:
        print(str(ex))
    return json({"valid": signature == calculated})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9999)
