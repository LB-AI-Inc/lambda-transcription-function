import json
import requests
import urllib
import openai
import boto3
import os
import re
import time
import subprocess


def replace_ssns(string):
    ssn_pattern = r'\b(\d{3}-\d{2}-\d{4}|\d{9})\b'
    result_string = re.sub(ssn_pattern, 'XXX-XX-XXXX', string)
    return result_string

def replace_credit_card_numbers(input_string):
    card_number_pattern = r'\b(\d{4}-?\d{4}-?\d{4}-?\d{4}|\d{16})\b'
    result_string = re.sub(card_number_pattern, 'XXXXXXXXXXXXXXXX', input_string)
    return result_string

def replace_4_digits(string):
    four_digit_pattern = r'\b\d{4}\b'
    result_string = re.sub(four_digit_pattern, 'XXXX', string)
    return result_string

def replace_digits_with_x(string):
    result_string = ''.join(['X' if char.isdigit() else char for char in string])
    return result_string

def move_file(source_bucket, source_key, destination_bucket, destination_key):
    s3 = boto3.client('s3')
    try:
        # Copy the object
        s3.copy_object(
            Bucket=destination_bucket,
            Key=destination_key,
            CopySource={
                'Bucket': source_bucket,
                'Key': source_key
            }
        )

        # Delete the original object
        s3.delete_object(
            Bucket=source_bucket,
            Key=source_key
        )

        print(f"File moved from {source_bucket}/{source_key} to {destination_bucket}/{destination_key}")
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def with_function(question, system_prompt, transcript, engine):
    functions = [{
            'name': 'answer_generator',
            'description': 'Get an answer to the question',
            'parameters': {
                'type': 'object',
                'properties': {
                    'answer': {
                        'type': 'boolean',
                        'description': question,
                    },
                    'reasoning': {
                        'type': 'string',
                        'description': 'Explain your reasoning.'
                    }
                }
            }
        }]

    response = openai.ChatCompletion.create(
        engine=engine,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": transcript
            }
        ],
        functions=functions,
        function_call={
            "name": "answer_generator",
        },
    )
    return response

def without_function(question, system_prompt, transcript, engine):
    response = openai.ChatCompletion.create(
            engine=engine,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": transcript + "\n\nQuestion: " + question
                }
            ]
        )
    return response

def get_openai_credentials():
    secret_name = "openAI_credentials"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    # Retrieve the secret
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])

        # Extract OpenAI and WhisperAI credentials
        openai_credentials = {
            'api_key': secret.get('OpenAI', ''),
            'api_base': "https://lightbulb.openai.azure.com/",
            'api_version': "2023-07-01-preview"
        }
        whisperai_credentials = {
            'api_key': secret.get('WhisperAI', ''),
            'api_base': "https://lightbulb-whisper.openai.azure.com/",
            'api_version': "2023-09-01-preview"
        }
        return openai_credentials, whisperai_credentials

    except Exception as e:
        print(f"Error retrieving OpenAI and WhisperAI credentials from Secrets Manager: {e}")
        return None, None

def get_deepgram_credentials():

    secret_name = "Deepgram_credentials"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(response['SecretString'])
        deepgram_api_key = secret.get('deepgram_api_key', '')
        return deepgram_api_key
    except Exception as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        print(f"Error retrieving Deepgram credentials from Secrets Manager: {e}")
        return None

