# lambda-transcription-function
Contains the python script &amp; necessary packages to upload

Lambda Functin Description:

    This function detects when a file lands in an S3 bucket, thus triggering it.
    The file is then downloaded to a temporary file, where it is then transcribed using Azure openAI's Whisper API, which transcribes the file. As of 11/16/23, the open.audio.transcribe() function is deprecated, but we use version 0.28, which routes this file to Azure's Whisper, instead of OpenAI's whisper.
    The transcribed file is then cleaned/de-identified, and then analized by feeding chatGPT a series of prompts, as well as the transcript.
    The results from this analysis are then returned and saved in a database.


Steps to update Lambda function in AWS:

1. Make change to lambda_function.py
2. Drag lambda_function.py into the 'package' folder
3. Click into the 'package' folder and select all files
4. Right-click, select "compress", and create a zip file containing all files inside 'package'. Name it whatever you want, but keep track of it.
    You might not be able to do this from your IDE, and will have to compress from your file explorer.
5. Go to the Lambda function url in AWS, select the Lightbulb-AI-processing-service, and in the code tab click 'Upload From'. Select 'Upload From Zip'.
6. Upload the zip file and once the color accents turn green, the Lambda function is ready to use
