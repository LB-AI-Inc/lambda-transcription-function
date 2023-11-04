import json
import requests
import urllib
import openai
import boto3
import os
import re


def replace_ssns(string):
    ssn_pattern = r'\b(\d{3}-\d{2}-\d{4}|\d{9})\b'
    result_string = re.sub(ssn_pattern, 'XXX-XX-XXXX', string)
    return result_string

def replace_credit_card_numbers(input_string):
    card_number_pattern = r'\b(\d{4}-?\d{4}-?\d{4}-?\d{4}|\d{16})\b'
    result_string = re.sub(card_number_pattern, 'XXXXXXXXXXXXXXXX', input_string)
    return result_string

def analyze(transcript):

    # initialize the chat completion azure creds
    openai.api_key = ""
    openai.api_base = ""
    openai.api_version = ""

    system_prompt = "You are an expert sales coach. You are helping critique a call for people to gather data and help people improve. Answer the questions as asked and provide clear details when asked for. The transcript is provided and be clear that there could be multiple people on the call. Do not include any Social Secuirty numbers in your response, this is sensitive information."

    ## v1
    # promptList = [
    #     "Did the representative begin the call by saying Nue Synergy or Plan Source? Answer should be either Plan Source or Nue Synergy.",
    #     "What was the name of the representative who answered the phone call?",
    #     "What was the name of the customer who called in asking for help?",
    #     'Did the representative greet the participant by saying "Thank you for calling NueSynergy/PlanSource my name is (Their Name)" or something similar to this? (They must include their name and NueSynergy/PlanSource in their greeting)',
    #     "Did the representative ask all the required security verification questions? (Must include: First and Last Name, Last four digits of their Social Security, Number, Mailing Address, Employer name and Email or Phone Number) Reps can pull up participant by card number but they still need to verify last 4 digits of SSN at bare minimum for security verification completion.",
    #     'Did the representative ask, "How can I help you today?" or something similar to this?',
    #     'Did the representative ask relevant questions to further understand the reasoning behind why the customer contacted NueSynergy?',
    #     'Did the representative provide the participant with thorough and accurate responses to all questions?',
    #     'If applicable, did the representative check in with the participant every minute to avoid the participant experiencing a long hold time as well as providing reassurance that they are still working on a resolution to the issue?',
    #     'Did the rep ask for permission to transfer the call and let them know they will be transferring them?',
    #     'Did the call end abruptly, or was there a formal goodbye?',
    #     'Did the rep review what they discussed with the customer on this call, clarify the solution, and thank the participant for calling?',
    #     'Did the representative provide a recap of their concern(s) along with the resolution and ask if they had any additional questions before ending the call?',
    #     'Did the representative ask if the participant would like to stay on the line to take a brief survey to provide feedback on their call? Or did they say “please hold for a brief survey.”',
    #     'Did the representative complete the call with a proper closing? (Ex: “Thank you for calling and have a great day!")',
    #     'Did the representative treat the participant with courtesy? For example: Ask the participant how they like to be addressed, do their best to pronounce their name correctly, and use this name consistently?',
    #     'Based on the language used by the rep, how positive was their tone and sentiment? Did they display an engaged, pleasant tone?',
    #     'Did the representative wait for the participant to finish talking before speaking? If they interrupt in error, did they apologize for the interruption?',
    #     'Did the representative treat the participant with respect by trying to understand the cause of the participant’s problem, understand how their problem affects their behavior, and respond with empathy?',
    #     'Did the rep give accurate answers in a confident tone that addressed the concern of the customer directly?',
    #     "Did the representative exhibit interest in the participant's questions or concerns?",
    #     "Did the representative show effort in solving the participant's issue with the goal of achieving a solution on the call?",
    #     "If applicable, did the representative show an effort in de-escalating the situation? Did they use Empathy statements, calm direct tone, and clear understanding of the problem, and statements to let the participant know the agent is working diligently to solve the issue.",
    #     "Did the representative place a note in the participant's interaction with a clear outline of the member's concerns, actions taken, and resolution?",
    #     "If additional assistance was required where other department(s) needed to be involved, did the representative follow up within two business days? Did the representative place a follow up note in participant's interaction with a clear outline?",
    #     "Identify elements of the call where the rep was performing positively. Act as a coach giving encouraging feedback to the rep for what they did right on this call.",
    #     "Identify elements of the call where the rep was performing poorly. Act as a coach giving feedback on what the rep can be doing better on the call to follow guidelines above. Summarize any aspects of the required process that they missed, and how they can improve next time.",
    #     "What was the main concern of the customer?"
    # ]

    ## v2
    # promptList = [
    #     "Was this call related to Nue Synergy or Plan Source? Answer should be either PlanSource or NueSynergy. No need to provide reasoning here, just the answer.",
    #     "What was the name of the representative who answered the phone call? No need to provide reasoning here, just the answer.",
    #     "What was the name of the customer who called in asking for help? No need to provide reasoning here, just the answer.",
    #     "Did the representative greet the participant by saying something like 'Thank you for calling NueSynergy” or “PlanSource my name is (Their Name)' or something similar to this? Another example would be 'Plansource or Nuesynergy, This is (THEIR NAME) how can I help you?' The rep must say their name and NueSynergy/PlanSource in their greeting. to get credit for this. If the rep introduced themselves by stating their company name, and their personal name, respond with ‘1 = yes.’ If they did not say their name and either plan source or nue synergy, respond with ‘0 = no.’ Explain your reasoning in a separate line.",
    #     "Did the participant disclose their social security number? Either the full number or their last four digits? If they didn’t verify the social, did they verify the If yes, respond with ‘1 =yes’ If no, respond with ‘0 = no’. Explain your reasoning in a separate line. Do not repeat the number in your reasoning.",
    #     "Did the representative ask, 'How can I help you today?' or something similar to this? If they did ask this or something very similar, respond with yes = 1. If they did not ask a question to understand why the client called, respond with 0 = no. Explain your reasoning.",
    #     "Did the representative ask relevant questions to further understand the reasoning behind why the customer contacted NueSynergy? If they did, respond with 1 = yes. If they didn’t, respond with 0 = no. Explain your reasoning.",
    #     "Does it appear that the representative used all the available resources they have at their disposal to resolve the customer’s issue? If they are taking a long time to answer the question, not seeming confident in their answers, or the customer is confused, this is likely evidence that they should have utilized additional resources to answer the call. If they did use all available resources, respond with 1 = yes. If the issue was resolved on this call, and it isn’t obvious that the rep was taking a long time to answer, not seeming confident, or the customer wasn’t confused by the rep’s responses, respond with 1 = N/A. If the rep did take a long time to answer questions, or wasn’t confident, or confused the customer, respond with 0 = no. Explain your reasoning.",
    #     "Did the representative provide the participant with thorough and accurate responses to all questions? If they did, respond with 1 = yes. If they did not, respond with 0 = no. Explain your reasoning.",
    #     "Based on the reasoning and progression of the call, should the representative have placed the participant on hold while investigating the issue? If there is a long silence, greater than a minute, the rep should place the participant on hold. Respond with either 1 or 0 and Use the following logic in your response: 1 = They should have placed the call on hold, and they DID place the call on hold. 0 = They should have placed the call on hold, and they DID NOT place the call on hold. 1 = They should NOT have placed the call on hold, and they DID NOT place the call on hold. 0 = They should NOT have placed the call on hold, and they DID place the call on hold. 1 = N/A/. Explain your reasoning.",
    #     "If the rep placed the customer on hold (evidence of this would be the rep saying they are placing the customer on a brief hold), did the representative check in with the participant every minute? Respond with either 1 or 0 and use the following logic in your response: 1 = Yes, 0 = No, 1 = N/A. If the rep did not tell the participant they will place them on hold, the answer will always be 1 = N/A. Explain your reasoning.",
    #     "If applicable, should the representative have transferred the call? This is applicable if the customer called the wrong department, were they asking questions the rep couldn’t answer, or if the customer is very frustrated. Respond with either '1 = yes' or '0 = no’ and use the following logic: 1 = They should have transferred the call, and they DID transfer the call, 0 = They should have transferred the call, and they DID NOT transfer the call, 1 = They should NOT have transferred the call, and they DID NOT transfer the call, 0 = They should NOT have transferred the call, and they DID transfer the call. Explain your reasoning in a separate line.",
    #     "Did the representative mention they would be transferring the participant to to someone else to help them? If they did not mention this, respond with “1 = not applicable.” If they did mention transferring the participant to another department, did they ask for permission to transfer the call and let them know they will be transferring them? If yes, respond with ‘1 = yes.’ If they did transfer the call, but forgot to ask for permission, respond with  ‘0 = no.’ Explain your reasoning.",
    #     "Was this call disconnected unintentionally? Evidence of this would include the call ending abruptly, without a formal goodbye. If there was no formal goodbye, respond with “yes, the call was disconnected.” If there was a formal goodbye and the call did not end abruptly, respond with “no” Explain your reasoning. No need to explain your answer, just answer yes or no.",
    #     "Did the representative provide a recap of the participant’s issue along with the resolution? Evidence of this would include the representative discussing next steps, or actions they will take to resolve the customer’s concern. If the representative did clarify how they are going to solve the customer’s issue, respond with ‘1 = yes.’ If they did not provide any kind of summary of the call, or the solution or steps the rep was going to take to solve the issue, respond with ‘0 = no.’ Explain your reasoning in a separate line.",
    #     "Did the representative or the participant indicate that all questions were answered or all needs were met before ending the call? If the representative asked a question like 'Is there anything else I can assist you with?' or if the participant indicated their needs were met, respond with '1 = yes' or '1 = N/A. Participant confirmed issue resolution.' If neither occurred, respond with '0 = no.'",
    #     "Did the representative ask if the participant would like to stay on the line to take a brief survey to provide feedback on their call? Or did they say “please hold for a brief survey.” If they did ask about or mention the survey, respond with '1 = yes.' If they did not ask about or mention the survey at the end of the call, respond with '0 = no.' Explain your reasoning in a separate line.",
    #     "Did the representative complete the call with a proper closing? An example of this would include the rep saying something like 'Thank you for calling and have a great day!' If the rep did thank them for calling and said goodbye, respond with '1 = yes.' If the rep did not say thank you for calling and said goodbye, respond with '0 = no.' Explain your reasoning in a separate line.",
    #     "Did the representative treat the participant with courtesy? Evidence of this would include the rep consistently addressing the participant by their name, showing empathy, and being professional. If they were generally courteous and professional, respond with “1 = yes.” If the rep never called the participant by name, or was unprofessional or rude, respond with “0 = no.’ Explain your reasoning in a separate line.",
    #     "Based on the language used by the rep, how positive was their tone and sentiment? Did they display an engaged, pleasant tone? If they They maintained a professional and courteous demeanor throughout the call, respond with ‘1 = yes.’ If the rep was rude or unprofessional, respond with ‘0 = no’ Explain your reasoning in a separate line.",
    #     "Did the representative wait for the participant to finish talking before speaking? If they interrupt in error, did they apologize for the interruption?  Respond with ‘1 = yes’ if there were no interruptions and the rep displayed proper listening etiquette, or if they apologized for interrupting. Respond with ‘0 = no’ if the rep interrupted the participant and did not apologize for interrupting. Explain your reasoning in a separate line.",
    #     "Did the representative treat the participant with respect by trying to understand the cause of the participant’s problem, understand how their problem affects their behavior, and respond with empathy? If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.",
    #     "Did the rep give accurate answers in a confident tone that addressed the concern of the customer directly?  If yes, respond with '1 = yes.' If no, respond with '0 = no.' Explain your reasoning in a separate line.",
    #     "Did the representative exhibit interest in the participant's questions or concerns?  If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.",
    #     "Did the representative show effort in solving the participant's issue with the goal of achieving a solution on the call?  If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.",
    #     "Did a situation arise during the call that required the representative to de-escalate tension or agitation from the participant? If yes, did the representative employ strategies like using empathy statements, maintaining a calm tone, and demonstrating a clear understanding of the problem to successfully de-escalate the situation? Respond with '1 = yes' ONLY if there was a palpable tension or agitation from the participant that the representative successfully de-escalated. Respond with '0 = no' if there was tension or agitation from the participant that the representative failed to de-escalate. Respond with '1 = not applicable' if the call was generally pleasant, with no instances of tension or agitation that required de-escalation. Explain your reasoning in a separate line and reference any utterances from the participant that indicate frustration or tension.",
    #     "Identify elements of the call where the rep was performing positively. Act as a coach giving encouraging feedback to the rep for what they did right on this call. Keep it to three main points of feedback so the reader isn’t overwhelmed.",
    #     "Identify elements of the call where the rep was performing poorly. Act as a coach giving feedback on what the rep can be doing better on the call to follow guidelines above. Summarize any aspects of the required process that they missed, and how they can improve next time. Keep this response concise, as to not overwhelm the reader."
    # ]

    ## v3
    promptList = [
        "Was this call related to Nue Synergy or Plan Source? Answer should be either PlanSource or NueSynergy. No need to provide reasoning here, just the answer.", # department ID
        "What was the name of the representative who answered the phone call? No need to provide reasoning here, just the answer.", # rep ID
        "What was the name of the customer who called in asking for help? No need to provide reasoning here, just the answer.", # customer ID
        "Did the representative greet the participant by saying something like 'Thank you for calling NueSynergy' or 'PlanSource my name is (Their Name)' or something similar to this? Another example would be 'Plansource or Nuesynergy, This is (THEIR NAME) how can I help you?' The rep must say their name and NueSynergy/PlanSource in their greeting. to get credit for this. If the rep introduced themselves by stating their company name, and their personal name, respond with ‘1 = yes.’ If they did not say their name and either plan source or nue synergy, respond with ‘0 = no.’ Explain your reasoning in a separate line.", # greeting
        "Did the participant disclose their social security number? Either the full number or their last four digits? If they didn’t verify the social, did they verify the last four digits? If yes, respond with ‘1 =yes’ If no, respond with ‘0 = no’. Explain your reasoning in a separate line. Do not repeat the number in your reasoning.", # Security verification
        "Did the representative ask, 'How can I help you today?' or something similar to this? If they did ask this or something very similar, respond with yes = 1. If they did not ask a question to understand why the client called, respond with 0 = no. Explain your reasoning.", # needs assessment
        "Did the representative ask relevant questions to further understand the reasoning behind why the customer contacted NueSynergy? If they did, respond with 1 = yes. If they didn’t, respond with 0 = no. Explain your reasoning.", # rep discovery
        "Does it appear that the representative used all the available resources they have at their disposal to resolve the customer’s issue? If they are taking a long time to answer the question, not seeming confident in their answers, or the customer is confused, this is likely evidence that they should have utilized additional resources to answer the call. If they did use all available resources, respond with 1 = yes. If the issue was resolved on this call, and it isn’t obvious that the rep was taking a long time to answer, not seeming confident, or the customer wasn’t confused by the rep’s responses, respond with 1 = N/A. If the rep did take a long time to answer questions, or wasn’t confident, or confused the customer, respond with 0 = no. Explain your reasoning.", # resource utilization
        "Did the representative provide the participant with thorough and accurate responses to all questions? If they did, respond with 1 = yes. If they did not, respond with 0 = no. Explain your reasoning.", # responsiveness
        "Does it appear the rep placed the customer on hold? Evidence of this would be the rep saying something like 'I’m going to place you on a brief hold.' If the word ‘hold’ was never mentioned, and it’s clear the rep didn’t place the customer on hold, respond with '1 = N/A.' It the rep did mention placing the customer on hold, respond with '0 = Yes.'", # hold compliance
        "If applicable, should the representative have transferred the call? This is applicable if the customer called the wrong department, were they asking questions the rep couldn’t answer, or if the customer is very frustrated. Respond with either 1 or 0 and use the following logic: 1 = They should have transferred the call, and they DID transfer the call; 0 = They should have transferred the call, and they DID NOT transfer the call; 1 = They should NOT have transferred the call, and they DID NOT transfer the call; 0 = They should NOT have transferred the call, and they DID transfer the call; 1 = N/A. Explain your reasoning.", # transfer compliance
        "Was this call disconnected unintentionally? Evidence of this would include the call ending abruptly, without a formal goodbye. If there was no formal goodbye, respond with “0 = yes.” If there was a formal goodbye and the call did not end abruptly, respond with “1 = N/A.” No need to explain your answer, just answer yes or no.", # call disconnected
        "Did the representative provide a recap of the participant’s issue along with the resolution? Evidence of this would include the representative discussing next steps, or actions they will take to resolve the customer’s concern. If the representative did clarify how they are going to solve the customer’s issue, respond with ‘1 = yes.’ If they did not provide any kind of summary of the call, or the solution or steps the rep was going to take to solve the issue, respond with ‘0 = no.’ Explain your reasoning in a separate line.", # recap confirmation
        "Did the representative or the participant indicate that all questions were answered or all needs were met before ending the call? If the representative asked a question like 'Is there anything else I can assist you with?' or if the participant indicated their needs were met, respond with '1 = yes' or '1 = N/A. Participant confirmed issue resolution.' If neither occurred, respond with '0 = no.'", # additional support
        "Did the representative ask if the participant would like to stay on the line to take a brief survey to provide feedback on their call? Or did they say “please hold for a brief survey.” If they did mention the survey at all, respond with “1 = yes.” If they did not ask about or mention the survey, respond with “0 = no.” Explain your reasoning in a separate line.", # survey request
        "Did the representative complete the call with a proper closing? An example of this would include the rep saying something like 'Thank you for calling and have a great day!' If the rep did thank them for calling and said goodbye, respond with \'1 = yes.\' If the rep did not say thank you for calling and said goodbye, respond with '0 = no.' Explain your reasoning in a separate line.", # closing formality
        "Did the representative treat the participant with courtesy? Evidence of this would include the rep consistently addressing the participant by their name, showing empathy, and being professional. If they were generally courteous and professional, respond with '1 = yes.' If the rep never called the participant by name, or was unprofessional or rude, respond with '0 = no.’ Explain your reasoning in a separate line.", # courtesy assessment
        "Based on the language used by the rep, how positive was their tone and sentiment? Did they display an engaged, pleasant tone? If they They maintained a professional and courteous demeanor throughout the call, respond with ‘1 = yes.’ If the rep was rude or unprofessional, respond with ‘0 = no’ Explain your reasoning in a separate line.", # communication tone
        "Did the representative wait for the participant to finish talking before speaking? If they interrupt in error, did they apologize for the interruption?  Respond with ‘1 = yes’ if there were no interruptions and the rep displayed proper listening etiquette, or if they apologized for interrupting. Respond with ‘0 = no’ if the rep interrupted the participant and did not apologize for interrupting. Explain your reasoning in a separate line.", # listening etiquette
        "Did the representative treat the participant with respect by trying to understand the cause of the participant’s problem, understand how their problem affects their behavior, and respond with empathy? If yes, respond with '1 = yes.' If no, respond with '0 = no.' Explain your reasoning in a separate line.", # empathy assessment
        "Did the rep give accurate answers in a confident tone that addressed the concern of the customer directly?  If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.", #accuracy assessment
        "Did the representative exhibit interest in the participant's questions or concerns?  If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.", # interest engagement
        "Did the representative show effort in solving the participant's issue with the goal of achieving a solution on the call?  If yes, respond with “1 = yes.” If no, respond with “0 = no.” Explain your reasoning in a separate line.", # resolution effort
        "Did a situation arise during the call that required the representative to de-escalate tension or agitation from the participant? If yes, did the representative employ strategies like using empathy statements, maintaining a calm tone, and demonstrating a clear understanding of the problem to successfully de-escalate the situation? Respond with '1 = yes' ONLY if there was a palpable tension or agitation from the participant that the representative successfully de-escalated. Respond with '0 = no' if there was tension or agitation from the participant that the representative failed to de-escalate. Respond with '1 = not applicable' if the call was generally pleasant, with no instances of tension or agitation that required de-escalation. Explain your reasoning in a separate line and reference any utterances from the participant that indicate frustration or tension.", # deescalation effort
        "Identify three elements of the call where the rep was performing positively. Act as a coach giving encouraging feedback to the rep for what they did right on this call. Keep it to three main points of feedback so the reader isn’t overwhelmed.", # strength assessment
        "Identify three elements of the call where the rep was performing poorly. Act as a coach giving feedback on what the rep can be doing better on the call to follow guidelines above. Summarize any aspects of the required process that they missed, and how they can improve next time. Keep this response concise, as to not overwhelm the reader.", # weakness assessment
        "Generate a brief summary of this call formatted with bullet points. Use the following criteria in your response: 1. Customer's concern, 2. Whether or not the issue was resolved, and how it was resolved, 3. Any action items that are required as a result of the call. 4. Customer's sentiment throughout the call. What was it at the beginning and what was it at the end." #gist
    ]

    results = {}
    for question in promptList:
        response = openai.ChatCompletion.create(
            engine="GPTturbo",
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
        print("Response:", response)
        results[question] = response['choices'][0]['message']['content']
    # returns a dictionary of results and a boolean indicating success
    return results, True

def notify_server(url, bucket, key):
    data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": '',
                "transcript": '',
                "success": '',
                "status": "Analyzing"
            })
    request = requests.post(url, data=data, verify=False)
    print("Analyzing:", request)
    # print(json.dumps(request))