def get_audio_duration(file_path):
    try:
        # Command to get audio duration using FFMPEG
        output_file = '/tmp/output.mp3'  # Output file path
        p1 = subprocess.run(["/opt/ffmpeg", "-i", file_path, output_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration_pattern = re.compile(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)")
        duration_match = duration_pattern.search(p1.stderr.decode("utf-8"))

        if duration_match:
            hours, minutes, seconds = map(float, duration_match.groups())
            total_seconds = (hours * 3600) + (minutes * 60) + seconds
            os.remove(output_file)
            return round(total_seconds)
        else:
            return None

    except subprocess.CalledProcessError as e:
        # Handle FFMPEG command execution errors
        print("FFMPEG error:", e)
        return None

def analyze(transcript, openai_credentials, prompts):
    # initialize the chat completion azure creds
    api_key, api_base, api_version = openai_credentials['api_key'], openai_credentials['api_base'], openai_credentials['api_version']
    openai.api_key = api_key
    openai.api_base = api_base
    openai.api_version = api_version

    # system_prompt = "You are an expert sales coach. You are helping critique a call for people to gather data and help people improve. Answer the questions as asked and provide clear details when asked for. The transcript is provided and be clear that there could be multiple people on the call. Do not include any Social Secuirty numbers in your response, this is sensitive information."
    system_prompt = "You are an expert quality assurance manager for an inbound call center. You are helping critique inbound calls made by customers, who we’ll refer to as participants, to our company representatives. Answer the questions as asked and provide clear details when asked for. The transcript of the call is provided and there are multiple people on the call- the participant (the customer) and the representative of the company (whose performance you are evaluating). On all calls, reps are required to verify the Social Security number of the caller for security reasons. Do not criticize the rep for asking for sensitive information like this, as it is a part of the standard process."

    results = {}
    for question in prompts:

        if prompts[question]['graded']:
            response = with_function(prompts[question]['question'], system_prompt, transcript, prompts[question]['engine'])
        elif not prompts[question]['graded']:
            response = without_function(prompts[question]['question'], system_prompt, transcript, prompts[question]['engine'])


        print(json.dumps(response))
        try:
            if prompts[question]['graded']:
                results[question] = {
                    "type": question,
                    "graded": prompts[question]['graded'],
                    "raw": response['choices'][0]['message']['function_call']['arguments'],
                    # "grade": answer['answer'],
                    # "reasoning": answer['reasoning']
                }
            elif not prompts[question]['graded']:
                results[question] = {
                    "type": question,
                    "graded": prompts[question]['graded'],
                    "raw": response['choices'][0]['message']['content']
                }
        except Exception as e:
            print("Exception in formatting response:", json.dumps(e))
        if results[question]['type'] != "StrengthAssessment" and results[question]['type'] != "WeaknessAssessment" and results[question]['type'] != "Gist":
            results[question]['raw'] = replace_digits_with_x(results[question]['raw'])
        print(json.dumps(results[question]))
    # returns a dictionary of results and a boolean indicating success
    return results, True

def notify_server(url, bucket, key, callCreate):
    data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": '',
                "transcript": '',
                "success": '',
                "callCreate": callCreate,
                "status": "Analyzing"
            })
    request = requests.post(url, data=data)
    print("Analyzing:", request)
    # print(json.dumps(request))

def create_prompt_list(prompts):
    promptList = {}
    for prompt in prompts:
        promptList[prompt['type']] = {
            "type": prompt['type'],
            "question": prompt['question'],
            "graded": prompt['graded'],
            "engine": prompt['engine']
        }
    return promptList

def retrieve_prompts(url, workflowId):
    request = requests.get(url+"/api/prompt-workflow?workflowId="+workflowId)
    print(request.json())
    workflow = request.json()['workflow']
    # print("Retrieving prompts:", workflow)
    return create_prompt_list(workflow)

