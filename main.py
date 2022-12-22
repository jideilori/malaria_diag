from fastapi import FastAPI, UploadFile, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

import io
from PIL import Image
import json
import numpy as np
import uuid
import logging
import sys
from typing import Optional, Any
from pathlib import Path
from typing import List
import requests
import json
import datetime
from google.cloud import storage


api_url = 'https://mp-api-app-zgymkx5l6a-uc.a.run.app/predict'
# local_api_url = 'http://0.0.0.0:8080/predict'

import cv2


def upload_blob(bucket_name, contents, destination_blob_name):
    """Uploads a file to the bucket."""

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(contents)
    return blob.public_url


def generate_download_signed_url_v4(bucket_name, blob_name):
    """Generates a v4 signed URL for downloading a blob.

    Note that this method requires a service account key file. You can not use
    this if you are using Application Default Credentials from Google Compute
    Engine or from the Google Cloud SDK.
    """
    # bucket_name = 'your-bucket-name'
    # blob_name = 'your-object-name'

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=datetime.timedelta(minutes=15),
        # Allow GET requests using this URL.
        method="GET",
    )

    print("Generated GET signed URL:")
    # print(url)
    return url





logging.basicConfig(stream=sys.stdout, level=logging.INFO)
app = FastAPI(
    title="Malaria detection",
    description="""Detect and count malaria parasites and white blood cells""",
    version="0.0.1",
)


origins = [
    "http://localhost",
    "http://localhost:8000",
    "*"
]
app.add_middleware(
     CORSMiddleware,
     allow_origins=origins,
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)


BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(Path(BASE_PATH ,"templates")))
app.mount("/static", StaticFiles(directory="static"), name="static") 

result_data =None

@app.route('/')
async def index(request: Request): 
   
    return TEMPLATES.TemplateResponse('index.html', context={'request': request,'data':result_data})
   

@app.post('/')
async def predict(request: Request,files: List[UploadFile]): 
    global result_data

    result_data = {}
    send_img={}
    for vals,img in enumerate(files): 
        # generate unique id to store image in bucket
        img_id = uuid.uuid4()
    
        read_img = Image.open(io.BytesIO(img.file.read()))
        read_img = read_img.resize((4032,3024))
        success, encoded_image = cv2.imencode('.jpg', np.array(read_img))
        read_img_bytes = encoded_image.tobytes()

        upload_blob(bucket_name='mpdiag_bucket_v2',contents=read_img_bytes,destination_blob_name=f'{img_id}.jpg')

        send_img[f'img_{vals}'] =f'{img_id}.jpg'
        json_data = json.dumps(send_img)     

        
        response = requests.post(api_url,data=json_data)
        result_data[f'{vals}'] = response.json()

      
    redirect_url = request.url_for('index')    
    return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)    



    
# run with in terminal
# uvicorn main:app --reload --host 0.0.0.0 --port 8000

