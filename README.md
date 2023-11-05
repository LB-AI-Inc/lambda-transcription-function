# lambda-transcription-function
Contains the python script &amp; necessary packages to upload

Steps to update Lambda function:

1. Make change to lambda_function.py
2. Drag lambda_function.py into the 'package' folder
3. Click into the 'package' folder and select all files
4. Right-click, select "compress", and create a zip file containing all files inside 'package'. Name it whatever you want, but keep track of it.
5. Go to the Lambda function url in AWS, select the Lightbulb-AI-processing-service, and in the code tab click 'Upload From'. Select 'Upload From Zip'.
6. Upload the zip file and once the color accents turn green, the Lambda function is ready to use