def lambda_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    # destination server info
    ip = '3.149.238.102'
    prod_domain = 'app.lightbulb.ai'
    dev_domain = 'dev.lightbulb.ai'
    api_route = '/api/call-data'
    port = '3088'
    haveTranscript = False
    haveResponse = False
    openai.api_type = "azure"
    result = 'empty'
    transcript = ''
    error = ''

    # Download file from S3
    s3client = boto3.client('s3')
    s3client.download_file(bucket, key, '/tmp/'+key)
    os.chdir('/tmp')
    for f in os.listdir():
        with open(f, 'rb') as file:

            ### initialize whisper azure creds
            openai.api_key = ""
            openai.api_base = ""
            openai.api_version=""
            try:
                url = "https://"+prod_domain+api_route
                notify_server(url, bucket, key)
            except Exception as e:
                print("Exception while phoning home:", e)
            try:
                # attempts to transcribe audio file
                transcript = openai.Audio.transcribe(
                    deployment_id="whisper-model",
                    model="whisper-1",
                    file=file
                    )['text']
                # replaces SSNs with XXX-XX-XXXX
                transcript = replace_ssns(transcript)
                transcript = replace_credit_card_numbers(transcript)
                print(transcript)
                if len(json.dumps(transcript)) > 0:
                    # if transcript text content is present, set haveTranscript to True in order to show success
                    haveTranscript = True
                    break
            except Exception as e:
                error = e
                print("Exception in transcription:", e)


    # analyze the transcript with the given prompt
    try:
        result, haveResponse = analyze(transcript)
    except Exception as e:
        error = e
        print("Exception in Q&A:", e)

    # indicates success or failure - can be redirected to a different server
    try:
        if haveTranscript & haveResponse:

            url = "https://"+prod_domain+api_route
            data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": json.dumps(result),
                "transcript": json.dumps(transcript),
                "success": "true",
                "status": "Completed"
            })
            request = requests.post(url, data=data, verify=False)
            print(request)
            print(json.dumps(transcript))
        else:
            url = "https://"+prod_domain+api_route
            data = json.dumps({
                "bucket": bucket,
                "key": key,
                "result": json.dumps(result),
                "transcript": json.dumps(transcript),
                "success": "false",
                "status": "Error",
                "errorMessage": json.dumps(error)
            })
            request = requests.post(url, data=data, verify=False)
            print(request)
    except Exception as e:
        print("Exception while phoning home:", e)

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from bucket %s-%s'%(bucket,key))
    }


# update the status to analyzing