def lambda_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print(json.dumps(event))
    # workflowId = event['Records'][0]['responseElements']['x-amz-meta-workflowid']
    key_lower = key.lower()

    # -----------------------------------------------------
    # destination server info:
    # change this if you're working in different environments

    prod_domain = 'app.lightbulb.ai'
    dev_domain = 'dev.lightbulb.ai'
    api_route = '/api/call-data'

    # destination_bucket = 'lightbulb-prod-output'
    destination_bucket = 'lightbulb-dev-output'

    prod_stub = "https://"+prod_domain
    dev_stub = "https://"+dev_domain
    test_stub = "https://8dec-136-62-209-37.ngrok-free.app"
    # url = prod_stub+api_route
    # url = dev_stub+api_route
    url = test_stub+api_route
    # -----------------------------------------------------

    haveTranscript = False
    haveResponse = False
    openai.api_type = "azure"
    result = 'empty'
    transcript = ''
    masked_transcript = ''
    segments = []
    error = ''
    audio_duration = 0
    workflow = {}

    # Download file from S3
    local_file_path = '/tmp/'+key
    s3client = boto3.client('s3')
    s3client.download_file(bucket, key, local_file_path)
    s3_response = s3client.head_object(Bucket=bucket, Key=key)
    metadata = s3_response.get('Metadata', {})
    workflowId = metadata['workflowid']
    callCreate = metadata['callcreate']
    # print("Metadata:", metadata)
    print("Workflow ID:", workflowId)
    print("Downloading", key, "from", bucket, local_file_path)
    openai_credentials, whisper_credentials = get_openai_credentials()

    try:
        notify_server(url, bucket, key, callCreate)
    except Exception as e:
        print("Exception while phoning home:", json.dumps(e))

    try:
        workflow = retrieve_prompts(test_stub, workflowId)
        print("Retrieved:", workflow)
    except Exception as e:
        print("Exception while retrieving prompts:", e)

    try:

        if not key_lower.endswith(('.wav', '.mp3')) or re.search(r'\.(wav|mp3)\s*\(\d+\)$', key_lower):
            raise Exception("Bad file format")
        print("Filepath: ", local_file_path)
        audio_duration = 0
        # audio_duration = get_audio_duration(local_file_path)
        # print("Audio Duration: ", audio_duration)


        ### initialize whisper azure creds
        api_key, api_base, api_version = whisper_credentials['api_key'], whisper_credentials['api_base'], whisper_credentials['api_version']
        openai.api_key = api_key
        openai.api_base = api_base
        openai.api_version = api_version

        ### initialize deepgram
        deepgram_api_key = get_deepgram_credentials()

        delay = 0
        maxAttempts = 5
        attempt = 0
        while (len(transcript) == 0 and attempt < maxAttempts):
            print("Beginning transcript loop")
            errorPresent = False
            try:
                # attempts to transcribe audio file
                print("Attempt #", attempt, "of", maxAttempts,"; Delay:", delay)
                time.sleep(delay)
                with open(local_file_path, 'rb') as file:
                    buffer_data = file.read()

                    response = requests.post(
                        "https://api.deepgram.com/v1/listen?smart_format=true&model=nova-2&language=en-US&redact=pci&diarize=true&redact=account_number&redact=age&redact=dob&redact=driver_license&redact=email_address&redact=healthcare_number&redact=ip_address&redact=location_address&redact=location_city&redact=location_coordinate&redact=location_country&redact=location_state&redact=location_zip&redact=marital_status&redact=name_family&redact=name_given&redact=name_medical_professional&redact=numerical_pii&redact=passport_number&redact=password&redact=phone_number&redact=ssn&redact=username&redact=vehicle_id",
                        headers={
                            "Authorization": "Token " + deepgram_api_key,
                        },
                        data=buffer_data
                    ).json()

                    print("Deepgram response:", response)
                    transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
                    segments = response['results']['channels'][0]['alternatives'][0]['paragraphs']

                    # transcript = openai.Audio.transcribe(
                    #     deployment_id="whisper-model",
                    #     model="whisper-1",
                    #     file=file
                    #     )['text']
                print("Closing file...")
                file.close()
                    # replaces SSNs with XXX-XX-XXXX
                if len(json.dumps(transcript)) > 0:
                    print("Success generating transcript; exiting loop")
                    haveTranscript = True
            except Exception as e:
                error = e
                attempt += 1
                if delay == 0:
                    delay = 10
                else:
                    delay = delay * 2
                print("Exception in transcription:", e)
                print("Current delay:", delay, "; Attempt", attempt, "of", maxAttempts," for file ", key)


    except Exception as e:
        error = e
        print("Could not open file:", e)

    try:
        # delete the file from the /tmp directory
        os.remove(local_file_path)
        print("Deleted file /tmp/"+key)
    except Exception as e:
        error = e
        print("Exception in deleting file:", e)

    if len(transcript) > 0:
        print("Transcript is present")
    else:
        print("Transcript is empty")

    try:
        # analyze the transcript with the given prompts
        if transcript:
            result, haveResponse = analyze(transcript, openai_credentials, workflow)
    except Exception as e:
        error = e
        print("Exception in Q&A:", e)

    try:
        # Indicates success or failure - can be redirected to a different server
        if haveTranscript & haveResponse:
            # replaces SSNs with XXX-XX-XXXX
            masked_transcript = replace_digits_with_x(transcript)
            if len(masked_transcript) > 0:
                print("Masked transcript is present")
            else:
                print("Masked transcript is empty")

            destination_key = key
            move_file(bucket, key, destination_bucket, destination_key)
            data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": json.dumps(result),
                "transcript": json.dumps(masked_transcript),
                "raw_transcript": json.dumps(transcript),
                "segments": json.dumps(segments),
                "workflowId": workflowId,
                "success": "true",
                "status": "Completed"
            })
            request = requests.post(url, data=data)
            print("Success:", request)

        else:
            data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": json.dumps(result),
                "transcript": json.dumps(masked_transcript),
                "raw_transcript": json.dumps(transcript),
                "segments": json.dumps(segments),
                "workflowId": workflowId,
                "success": "false",
                "status": "Error",
                # "errorMessage": json.dumps(error)
            })
            request = requests.post(url, data=data)
            print("Error:", request)
    except Exception as e:
        data = json.dumps({
            "bucket": bucket,
            "key": key,
            "result": json.dumps(result),
            "transcript": json.dumps(masked_transcript),
            "raw_transcript": json.dumps(transcript),
            "segments": json.dumps(segments),
            "workflowId": workflowId,
            "success": "false",
            "status": "Error",
            # "errorMessage": json.dumps(error)
        })
        request = requests.post(url, data=data)
        print("Error:", request)
        print("Exception while phoning home:", json.dumps(e))

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from bucket %s-%s'%(bucket,key))
    }